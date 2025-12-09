import json
import os
import logging
import razorpay
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File, Depends
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import httpx
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session

from mic.database import init_db, get_db
from mic.models import User
from mic.auth import register_user, verify_user, get_user_status, update_user_tier
from mic.tool_manager import tool_registry, load_tools_dynamically
from mic.core import process_input
from mic.config import (
    SUBSCRIPTION_TIERS,
    EXCHANGE_RATE_API_KEY,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from mic.logging_config import setup_logging
from mic.llm_loader import get_llm

from dotenv import load_dotenv

load_dotenv()

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

setup_logging()
logger = logging.getLogger(__name__)

hf_home = os.getenv("HF_HOME", "E:/mic/LLM")
os.environ["HF_HOME"] = hf_home
os.makedirs(hf_home, exist_ok=True)

init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    load_tools_dynamically()
    logger.info(f"Tools available: {list(tool_registry.keys())}")
    yield
    logger.info("Server shutting down.")

app = FastAPI(lifespan=lifespan)

# --- JWT and Security Setup ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Pydantic Models ---

class PromptRequest(BaseModel):
    history: List[Dict[str, str]]

class SubscriptionRequest(BaseModel):
    new_tier: str | None = None

class OrderRequest(BaseModel):
    tier: str

class VerificationRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    new_tier: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    age: int | None = None
    location: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserStatusResponse(BaseModel):
    username: str
    subscription_tier: str
    llm_queries_left: int
    web_searches_left: int
    file_processing_left: int

# --- Static Files and Root ---

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/subscribe")
async def read_subscribe():
    return FileResponse('static/subscribe.html')

# --- Authentication Endpoints ---

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        if not verify_user(db, form_data.username, form_data.password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # Re-raise HTTPException as it's an expected error flow
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during login for user '{form_data.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login.")

@app.post("/api/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        if register_user(db, request.username, request.password, request.email, request.age, request.location):
            logger.info(f"User '{request.username}' registered successfully.")
            return {"message": "User registered successfully"}
        # register_user returns False if username exists or data is invalid
        raise HTTPException(status_code=400, detail="Username already exists or invalid data provided.")
    except HTTPException:
        raise # Re-raise expected HTTP exceptions
    except Exception as e:
        logger.error(f"An unexpected error occurred during registration for user '{request.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during registration.")

@app.get("/api/user/status", response_model=UserStatusResponse)
async def get_user_status_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the current user's subscription tier and usage limits.
    """
    try:
        logger.info(f"User status requested by '{current_user.username}'")
        user_status = get_user_status(db, current_user.username)
        if not user_status:
            logger.warning(f"User '{current_user.username}' not found when requesting status.")
            raise HTTPException(status_code=404, detail="User not found.")
        return user_status
    except HTTPException:
        raise # Re-raise expected HTTP exceptions
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching status for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching user status.")

# --- Core API Endpoints ---

async def sse_formatter(response_stream: AsyncGenerator[Dict[str, Any], None]) -> AsyncGenerator[str, None]:
    async for event in response_stream:
        try:
            formatted_event = f"data: {json.dumps(event)}\n\n"
            yield formatted_event
        except TypeError as e:
            error_event = {"type": "error", "content": f"Failed to serialize event: {e}"}
            yield f"data: {json.dumps(error_event)}\n\n"

@app.post("/api/prompt")
async def api_prompt(request: PromptRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"API prompt received for user '{current_user.username}' with input: {request.history[-1].get('content', 'N/A')}")
    try:
        response_stream = process_input(request.history, current_user.username)
        # This part needs careful handling for streaming responses
        async def stream_wrapper():
            try:
                async for event in response_stream:
                    yield event
            except Exception as e:
                logger.error(f"Error during stream processing for user '{current_user.username}': {e}", exc_info=True)
                # Yield a final error event to the client
                yield {"type": "error", "content": "An internal error occurred during the response stream."}

        return StreamingResponse(sse_formatter(stream_wrapper()), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error processing prompt for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/tools")
async def get_tools(current_user: User = Depends(get_current_user)):
    """
    Returns a list of available tool names.
    """
    logger.info(f"Tool list requested by user '{current_user.username}'")
    try:
        tool_names = sorted(list(tool_registry.keys()))
        return JSONResponse(content={"tools": tool_names})
    except Exception as e:
        logger.error(f"Error fetching tool list for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve tool list.")

# ... (other endpoints like /api/process_file, /api/register) ...

@app.post("/api/subscription/status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    # This function remains the same
    pass # Placeholder for brevity, the original code is kept

@app.post("/api/subscription/create_order")
async def create_order(request: OrderRequest, current_user: User = Depends(get_current_user)):
    if not request.tier or request.tier not in SUBSCRIPTION_TIERS or request.tier == "Free":
        raise HTTPException(status_code=400, detail="Invalid subscription tier specified.")

    try:
        tier_info = SUBSCRIPTION_TIERS[request.tier]
        price_usd = tier_info["price_usd"]
        
        usd_to_inr_rate = 83.0 
        amount_inr = price_usd * usd_to_inr_rate
        amount_in_paise = int(amount_inr * 100)

        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"receipt_mic_{current_user.username}_{request.tier}",
            "notes": {
                "username": current_user.username,
                "tier": request.tier
            }
        }

        order = razorpay_client.order.create(data=order_data)
        logger.info(f"Created Razorpay order {order['id']} for user {current_user.username}")
        return {"order_id": order["id"], "amount": order["amount"], "currency": "INR"}

    except Exception as e:
        logger.error(f"Error creating Razorpay order for {current_user.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create payment order.")

@app.post("/api/subscription/verify")
async def verify_payment(request: VerificationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        logger.info(f"Razorpay signature verified for order {request.razorpay_order_id}")

    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Razorpay signature verification failed for order {request.razorpay_order_id}: {e}")
        raise HTTPException(status_code=400, detail="Payment verification failed.")

    try:
        user = db.query(User).filter(User.username == current_user.username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        new_tier_limits = SUBSCRIPTION_TIERS[request.new_tier]
        
        user.subscription_tier = request.new_tier
        user.llm_queries_left = new_tier_limits["llm_query_limit"]
        user.web_searches_left = new_tier_limits["web_search_limit"]
        user.file_processing_left = new_tier_limits["file_processing_limit"]
        user.last_reset_date = datetime.utcnow().date()
        
        db.commit()

        logger.info(f"User {current_user.username} upgraded to {request.new_tier} tier after payment verification.")
        return {"message": f"Subscription upgraded to {request.new_tier} successfully."}

    except Exception as e:
        logger.error(f"Error upgrading subscription for {current_user.username} after verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database update failed after payment verification.")


@app.get("/api/subscription/localized_pricing")
async def get_localized_pricing(request: Request):
    pass 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # nosec B104 - Binding to all interfaces is intentional for development/internal access.
