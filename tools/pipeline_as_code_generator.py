import logging
import random
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PipelineAsCodeGeneratorTool(BaseTool):
    """
    A tool that generates pipeline-as-code definitions (e.g., Jenkinsfile,
    GitLab CI/CD YAML) based on specified stages and platform.
    """
    def __init__(self, tool_name: str = "PipelineAsCodeGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates pipeline-as-code definitions (Jenkinsfile, GitLab CI/CD) based on stages and platform."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_pipeline"]},
                "pipeline_name": {"type": "string", "description": "The name of the pipeline."},
                "stages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of pipeline stages (e.g., 'build', 'test', 'deploy')."
                },
                "platform": {"type": "string", "enum": ["jenkins", "gitlab", "github_actions"], "default": "jenkins", "description": "The CI/CD platform."}
            },
            "required": ["operation", "pipeline_name", "stages"]
        }

    def execute(self, operation: str, pipeline_name: str, stages: List[str], platform: str = "jenkins", **kwargs: Any) -> Dict[str, Any]:
        """
        Generates a pipeline-as-code definition for the specified platform and stages.
        """
        if operation != "generate_pipeline":
            raise ValueError(f"Invalid operation: {operation}. Only 'generate_pipeline' is supported.")
        if not pipeline_name or not stages:
            raise ValueError("Pipeline name and stages are required.")

        generated_pipeline_code = ""
        if platform == "jenkins":
            generated_pipeline_code = self._generate_jenkinsfile(pipeline_name, stages)
        elif platform == "gitlab":
            generated_pipeline_code = self._generate_gitlab_ci(pipeline_name, stages)
        elif platform == "github_actions":
            generated_pipeline_code = self._generate_github_actions(pipeline_name, stages)
        else:
            raise ValueError(f"Unsupported platform: {platform}. Choose from 'jenkins', 'gitlab', 'github_actions'.")

        return {
            "status": "success",
            "pipeline_name": pipeline_name,
            "platform": platform,
            "generated_code": generated_pipeline_code
        }

    def _generate_jenkinsfile(self, pipeline_name: str, stages: List[str]) -> str:
        """Generates a simulated Jenkinsfile (Groovy syntax)."""
        jenkinsfile_template = f"""
pipeline {{
    agent any
    stages {{
"""
        for stage in stages:
            jenkinsfile_template += f"""
        stage('{stage.title()}') {{
            steps {{
                echo 'Running {stage} stage for {pipeline_name}'
"""
            if stage.lower() == "build":
                jenkinsfile_template += """
                sh 'mvn clean install' // Example build command
"""
            elif stage.lower() == "test":
                jenkinsfile_template += """
                sh 'mvn test' // Example test command
"""
            elif stage.lower() == "deploy":
                jenkinsfile_template += """
                sh 'deploy_to_production.sh' // Example deploy command
"""
            jenkinsfile_template += """
            }}
        }}
"""
        jenkinsfile_template += """
    }}
}}
"""
        return jenkinsfile_template

    def _generate_gitlab_ci(self, pipeline_name: str, stages: List[str]) -> str:
        """Generates a simulated .gitlab-ci.yml (YAML syntax)."""
        gitlab_ci_template = f"""
stages: {json.dumps(stages)}

"""
        for stage in stages:
            gitlab_ci_template += f"""
{stage.lower()}_job:
  stage: {stage.lower()}
  script:
    - echo "Running {stage} stage for {pipeline_name}"
"""
            if stage.lower() == "build":
                gitlab_ci_template += """
    - mvn clean install # Example build command
"""
            elif stage.lower() == "test":
                gitlab_ci_template += """
    - mvn test # Example test command
"""
            elif stage.lower() == "deploy":
                gitlab_ci_template += """
    - deploy_to_production.sh # Example deploy command
"""
            gitlab_ci_template += "\n"
        return gitlab_ci_template

    def _generate_github_actions(self, pipeline_name: str, stages: List[str]) -> str:
        """Generates a simulated GitHub Actions workflow (YAML syntax)."""
        github_actions_template = f"""
name: {pipeline_name} CI/CD

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
"""
        for stage in stages:
            github_actions_template += f"""
  {stage.lower()}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run {stage} stage
        run: |
          echo "Running {stage} stage for {pipeline_name}"
"""
            if stage.lower() == "build":
                github_actions_template += """
          mvn clean install # Example build command
"""
            elif stage.lower() == "test":
                github_actions_template += """
          mvn test # Example test command
"""
            elif stage.lower() == "deploy":
                github_actions_template += """
          deploy_to_production.sh # Example deploy command
"""
            github_actions_template += "\n"
        return github_actions_template

if __name__ == '__main__':
    print("Demonstrating PipelineAsCodeGeneratorTool functionality...")
    
    generator_tool = PipelineAsCodeGeneratorTool()
    
    try:
        # 1. Generate a Jenkinsfile
        print("\n--- Generating Jenkinsfile for 'MyWebApp' ---")
        jenkins_code = generator_tool.execute(operation="generate_pipeline", pipeline_name="MyWebApp", stages=["build", "test", "deploy"], platform="jenkins")
        print(jenkins_code["generated_code"])

        # 2. Generate a GitLab CI/CD pipeline
        print("\n--- Generating GitLab CI/CD for 'BackendAPI' ---")
        gitlab_code = generator_tool.execute(operation="generate_pipeline", pipeline_name="BackendAPI", stages=["build", "test", "deploy"], platform="gitlab")
        print(gitlab_code["generated_code"])
        
        # 3. Generate a GitHub Actions workflow
        print("\n--- Generating GitHub Actions for 'MobileApp' ---")
        github_code = generator_tool.execute(operation="generate_pipeline", pipeline_name="MobileApp", stages=["build", "test"], platform="github_actions")
        print(github_code["generated_code"])

    except Exception as e:
        print(f"\nAn error occurred: {e}")