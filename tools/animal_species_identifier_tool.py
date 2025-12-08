

import logging
from typing import Dict, Any
import torch
from PIL import Image
import timm
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform
import requests
from tools.base_tool import BaseTool

class AnimalSpeciesIdentifierTool(BaseTool):
    def __init__(self, tool_name: str = "animal_species_identifier_tool", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.model = None
        self.transform = None
        self.labels = None
        self.load_model()

    def load_model(self):
        """
        Loads a pre-trained model for image classification.
        """
        try:
            self.model = timm.create_model('efficientnet_b3a', pretrained=True)
            self.model.eval()
            config = resolve_data_config({}, model=self.model)
            self.transform = create_transform(**config)

            # Download class labels
            url = 'https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt'
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            self.labels = response.text.split('\n')
        except Exception as e:
            logging.error(f"Error loading model: {e}")

    @property
    def description(self) -> str:
        return "Identifies animal species from an image."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "media_path": {
                    "type": "string",
                    "description": "The path or URL to the image of the animal."
                }
            },
            "required": ["media_path"]
        }

    def execute(self, media_path: str) -> str:
        """
        Identifies an animal species from an image using a pre-trained model.
        """
        if self.model is None or self.transform is None or self.labels is None:
            return "Error: Model not loaded. Please check the logs for details."

        logging.info(f"Identifying animal species from {media_path}.")

        try:
            if media_path.startswith(('http://', 'https://')):
                response = requests.get(media_path, stream=True, timeout=10)
                response.raise_for_status()
                img = Image.open(response.raw).convert('RGB')
            else:
                img = Image.open(media_path).convert('RGB')
        except Exception as e:
            return f"Error opening image: {e}"

        try:
            tensor = self.transform(img).unsqueeze(0)  # Add batch dimension

            with torch.no_grad():
                out = self.model(tensor)

            probabilities = torch.nn.functional.softmax(out[0], dim=0)
            top5_prob, top5_catid = torch.topk(probabilities, 5)

            results = []
            for i in range(top5_prob.size(0)):
                results.append(f"{self.labels[top5_catid[i]]}: {top5_prob[i].item():.4f}")
            
            return f"SUCCESS: Top 5 predictions:\n" + "\n".join(results)

        except Exception as e:
            return f"Error during inference: {e}"
