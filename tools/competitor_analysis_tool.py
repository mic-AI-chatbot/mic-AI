import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import Product
from sqlalchemy.exc import IntegrityError

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered competitive strategy generation will not be available.")

logger = logging.getLogger(__name__)

class CompetitiveStrategyModel:
    """Manages the text generation model for competitive strategy, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CompetitiveStrategyModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for competitive strategy are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for competitive strategy...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

competitive_strategy_model_instance = CompetitiveStrategyModel()

class AddProductToMarketTool(BaseTool):
    """Adds a new product to the simulated market database."""
    def __init__(self, tool_name="add_product_to_market"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new product to the simulated market database with its industry, market share, features, pricing, strengths, and weaknesses."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "A unique name for the product."},
                "industry": {"type": "string", "description": "The industry the product belongs to."},
                "market_share": {"type": "number", "description": "Market share as a decimal (e.g., 0.15 for 15%)."},
                "features": {"type": "array", "items": {"type": "string"}, "description": "A list of key features."},
                "pricing": {"type": "string", "description": "Description of the product's pricing strategy."},
                "strengths": {"type": "string", "description": "Key strengths of the product."},
                "weaknesses": {"type": "string", "description": "Key weaknesses of the product."}
            },
            "required": ["product_name", "industry", "market_share", "features", "pricing", "strengths", "weaknesses"]
        }

    def execute(self, product_name: str, industry: str, market_share: float, features: List[str], pricing: str, strengths: str, weaknesses: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_product = Product(
                product_name=product_name,
                industry=industry,
                market_share=market_share,
                features=json.dumps(features),
                pricing=pricing,
                strengths=strengths,
                weaknesses=weaknesses,
                created_at=now
            )
            db.add(new_product)
            db.commit()
            db.refresh(new_product)
            report = {"message": f"Product '{product_name}' added to the market."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Product '{product_name}' already exists. Use update if you want to modify it."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding product to market: {e}")
            report = {"error": f"Failed to add product to market: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AnalyzeMarketShareTool(BaseTool):
    """Analyzes market share data for a given product or industry."""
    def __init__(self, tool_name="analyze_market_share"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes market share data for a specified product within a given industry, returning its market share percentage."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "The name of the product to analyze."},
                "industry": {"type": "string", "description": "The industry for context in analysis (e.g., 'software', 'automotive').", "default": "general"}
            },
            "required": ["product_name"]
        }

    def execute(self, product_name: str, industry: str = "general", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            product = db.query(Product).filter(Product.product_name == product_name).first()
            if not product:
                return json.dumps({"error": f"Product '{product_name}' not found in the market database."})
            
            report = {
                "product_name": product_name,
                "industry": industry,
                "market_share_percent": round(product.market_share * 100, 2),
                "analysis_summary": f"Market share for '{product_name}' in the '{industry}' industry is {round(product.market_share * 100, 2)}%."
            }
        except Exception as e:
            logger.error(f"Error analyzing market share: {e}")
            report = {"error": f"Failed to analyze market share: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class CompareProductFeaturesTool(BaseTool):
    """Compares features of different products."""
    def __init__(self, tool_name="compare_product_features"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Compares the features of two or more products, highlighting commonalities and differences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of product names to compare (e.g., ['my_product', 'competitor_A'])."
                }
            },
            "required": ["product_names"]
        }

    def execute(self, product_names: List[str], **kwargs: Any) -> str:
        if len(product_names) < 2:
            return json.dumps({"error": "At least two product names are required for comparison."})
            
        db = next(get_db())
        try:
            products_data = {}
            all_features = set()
            
            for name in product_names:
                product = db.query(Product).filter(Product.product_name == name).first()
                if not product:
                    return json.dumps({"error": f"Product '{name}' not found in the market database."})
                products_data[name] = product
                all_features.update(json.loads(product.features))
                
            comparison_details = {}
            for name, data in products_data.items():
                comparison_details[name] = {"features": json.loads(data.features), "pricing": data.pricing, "strengths": data.strengths, "weaknesses": data.weaknesses}
            
            common_features = list(all_features)
            if len(product_names) == 2: # For two products, find intersection
                features1 = set(json.loads(products_data[product_names[0]].features))
                features2 = set(json.loads(products_data[product_names[1]].features))
                common_features = list(features1.intersection(features2))
            
            report = {
                "products_compared": product_names,
                "comparison_details": comparison_details,
                "common_features": common_features,
                "analysis_summary": "Detailed feature comparison completed."
            }
        except Exception as e:
            logger.error(f"Error comparing product features: {e}")
            report = {"error": f"Failed to compare product features: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GenerateCompetitiveStrategyTool(BaseTool):
    """Generates strategic recommendations based on competitive analysis using an AI model."""
    def __init__(self, tool_name="generate_competitive_strategy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates strategic recommendations (e.g., market positioning, product development, pricing) based on competitive analysis using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "my_product_name": {"type": "string", "description": "The name of your product."},
                "competitor_product_names": {"type": "array", "items": {"type": "string"}, "description": "A list of competitor product names."},
                "analysis_context": {"type": "string", "description": "Optional: Additional context for strategy generation (e.g., 'we want to target a younger demographic').", "default": ""}
            },
            "required": ["my_product_name", "competitor_product_names"]
        }

    def execute(self, my_product_name: str, competitor_product_names: List[str], analysis_context: str = "", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        db = next(get_db())
        try:
            my_product = db.query(Product).filter(Product.product_name == my_product_name).first()
            if not my_product:
                return json.dumps({"error": f"My product '{my_product_name}' not found in the market database."})

            competitors_data = []
            for name in competitor_product_names:
                competitor = db.query(Product).filter(Product.product_name == name).first()
                if not competitor:
                    return json.dumps({"error": f"Competitor product '{name}' not found in the market database."})
                competitors_data.append(competitor)

            prompt = f"Generate strategic recommendations for '{my_product_name}' (Features: {json.loads(my_product.features)}, Pricing: {my_product.pricing}, Strengths: {my_product.strengths}, Weaknesses: {my_product.weaknesses}, Market Share: {my_product.market_share*100:.2f}%). "
            prompt += "Its main competitors are:\n"
            for comp in competitors_data:
                prompt += f"- {comp.product_name} (Features: {json.loads(comp.features)}, Pricing: {comp.pricing}, Strengths: {comp.strengths}, Weaknesses: {comp.weaknesses}, Market Share: {comp.market_share*100:.2f}%)\n"
            
            if analysis_context:
                prompt += f"Additional context: {analysis_context}. "
            
            prompt += "Provide actionable strategies for market positioning, product development, and pricing. Strategic Recommendations:"
            
            llm_response = competitive_strategy_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
            
            report = {"my_product": my_product_name, "competitors": competitor_product_names, "strategic_recommendations": llm_response}
        except Exception as e:
            logger.error(f"Error generating competitive strategy: {e}")
            report = {"error": f"Failed to generate competitive strategy: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)