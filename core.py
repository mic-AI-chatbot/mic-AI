import json
import logging
from typing import AsyncGenerator, Dict, Any

from .llm_loader import get_llm
from .tool_manager import tool_registry

logger = logging.getLogger(__name__)

# A set of tools that are considered purely computational or logical
COMPUTATIONAL_TOOLS = {
    "math_problem_solver",
    "liquid_learning_network",
    # We can add more tools like "puzzle_solver", "graph_analyzer" etc. here
}

def get_hrm_planner_prompt(user_input: str) -> str:
    """
    Creates the meta-prompt for the Planner LLM, instructing it on how to behave within the HRM architecture.
    """
    # We only present the computational tools to the planner.
    # General tools will be handled by a different mechanism if needed.
    tool_descriptions = "\n".join(
        f"- {name}: {tool_registry[name].description}"
        for name in COMPUTATIONAL_TOOLS
        if name in tool_registry
    )

    return f"""You are an expert HRM-Planner. Your task is to analyze the user's request and decide the best way to solve it.

You have two options:
1.  If the request is a general question, a creative task, or a simple conversation, answer it directly based on your own knowledge.
2.  If the request requires a precise logical or mathematical computation, delegate it to a specialized computational tool.

The available computational tools are:
{tool_descriptions}

When delegating to a tool, you MUST respond ONLY with a JSON object in the following format:
{{"tool": "tool_name", "input": "the_exact_input_for_the_tool"}}

Do not provide any other text, explanation, or formatting around the JSON.

---

### Example 1: General Question
User request: Tell me a fun fact about the Roman Empire.
Your response:
A fun fact is that the Romans used a communal sponge on a stick, known as a xylospongium, as their version of toilet paper.

### Example 2: Computational Task
User request: What is the result of 987 divided by 3?
Your response:
{{"tool": "math_problem_solver", "input": "987 / 3"}}

---

Now, analyze the following user request and generate your response.

User request: {user_input}
Your response:
"""

async def process_input(history: list[dict], current_user: str = None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Processes user input using the new HRM (Hierarchical Reasoning Model) architecture.
    """
    if not history:
        yield {"type": "error", "content": "Error: Received empty history."}
        return

    user_input = history[-1].get("content")
    if not user_input:
        yield {"type": "error", "content": "Error: Could not extract user message."}
        return

    # --- HRM Step 1: Planner ---
    # For now, we use the default LLM as our planner.
    # In the future, this could be a router to select between LLMs and SLMs.
    planner_llm = get_llm()
    if planner_llm is None:
        yield {"type": "error", "content": "HRM Planner (LLM) is not available."}
        return

    # Create the detailed prompt for the planner
    planner_prompt = get_hrm_planner_prompt(user_input)

    # Get the full response from the planner, not streaming.
    # The planner's decision (JSON vs. text) is a single atomic unit.
    try:
        planner_response = await planner_llm.get_response(planner_prompt)
        logger.info(f"HRM Planner response: {planner_response}")
    except Exception as e:
        logger.error(f"An error occurred while getting planner response: {e}", exc_info=True)
        yield {"type": "error", "content": "An error occurred while communicating with the HRM Planner."}
        return

    # --- HRM Step 2: Dispatcher ---
    # Check if the planner's response is a command for the "Computer"
    try:
        # A simple but effective check for a JSON object
        if planner_response.strip().startswith("{") and planner_response.strip().endswith("}"):
            command_data = json.loads(planner_response)
            tool_name = command_data.get("tool")
            tool_input = command_data.get("input")

            if tool_name in COMPUTATIONAL_TOOLS and tool_name in tool_registry:
                # --- HRM Step 3: Computer ---
                logger.info(f"HRM Dispatcher: Routing to tool '{tool_name}' with input '{tool_input}'")
                tool_instance = tool_registry[tool_name]
                try:
                    # Execute the computational tool
                    result = tool_instance.execute(query=tool_input)
                    yield {"type": "tool_result", "tool_name": tool_name, "content": str(result)}
                except Exception as e:
                    logger.error(f"Error executing computational tool '{tool_name}': {e}", exc_info=True)
                    yield {"type": "error", "content": f"Error running tool {tool_name}."}
                return # End of computational path
            else:
                # The JSON doesn't match a valid computational tool, so treat it as text
                pass
    except (json.JSONDecodeError, AttributeError):
        # The response is not a valid JSON command, so treat it as a direct answer.
        pass

    # If it's not a valid tool command, stream the planner's response as a direct answer.
    logger.info("HRM Dispatcher: Treating planner response as a direct answer.")
    yield {"type": "token", "content": planner_response}
