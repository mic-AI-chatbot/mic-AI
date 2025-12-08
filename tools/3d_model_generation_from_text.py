import torch
from diffusers import ShapEPipeline
from diffusers.utils import export_to_gif
from tools.base_tool import BaseTool
from typing import Dict, Any

class ShapE3DModelGeneratorTool(BaseTool):
    """
    A tool for generating 3D models from text prompts using OpenAI's Shap-E.
    """

    def __init__(self, tool_name="shape_3d_model_generator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.pipe = None
        self.device = None

    def _setup(self):
        if self.pipe is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.pipe = ShapEPipeline.from_pretrained("openai/shap-e", torch_dtype=torch.float16, variant="fp16")
            self.pipe = self.pipe.to(self.device)

    @property
    def description(self) -> str:
        return "Generates a 3D model from a text prompt and saves it as a GIF."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "prompt": {
                "type": "string",
                "description": "The text prompt to generate the 3D model from."
            },
            "output_path": {
                "type": "string",
                "description": "The path to save the generated GIF file (e.g., 'output.gif')."
            }
        }

    def execute(self, **kwargs: Dict[str, Any]) -> str:
        prompt = kwargs.get("prompt")
        output_path = kwargs.get("output_path", "generated_model.gif")

        if not prompt:
            return "Error: Prompt cannot be empty."

        if not output_path.endswith(".gif"):
            return "Error: Output path must end with .gif"

        try:
            self._setup()
            guidance_scale = 15.0
            num_inference_steps = 64

            images = self.pipe(
                prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                frame_size=256,
            ).images

            export_to_gif(images[0], output_path)
            return f"3D model generated and saved as a GIF to {output_path}"
        except Exception as e:
            return f"An error occurred: {e}"