
import logging
import os
import json
import random
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MultiAgentRLSimulatorTool(BaseTool):
    """
    A tool that simulates a Multi-Agent Reinforcement Learning (MARL) platform,
    allowing definition of environments and agents, and running training episodes.
    """

    def __init__(self, tool_name: str = "MultiAgentRLSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "marl_data.json")
        self.data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={"environments": {}, "agents": {}, "episodes": {}})

    @property
    def description(self) -> str:
        return "Simulates Multi-Agent Reinforcement Learning: define environments/agents, run training episodes."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_environment", "define_agent", "run_training_episode", "get_data"]},
                "env_id": {"type": "string"}, "grid_size": {"type": "integer"}, "num_agents": {"type": "integer"},
                "rewards": {"type": "object", "description": "e.g., {'goal': 10, 'collision': -5}"},
                "agent_id": {"type": "string"}, "agent_type": {"type": "string", "enum": ["q_learner", "random_walker"]},
                "initial_policy": {"type": "string", "enum": ["explore", "exploit"]},
                "episode_id": {"type": "string"}, "agent_ids": {"type": "array", "items": {"type": "string"}},
                "num_steps": {"type": "integer"},
                "data_type": {"type": "string", "enum": ["environment", "agent", "episode"]}
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

    def _save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=2)

    def define_environment(self, env_id: str, grid_size: int, num_agents: int, rewards: Dict[str, int]) -> Dict:
        """Defines a new simulated environment."""
        if env_id in self.data["environments"]: raise ValueError(f"Environment '{env_id}' already exists.")
        new_env = {"env_id": env_id, "grid_size": grid_size, "num_agents": num_agents, "rewards": rewards}
        self.data["environments"][env_id] = new_env
        self._save_data()
        return new_env

    def define_agent(self, agent_id: str, agent_type: str, initial_policy: str) -> Dict:
        """Defines a new simulated agent."""
        if agent_id in self.data["agents"]: raise ValueError(f"Agent '{agent_id}' already exists.")
        new_agent = {"agent_id": agent_id, "agent_type": agent_type, "initial_policy": initial_policy}
        self.data["agents"][agent_id] = new_agent
        self._save_data()
        return new_agent

    def run_training_episode(self, episode_id: str, env_id: str, agent_ids: List[str], num_steps: int) -> Dict:
        """Simulates a training episode for agents in an environment."""
        if episode_id in self.data["episodes"]: raise ValueError(f"Episode '{episode_id}' already exists.")
        env = self.data["environments"].get(env_id)
        if not env: raise ValueError(f"Environment '{env_id}' not found.")
        
        agents = [self.data["agents"].get(aid) for aid in agent_ids]
        if any(a is None for a in agents): raise ValueError("One or more agents not found.")

        # Simple simulation: agents move randomly, collect rewards
        episode_results = {"agent_rewards": {aid: 0 for aid in agent_ids}, "collisions": 0, "goals_reached": 0}
        
        for step in range(num_steps):
            for agent_id in agent_ids:
                action = random.choice(["up", "down", "left", "right"]) # Random action  # nosec B311
                reward = random.choice(list(env["rewards"].values())) # Random reward  # nosec B311
                episode_results["agent_rewards"][agent_id] += reward
                
                if reward == env["rewards"].get("collision"): episode_results["collisions"] += 1
                if reward == env["rewards"].get("goal"): episode_results["goals_reached"] += 1
        
        new_episode = {"episode_id": episode_id, "env_id": env_id, "agent_ids": agent_ids, "num_steps": num_steps, "results": episode_results}
        self.data["episodes"][episode_id] = new_episode
        self._save_data()
        return new_episode

    def get_data(self, data_type: str, item_id: str) -> Optional[Dict]:
        """Retrieves data for a specific environment, agent, or episode."""
        if data_type == "environment": return self.data["environments"].get(item_id)
        if data_type == "agent": return self.data["agents"].get(item_id)
        if data_type == "episode": return self.data["episodes"].get(item_id)
        return None

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "define_environment": self.define_environment,
            "define_agent": self.define_agent,
            "run_training_episode": self.run_training_episode,
            "get_data": self.get_data
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MultiAgentRLSimulatorTool functionality...")
    temp_dir = "temp_marl_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    marl_sim = MultiAgentRLSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define an environment
        print("\n--- Defining a grid environment ---")
        marl_sim.execute(operation="define_environment", env_id="grid_world_01", grid_size=10, num_agents=2, rewards={"goal": 10, "collision": -5, "step": -1})
        print("Environment 'grid_world_01' defined.")

        # 2. Define agents
        print("\n--- Defining agents ---")
        marl_sim.execute(operation="define_agent", agent_id="agent_A", agent_type="random_walker", initial_policy="explore")
        marl_sim.execute(operation="define_agent", agent_id="agent_B", agent_type="random_walker", initial_policy="exploit")
        print("Agents 'agent_A' and 'agent_B' defined.")

        # 3. Run a training episode
        print("\n--- Running a training episode ---")
        episode_result = marl_sim.execute(operation="run_training_episode", episode_id="ep_001", env_id="grid_world_01", agent_ids=["agent_A", "agent_B"], num_steps=10)
        print("Episode results:")
        print(json.dumps(episode_result, indent=2))

        # 4. Get environment data
        print("\n--- Getting environment data ---")
        env_data = marl_sim.execute(operation="get_data", data_type="environment", item_id="grid_world_01")
        print(json.dumps(env_data, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
