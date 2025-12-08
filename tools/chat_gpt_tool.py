import logging
import json
import os
from typing import Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    from diffusers import StableDiffusionPipeline
    from PIL import Image
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers or diffusers library not found. ChatGPT tools will not be fully functional.")

logger = logging.getLogger(__name__)

class ChatGPTModel:
    """Manages AI models for ChatGPT-like functionalities, using a lazy-loading singleton pattern."""
    _generator = None
    _image_captioner = None
    _text_to_image_pipe = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatGPTModel, cls).__new__(cls)
        return cls._instance

    def _load_model(self, model_attr, loader_func, friendly_name):
        """Generic lazy loader for a model."""
        if getattr(self, model_attr) is None:
            if not TRANSFORMERS_AVAILABLE:
                logger.error(f"Required libraries for {friendly_name} are not installed.")
                setattr(self, model_attr, "unavailable")
                return
            try:
                logger.info(f"Initializing {friendly_name} model...")
                setattr(self, model_attr, loader_func())
                logger.info(f"{friendly_name} model loaded.")
            except Exception as e:
                logger.error(f"Failed to load {friendly_name} model: {e}")
                setattr(self, model_attr, "unavailable")

    def get_generator(self):
        self._load_model(
            '_generator',
            lambda: pipeline("text-generation", model="distilgpt2"),
            "text generation"
        )
        return self._generator if self._generator != "unavailable" else None

    def get_captioner(self):
        self._load_model(
            '_image_captioner',
            lambda: pipeline("image-to-text", model="Salesforce/blip-image-captioning-base"),
            "image captioning"
        )
        return self._image_captioner if self._image_captioner != "unavailable" else None

    def get_text_to_image_pipe(self):
        self._load_model(
            '_text_to_image_pipe',
            lambda: {
                "pipe": StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16, safety_checker=None).to("cuda" if torch.cuda.is_available() else "cpu")
            },
            "text-to-image"
        )
        # The model is wrapped in a dict to handle the .to() method call correctly
        return self._text_to_image_pipe['pipe'] if isinstance(self._text_to_image_pipe, dict) else None

    def generate_text(self, prompt: str, max_length: int) -> str:
        generator = self.get_generator()
        if not generator:
            return "Text generation model not available. Check logs for loading errors."
        try:
            generated = generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=generator.tokenizer.eos_token_id)[0]['generated_text']
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

    def caption_image(self, image_path: str) -> str:
        captioner = self.get_captioner()
        if not captioner:
            return "Image captioning model not available. Check logs for loading errors."
        try:
            image = Image.open(image_path)
            caption = captioner(image)[0]['generated_text']
            return caption
        except Exception as e:
            logger.error(f"Image captioning failed for '{image_path}': {e}")
            return f"Error during image captioning: {e}"

    def generate_image(self, text_description: str, output_path: str) -> str:
        pipe = self.get_text_to_image_pipe()
        if not pipe:
            return "Text-to-image model not available. Check logs for loading errors."
        try:
            image = pipe(text_description).images[0]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            return os.path.abspath(output_path)
        except Exception as e:
            logger.error(f"Image generation failed for '{text_description}': {e}")
            return f"Error during image generation: {e}"

chatgpt_model_instance = ChatGPTModel()

class AskChatGPTTool(BaseTool):
    """Asks a question or provides a prompt to a simulated ChatGPT and gets a text response."""
    def __init__(self, tool_name="ask_chatgpt"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Asks a question or provides a prompt to a simulated ChatGPT and gets a text response."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"prompt": {"type": "string", "description": "The prompt to send to ChatGPT."}},
            "required": ["prompt"]
        }

    def execute(self, prompt: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})
        
        response = chatgpt_model_instance.generate_text(prompt, max_length=len(prompt.split()) + 200)
        return json.dumps({"prompt": prompt, "response": response}, indent=2)

class AnalyzeImageWithChatGPTTool(BaseTool):
    """Analyzes an image using a simulated ChatGPT's image capabilities."""
    def __init__(self, tool_name="analyze_image_with_chatgpt"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes an image using a simulated ChatGPT's image capabilities, generating a descriptive caption."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"image_path": {"type": "string", "description": "The absolute path to the image file to analyze."}},
            "required": ["image_path"]
        }

    def execute(self, image_path: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})
        
        caption = chatgpt_model_instance.caption_image(image_path)
        return json.dumps({"image_path": image_path, "analysis": caption}, indent=2)

class GenerateImageWithChatGPTTool(BaseTool):
    """Generates an image from a text description using a simulated ChatGPT's image generation capabilities."""
    def __init__(self, tool_name="generate_image_with_chatgpt"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates an image from a text description using a simulated ChatGPT's image generation capabilities (Dall-E like)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text_description": {"type": "string", "description": "The text description to generate the image from."},
                "output_path": {"type": "string", "description": "The absolute path to save the generated image (e.g., 'generated_image.png')."}
            },
            "required": ["text_description", "output_path"]
        }

    def execute(self, text_description: str, output_path: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' and 'diffusers' libraries to be installed."})
        
        image_path = chatgpt_model_instance.generate_image(text_description, output_path)
        if "Error" in image_path: # Check if the generate_image method returned an error string
            return json.dumps({"error": image_path})
        return json.dumps({"text_description": text_description, "generated_image_path": image_path}, indent=2)

class SummarizeDocumentWithChatGPTTool(BaseTool):
    """Summarizes a document using a simulated ChatGPT's file analysis capabilities."""
    def __init__(self, tool_name="summarize_document_with_chatgpt"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Summarizes a document using a simulated ChatGPT's file analysis capabilities."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"document_text": {"type": "string", "description": "The full text content of the document to summarize."}},
            "required": ["document_text"]
        }

    def execute(self, document_text: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})
        
        prompt = f"Summarize the following document concisely:\n\n{document_text}\n\nSummary:"
        summary = chatgpt_model_instance.generate_text(prompt, max_length=len(prompt.split()) + 300)
        return json.dumps({"document_text_sample": document_text[:100] + "...", "summary": summary}, indent=2)