import logging
import os
import random
import shutil
from typing import List, Dict, Any
from PIL import Image, ImageEnhance
from tools.base_tool import BaseTool

try:
    import nltk
    from nltk.corpus import wordnet
    nltk.download('wordnet', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    wordnet = None
    NLTK_AVAILABLE = False
    logging.warning("NLTK not found. Text augmentation will use a basic placeholder for synonym replacement.")

logger = logging.getLogger(__name__)

class DataAugmentationTool(BaseTool):
    """
    A tool for augmenting text and image data.
    """

    def __init__(self, tool_name: str = "data_augmentation_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Augments text or image data using various techniques like synonym replacement, rotation, or brightness adjustment."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_type": {"type": "string", "enum": ["text", "image"]},
                "technique": {"type": "string", "enum": ["synonym_replacement", "rotate", "flip", "brightness"]},
                "text": {"type": "string", "description": "The input text to augment."},
                "image_path": {"type": "string", "description": "The path to the input image."},
                "output_path": {"type": "string", "description": "The path to save the augmented image."},
                "num_replacements": {"type": "integer", "default": 1},
                "angle": {"type": "integer", "description": "Rotation angle in degrees."},
                "factor": {"type": "number", "description": "Brightness factor (1.0 is original)."}
            },
            "required": ["data_type", "technique"]
        }

    def _get_synonyms(self, word: str) -> List[str]:
        if NLTK_AVAILABLE and wordnet:
            synonyms = set()
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    synonyms.add(lemma.name().replace('_', ' '))
            return list(synonyms)
        return []

    def _augment_text(self, technique: str, text: str, **kwargs) -> str:
        words = text.split()
        if not words: return text

        if technique == "synonym_replacement":
            num_replacements = kwargs.get('num_replacements', 1)
            indices = random.sample(range(len(words)), min(num_replacements, len(words)))  # nosec B311
            for i in indices:
                syns = self._get_synonyms(words[i])
                if syns: words[i] = random.choice(syns)  # nosec B311
            return " ".join(words)
        else:
            raise ValueError(f"Unsupported text augmentation technique: {technique}")

    def _augment_image(self, technique: str, image_path: str, output_path: str, **kwargs) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at '{image_path}'.")
        
        img = Image.open(image_path).convert("RGB")
        
        if technique == "rotate":
            angle = kwargs.get("angle")
            if angle is None: raise ValueError("'angle' is required for rotate.")
            augmented_img = img.rotate(angle, expand=True)
        elif technique == "flip":
            augmented_img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif technique == "brightness":
            factor = kwargs.get("factor")
            if factor is None: raise ValueError("'factor' is required for brightness.")
            enhancer = ImageEnhance.Brightness(img)
            augmented_img = enhancer.enhance(factor)
        else:
            raise ValueError(f"Unsupported image augmentation technique: {technique}")

        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        augmented_img.save(output_path)
        return f"Augmented image saved to {output_path}"

    def execute(self, data_type: str, technique: str, **kwargs: Any) -> str:
        if data_type == "text":
            text = kwargs.get("text")
            if not text: raise ValueError("'text' is required for text augmentation.")
            return self._augment_text(technique, text, **kwargs)
        elif data_type == "image":
            image_path = kwargs.get("image_path")
            output_path = kwargs.get("output_path")
            if not all([image_path, output_path]):
                raise ValueError("'image_path' and 'output_path' are required for image augmentation.")
            return self._augment_image(technique, image_path, output_path, **kwargs)
        else:
            raise ValueError(f"Invalid data_type: {data_type}")

if __name__ == '__main__':
    print("Demonstrating DataAugmentationTool functionality...")
    tool = DataAugmentationTool()
    
    # Text augmentation
    sample_text = "The quick brown fox jumps over the lazy dog."
    print(f"\nOriginal Text: {sample_text}")
    try:
        augmented_text = tool.execute(data_type="text", technique="synonym_replacement", text=sample_text, num_replacements=2)
        print(f"Augmented Text: {augmented_text}")
    except Exception as e:
        print(f"Text augmentation failed: {e}")

    # Image augmentation
    dummy_image = "temp_aug_image.png"
    output_dir = "temp_augmented"
    try:
        Image.new('RGB', (100, 100), color='blue').save(dummy_image)
        print(f"\nCreated dummy image: {dummy_image}")
        
        output_path = os.path.join(output_dir, "rotated.png")
        result = tool.execute(data_type="image", technique="rotate", image_path=dummy_image, output_path=output_path, angle=45)
        print(result)

    except Exception as e:
        print(f"Image augmentation failed: {e}")
    finally:
        if os.path.exists(dummy_image): os.remove(dummy_image)
        if os.path.exists(output_dir): shutil.rmtree(output_dir)
