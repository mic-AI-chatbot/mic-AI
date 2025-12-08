
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ReinforcementLearningSimulatorTool(BaseTool):
    """
    A tool that simulates a Reinforcement Learning (RL) environment and agent,
    allowing for defining environments, agents, and running training episodes.
    """

    def __init__(self, tool_name: str = "ReinforcementLearningSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.envs_file = os.path.join(self.data_dir, "rl_environments.json")
        self.agents_file = os.path.join(self.data_dir, "rl_agents.json")
        self.results_file = os.path.join(self.data_dir, "rl_training_results.json")
        
        # Environments: {env_id: {grid_size: ..., start_pos: ..., goal_pos: ..., rewards: {}}}
        self.environments: Dict[str, Dict[str, Any]] = self._load_data(self.envs_file, default={})
        # Agents: {agent_id: {learning_rate: ..., discount_factor: ..., exploration_rate: ..., q_table: {}}}
        self.agents: Dict[str, Dict[str, Any]] = self._load_data(self.agents_file, default={})
        # Training results: {episode_id: {env_id: ..., agent_id: ..., total_reward: ..., path: []}}
        self.training_results: Dict[str, Dict[str, Any]] = self._load_data(self.results_file, default={})

    @property
    def description(self) -> str:
        return "Simulates Reinforcement Learning: define environments/agents, run training episodes, and get results."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_environment", "define_agent", "run_training_episode", "get_results"]},
                "env_id": {"type": "string"},
                "grid_size": {"type": "integer", "minimum": 3, "maximum": 10},
                "start_position": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                "goal_position": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                "rewards": {"type": "object", "description": "e.g., {'goal': 10, 'obstacle': -5, 'step': -1}"},
                "agent_id": {"type": "string"},
                "learning_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "discount_factor": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "exploration_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "num_steps": {"type": "integer", "minimum": 10, "maximum": 1000},
                "result_id": {"type": "string", "description": "ID of the result to retrieve."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_envs(self):
        with open(self.envs_file, 'w') as f: json.dump(self.environments, f, indent=2)

    def _save_agents(self):
        with open(self.agents_file, 'w') as f: json.dump(self.agents, f, indent=2)

    def _save_results(self):
        with open(self.results_file, 'w') as f: json.dump(self.training_results, f, indent=2)

    def define_environment(self, env_id: str, grid_size: int, start_position: List[int], goal_position: List[int], rewards: Dict[str, int]) -> Dict[str, Any]:
        """Defines a new simulated RL environment (grid world)."""
        if env_id in self.environments: raise ValueError(f"Environment '{env_id}' already exists.")
        
        new_env = {
            "id": env_id, "grid_size": grid_size, "start_position": start_position,
            "goal_position": goal_position, "rewards": rewards,
            "defined_at": datetime.now().isoformat()
        }
        self.environments[env_id] = new_env
        self._save_envs()
        return new_env

    def define_agent(self, agent_id: str, learning_rate: float, discount_factor: float, exploration_rate: float) -> Dict[str, Any]:
        """Defines a new simulated RL agent."""
        if agent_id in self.agents: raise ValueError(f"Agent '{agent_id}' already exists.")
        
        new_agent = {
            "id": agent_id, "learning_rate": learning_rate, "discount_factor": discount_factor,
            "exploration_rate": exploration_rate, "q_table": {}, # Q-table will be updated during training
            "defined_at": datetime.now().isoformat()
        }
        self.agents[agent_id] = new_agent
        self._save_agents()
        return new_agent

    def run_training_episode(self, env_id: str, agent_id: str, num_steps: int) -> Dict[str, Any]:
        """Simulates a training episode for an agent in an environment."""
        env = self.environments.get(env_id)
        agent = self.agents.get(agent_id)
        if not env: raise ValueError(f"Environment '{env_id}' not found.")
        if not agent: raise ValueError(f"Agent '{agent_id}' not found.")
        
        episode_id = f"episode_{env_id}_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        current_position = list(env["start_position"])
        total_reward = 0
        path_taken = [current_position]
        
        for step in range(num_steps):
            action = random.choice(["up", "down", "left", "right"]) # Simple random policy for simulation  # nosec B311
            
            next_position = list(current_position)
            if action == "up": next_position[0] = max(0, next_position[0] - 1)
            elif action == "down": next_position[0] = min(env["grid_size"] - 1, next_position[0] + 1)
            elif action == "left": next_position[1] = max(0, next_position[1] - 1)
            elif action == "right": next_position[1] = min(env["grid_size"] - 1, next_position[1] + 1)
            
            reward = env["rewards"].get("step", 0) # Default step reward
            if next_position == env["goal_position"]: reward = env["rewards"].get("goal", 0)
            elif random.random() < 0.1: reward = env["rewards"].get("obstacle", 0) # Simulate hitting an obstacle  # nosec B311
            
            total_reward += reward
            current_position = next_position
            path_taken.append(current_position)
            
            if current_position == env["goal_position"]: break # Goal reached
        
        result = {
            "id": episode_id, "env_id": env_id, "agent_id": agent_id,
            "total_reward": total_reward, "path_taken": path_taken,
            "goal_reached": (current_position == env["goal_position"]),
            "simulated_at": datetime.now().isoformat()
        }
        self.training_results[episode_id] = result
        self._save_results()
        return result

    def get_results(self, result_id: str) -> Dict[str, Any]:
        """Retrieves stored environment, agent, or training results."""
        result = self.training_results.get(result_id)
        if not result: raise ValueError(f"Result '{result_id}' not found.")
        return result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_environment":
            env_id = kwargs.get('env_id')
            grid_size = kwargs.get('grid_size')
            start_position = kwargs.get('start_position')
            goal_position = kwargs.get('goal_position')
            rewards = kwargs.get('rewards')
            if not all([env_id, grid_size, start_position, goal_position, rewards]):
                raise ValueError("Missing 'env_id', 'grid_size', 'start_position', 'goal_position', or 'rewards' for 'define_environment' operation.")
            return self.define_environment(env_id, grid_size, start_position, goal_position, rewards)
        elif operation == "define_agent":
            agent_id = kwargs.get('agent_id')
            learning_rate = kwargs.get('learning_rate')
            discount_factor = kwargs.get('discount_factor')
            exploration_rate = kwargs.get('exploration_rate')
            if not all([agent_id, learning_rate is not None, discount_factor is not None, exploration_rate is not None]):
                raise ValueError("Missing 'agent_id', 'learning_rate', 'discount_factor', or 'exploration_rate' for 'define_agent' operation.")
            return self.define_agent(agent_id, learning_rate, discount_factor, exploration_rate)
        elif operation == "run_training_episode":
            env_id = kwargs.get('env_id')
            agent_id = kwargs.get('agent_id')
            num_steps = kwargs.get('num_steps')
            if not all([env_id, agent_id, num_steps]):
                raise ValueError("Missing 'env_id', 'agent_id', or 'num_steps' for 'run_training_episode' operation.")
            return self.run_training_episode(env_id, agent_id, num_steps)
        elif operation == "get_results":
            result_id = kwargs.get('result_id')
            if not result_id:
                raise ValueError("Missing 'result_id' for 'get_results' operation.")
            return self.get_results(result_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ReinforcementLearningSimulatorTool functionality...")
    temp_dir = "temp_rl_sim_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rl_sim = ReinforcementLearningSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define an environment
        print("\n--- Defining environment 'grid_world_1' ---")
        rl_sim.execute(operation="define_environment", env_id="grid_world_1", grid_size=5, start_position=[0,0], goal_position=[4,4], rewards={"goal": 100, "obstacle": -10, "step": -1})
        print("Environment defined.")

        # 2. Define an agent
        print("\n--- Defining agent 'q_agent_01' ---")
        rl_sim.execute(operation="define_agent", agent_id="q_agent_01", learning_rate=0.1, discount_factor=0.9, exploration_rate=0.2)
        print("Agent defined.")

        # 3. Run a training episode
        print("\n--- Running training episode for 'q_agent_01' in 'grid_world_1' ---")
        episode_result = rl_sim.execute(operation="run_training_episode", env_id="grid_world_1", agent_id="q_agent_01", num_steps=50)
        print(json.dumps(episode_result, indent=2))

        # 4. Get results of the episode
        print(f"\n--- Getting results for episode '{episode_result['id']}' ---")
        retrieved_results = rl_sim.execute(operation="get_results", result_id=episode_result["id"])
        print(json.dumps(retrieved_results, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
