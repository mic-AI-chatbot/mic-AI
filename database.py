import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DB_TYPE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from .models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = ""
if DB_TYPE == "postgres":
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        logger.warning("PostgreSQL environment variables not fully set. Falling back to SQLite.")
        DB_TYPE = "sqlite"
    else:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DB_NAME}"

if not DATABASE_URL:
    raise ValueError("Database configuration is invalid. Could not determine DATABASE_URL.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes the database schema using SQLAlchemy models.
    It's safe to run multiple times as it won't recreate existing tables.
    """
    logger.info(f"Initializing database with type: {DB_TYPE}")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise

def get_db():
    """
    Provides a database session for use in dependencies.
    Ensures the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

