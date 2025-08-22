import os
from typing import TypedDict, List, Annotated
import json
from langgraph.graph import StateGraph, END, START
from rich import print
from .models import (
    Agent,
    llm_default,
    default_tools_map,
    llm_implementer,
    implementer_tools_map,
    llm_refactor,
    llm_tester,
    tester_tools_map,
)
from .tools import (
    build_code_map_tool,
    load_schema_tool,
)
from .utils import check_for_user_input

# --- Graph State ---

class AppState(TypedDict):
    user_request: str
    app_root: str
    policy: str
    spec: dict
    plan: dict
    code_map: dict
    api_schema: dict
    critic_feedback: Annotated[List[dict], lambda _, y: y]
    user_feedback_queue: List[str]
    iteration_count: int
    max_iterations: int
    run_performance_test: bool
    test_report: dict
    performance_report: dict
    final_summary: str

# --- Agent Nodes ---

def router_node(state: AppState):
    print("--- Calling Router Agent ---")
    router_agent = Agent(llm_default, default_tools_map, "aide/prompts/router_prompt.txt", app_root=state["app_root"])
    result = router_agent.run(user_input=state["user_request"])
    policy = result.get("policy", "implement") if result else "implement"
    return {"policy": policy, "iteration_count": 0}

def spec_node(state: AppState):
    print("--- Calling Spec Agent ---")
    spec_agent = Agent(llm_default, default_tools_map, "aide/prompts/spec_prompt.txt", "spec.json", app_root=state["app_root"])
    spec = spec_agent.run(user_input=state["user_request"])
    return {"spec": spec}

def generate_plan_prompt():
    return """You are a senior software developer acting as a planner. Your job is to take a technical specification and produce a concrete, step-by-step plan for implementation.

The plan must be a JSON object with a single key, "plan", which is a list of strings. Each string should be a single, actionable step.

**Instructions:**
1.  Read the `spec.json` carefully.
2.  If the project involves any external APIs or libraries you are not familiar with, your **first step** must be to use the `web_search_tool` to find documentation.
3.  Break down the implementation into small, logical steps.
4.  For each step, specify the file to be modified and the changes to be made.
5.  If the project is complex and has external dependencies, include steps for creating a `Dockerfile` to manage dependencies. For simple scripts, this is not necessary.
6.  Include steps for writing tests. All test files must be placed in a `tests/` directory.
7.  Include steps for running the tests.
8.  Respond with a single JSON object containing a list of strings, where each string is a step in the plan.

**Specification:**
{spec}


**Example Plan:**
```json
{{
  "plan": [
    "Create a file named `calculator.py`",
    "Write a function named `add` in `calculator.py` that takes two numbers as input and returns their sum.",
    "Create a directory named `tests`",
    "Create a file named `test_calculator.py` inside the `tests` directory",
    "In `test_calculator.py`, write a test case using a testing framework (e.g., `pytest`) to verify the functionality of the `add` function in `calculator.py`.",
    "Run the tests using the command `pytest tests/`."
  ]
}}
```"""

def plan_node(state: AppState):
    print("--- Calling Plan Agent ---")
    prompt_content = generate_plan_prompt()
    prompt_path = "aide/prompts/plan_prompt.txt"
    full_prompt_path = os.path.join(state["app_root"], prompt_path)
    os.makedirs(os.path.dirname(full_prompt_path), exist_ok=True)
    with open(full_prompt_path, "w") as f:
        f.write(prompt_content)
    plan_agent = Agent(llm_default, default_tools_map, prompt_path, "plan.json", app_root=state["app_root"])
    plan = plan_agent.run(spec=json.dumps(state["spec"], indent=4))
    return {"plan": plan}

def research_node(state: AppState):
    print("--- Calling Research Agent ---")
    research_agent = Agent(llm_default, default_tools_map, "aide/prompts/research_prompt.txt", "spec.json", app_root=state["app_root"])
    spec = research_agent.run(user_input=state["user_request"], plan=json.dumps(state["plan"], indent=4))
    return {"spec": spec}

def debug_node(state: AppState):
    print("--- Calling Debug Implementer ---")
    debug_agent = Agent(llm_implementer, implementer_tools_map, "aide/prompts/debug_implementer_prompt.txt", app_root=state["app_root"])
    debug_agent.run(
        spec=json.dumps(state["spec"], indent=4),
        plan=json.dumps({"fix": "Analyze the test report and fix the code based on the errors."}, indent=4),
        code_map=json.dumps(state["code_map"], indent=4),
        api_schema=json.dumps(state["api_schema"], indent=4),
        critic_feedback=state.get("critic_feedback", ""),
        user_feedback="\n".join(state.get("user_feedback_queue", [])),
        test_report=json.dumps(state.get("test_report", {}), indent=4)
    )
    return {"iteration_count": state["iteration_count"] + 1}

def refactor_node(state: AppState):
    print("--- Calling Refactor Implementer ---")
    refactor_agent = Agent(llm_refactor, implementer_tools_map, "aide/prompts/refactor_implementer_prompt.txt", app_root=state["app_root"])
    plan_agent = Agent(llm_default, default_tools_map, "aide/prompts/plan_prompt.txt", "plan.json", app_root=state["app_root"])
    plan = plan_agent.run(spec=json.dumps(state["spec"], indent=4))
    if not plan:
        return {"plan": {"error": "Failed to generate a refactoring plan."}}
    refactor_agent.run(
        spec=json.dumps(state["spec"], indent=4),
        plan=json.dumps(plan, indent=4),
        code_map=json.dumps(state["code_map"], indent=4),
        api_schema=json.dumps(state["api_schema"], indent=4),
        user_feedback="\n".join(state.get("user_feedback_queue", [])),
    )
    return {"plan": plan, "iteration_count": state["iteration_count"] + 1}

def generate_implementer_prompt():
    return """You are an expert software developer. Your task is to implement the software described in the specification, following the provided plan.

You have access to the following tools:
- `write_file_tool(path, content)`: Writes content to a file.
- `read_file_tool(path)`: Reads the content of a file.
- `command_runner_tool(command)`: Executes a shell command.
- `web_search_tool(query)`: Searches the web for information.
- `websocket_test_tool(uri, message)`: Connects to a WebSocket, sends a message, and returns the response.
- `docker_compose_up_tool(compose_file)`: Starts services using Docker Compose.
- `docker_compose_down_tool(compose_file)`: Stops services using Docker Compose.

**Instructions:**
1.  **Strictly Adhere to the API Schema:** The provided API Schema is the source of truth. Your implementation **must** match the endpoints, data models, and status codes defined in it. Any deviation is a failure.
2.  Consult the **Code Map** to understand existing code and avoid duplication.
3.  Follow the plan step by step. Your job is to **write the code**.
4.  **Do not run any tests or build any images.** That is the Tester agent's job.
5.  If the plan includes a `Dockerfile`, create it. Otherwise, you can skip it.
6.  If you encounter an error, an unknown library, or an ambiguous requirement, use the `web_search_tool` to find information before proceeding.
7.  If you receive feedback from the critic, address it carefully.
8.  When you have finished writing all the code, you must respond with a JSON object containing a list of tool calls that will create the files.

**Expected Output Format:**

You must respond with a single JSON object. This object should contain a key "tool_calls", which is a list of dictionaries. Each dictionary represents a single tool call.

```json
{{
  "tool_calls": [
    {{
      "tool_name": "write_file_tool",
      "args": {{
        "path": "calculator.py",
        "content": "def add(a, b):\n    return a + b\n"
      }}
    }},
    {{
      "tool_name": "write_file_tool",
      "args": {{
        "path": "tests/test_calculator.py",
        "content": "import calculator\n\ndef test_add():\n    assert calculator.add(2, 3) == 5\n"
      }}
    }}
  ]
}}
```

**Specification:**
{spec}

**Plan:**
{plan}

**Code Map:**
{code_map}

**API Schema:**
{api_schema}

**Critic Feedback:**
{critic_feedback}

**User Feedback:**
{user_feedback}
"""

def implementer_node(state: AppState):
    policy = state["policy"]
    print(f"--- Calling Implementer Agent (Policy: {policy}, Iteration: {state['iteration_count'] + 1}) ---")
    prompt_path = "aide/prompts/implementer_prompt.txt"
    prompt_content = generate_implementer_prompt()
    full_prompt_path = os.path.join(state["app_root"], prompt_path)
    os.makedirs(os.path.dirname(full_prompt_path), exist_ok=True)
    with open(full_prompt_path, "w") as f:
        f.write(prompt_content)
    implementer_agent = Agent(llm_implementer, implementer_tools_map, prompt_path, app_root=state["app_root"])
    agent_args = {
        "spec": json.dumps(state["spec"], indent=4),
        "plan": json.dumps(state["plan"], indent=4),
        "code_map": json.dumps(state["code_map"], indent=4),
        "api_schema": json.dumps(state["api_schema"], indent=4),
        "critic_feedback": state.get("critic_feedback", ""),
        "user_feedback": "\n".join(state.get("user_feedback_queue", [])),
    }
    implementer_agent.run(**agent_args)
    return {"iteration_count": state["iteration_count"] + 1}


def tester_node(state: AppState):
    print("--- Calling Tester Agent ---")
    tester_agent = Agent(llm_tester, tester_tools_map, "aide/prompts/tester_prompt.txt", "test_report.json", app_root=state["app_root"])
    test_report = tester_agent.run(spec=json.dumps(state["spec"], indent=4))
    return {"test_report": test_report}

def critic_node(state: AppState):
    print("--- Calling Critic Agent ---")
    critic_agent = Agent(llm_default, default_tools_map, "aide/prompts/critic_prompt.txt", app_root=state["app_root"])
    code_for_critic = ""
    if state["code_map"]:
        for file_path in state["code_map"].keys():
            try:
                with open(file_path, "r") as f:
                    code_for_critic += f"---\n{file_path} ---\n{f.read()}\n\n"
            except FileNotFoundError:
                pass
    critic_feedback = critic_agent.run(
        spec=json.dumps(state["spec"], indent=4),
        plan=json.dumps(state["plan"], indent=4),
        code_map=json.dumps(state["code_map"], indent=4),
        api_schema=json.dumps(state["api_schema"], indent=4),
        test_report=json.dumps(state["test_report"], indent=4),
        performance_report=json.dumps(state.get("performance_report", {}), indent=4),
        user_feedback="\n".join(state["user_feedback_queue"]),
        code=code_for_critic
    )
    return {"critic_feedback": critic_feedback}

def reset_state_node(state: AppState):
    print("--- Resetting State ---")
    return {
        "test_report": None,
        "critic_feedback": None,
    }

def code_map_node(state: AppState):
    print("--- Building Code Map ---")
    code_map = build_code_map_tool.invoke({})
    return {"code_map": code_map}

def schema_load_node(state: AppState):
    print("--- Loading API Schema ---")
    api_schema = load_schema_tool.invoke({})
    return {"api_schema": api_schema}

def plan_approval_node(state: AppState):
    print("[bold blue]Generated Plan:[/bold blue]")
    print(json.dumps(state["plan"], indent=4))
    print("Do you approve this plan? [y/n]")
    user_approval = input().lower()
    if user_approval != 'y':
        print("Plan rejected. Exiting.")
        return {"final_summary": "Plan rejected by user."}
    return {}

def user_input_node(state: AppState):
    critic_feedback = state.get("critic_feedback")
    if critic_feedback and isinstance(critic_feedback, list) and critic_feedback:
        print("[bold yellow]--- Critic Feedback ---[/bold yellow]")
        for i, item in enumerate(critic_feedback):
            severity = item.get('severity', 'N/A').upper()
            print(f"[bold]{i + 1}. [{severity}] {item.get('description')}[/bold]")

        print("\n[bold yellow]Please select the feedback items to address (e.g., '1,3', 'critical', 'all'), or press Enter to finish.[/bold yellow]")
        selection = input().lower().strip()

        if not selection:
            return {"critic_feedback": []}

        selected_feedback = []
        if selection == 'all':
            selected_feedback = critic_feedback
        else:
            try:
                # Handle severity selection
                if selection in ['critical', 'major', 'minor']:
                    selected_feedback = [item for item in critic_feedback if item.get('severity', '').lower() == selection]
                # Handle numeric selection
                else:
                    indices = [int(i.strip()) - 1 for i in selection.split(',')]
                    selected_feedback = [critic_feedback[i] for i in indices if 0 <= i < len(critic_feedback)]
            except (ValueError, IndexError):
                print("[bold red]Invalid selection. Continuing with all feedback.[/bold red]")
                selected_feedback = critic_feedback
        
        return {"critic_feedback": selected_feedback}

    print("\n[bold yellow]Awaiting user input... (Press Enter to continue without feedback)[/bold yellow]")
    user_input = check_for_user_input()
    if user_input:
        print(f"[bold green]Feedback received:[/bold green] {user_input}")
        current_queue = state.get("user_feedback_queue", [])
        current_queue.append(user_input)
        return {"user_feedback_queue": current_queue}
    
    return {}


def route_after_router(state: AppState):
    policy = state["policy"]
    if policy == "research":
        return "plan_node"
    elif policy == "debug":
        return "spec_node"
    elif policy == "refactor":
        return "spec_node"
    elif policy == "exit" or policy == "clarify":
        return END
    return "spec_node"

def route_after_spec(state: AppState):
    policy = state["policy"]
    if policy == "debug":
        return "tester_node"
    elif policy == "refactor":
        return "refactor_node"
    return "plan_node"

def route_after_plan(state: AppState):
    policy = state["policy"]
    if policy == "research":
        return "research_node"
    return "plan_approval_node"

def route_after_approval(state: AppState):
    if state.get("final_summary"):
        return END
    return ["code_map_node", "schema_load_node"]

def route_after_critic(state: AppState):
    if state["iteration_count"] >= state["max_iterations"]:
        print("[bold red]Max iterations reached. Ending run.[/bold red]")
        return END
    
    critic_feedback = state.get("critic_feedback")
    if isinstance(critic_feedback, list) and not critic_feedback:
        print("[bold green]Critic is satisfied. Moving to final steps.[/bold green]")
        if state["run_performance_test"]:
            return "performance_node"
        else:
            print("[bold green]Performance test skipped. Implementation complete.[/bold green]")
            return END
    else:
        return "user_input_node"

def route_after_user_input(state: AppState):
    critic_feedback = state.get("critic_feedback")
    if isinstance(critic_feedback, list) and not critic_feedback:
        if state["run_performance_test"]:
            return "performance_node"
        else:
            print("[bold green]Performance test skipped. Implementation complete.[/bold green]")
            return END
    else:
        return "implementer_node"

def create_graph():
    workflow = StateGraph(AppState)
    workflow.add_node("router_node", router_node)
    workflow.add_node("spec_node", spec_node)
    workflow.add_node("plan_node", plan_node)
    workflow.add_node("research_node", research_node)
    workflow.add_node("debug_node", debug_node)
    workflow.add_node("refactor_node", refactor_node)
    workflow.add_node("code_map_node", code_map_node)
    workflow.add_node("schema_load_node", schema_load_node)
    workflow.add_node("reset_state_node", reset_state_node)
    workflow.add_node("implementer_node", implementer_node)
    workflow.add_node("tester_node", tester_node)
    workflow.add_node("critic_node", critic_node)
    workflow.add_node("performance_node", performance_node)
    workflow.add_node("user_input_node", user_input_node)
    workflow.add_node("plan_approval_node", plan_approval_node)
    
    workflow.add_edge(START, "router_node")
    workflow.add_conditional_edges("router_node", route_after_router)
    workflow.add_conditional_edges("spec_node", route_after_spec)
    workflow.add_conditional_edges("plan_node", route_after_plan)
    workflow.add_conditional_edges("plan_approval_node", route_after_approval)
    workflow.add_edge("research_node", "plan_approval_node")
    workflow.add_edge("refactor_node", "plan_approval_node")
    workflow.add_edge("debug_node", "reset_state_node")
    workflow.add_edge("code_map_node", "schema_load_node")
    workflow.add_edge("schema_load_node", "reset_state_node")
    workflow.add_edge("reset_state_node", "implementer_node")
    workflow.add_edge("implementer_node", "tester_node")
    workflow.add_edge("tester_node", "critic_node")

    workflow.add_conditional_edges(
        "critic_node",
        route_after_critic,
        {
            "user_input_node": "user_input_node",
            "performance_node": "performance_node",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "user_input_node",
        route_after_user_input,
        {
            "implementer_node": "implementer_node",
            "performance_node": "performance_node",
            END: END
        }
    )
    
    workflow.add_edge("performance_node", END)
    return workflow.compile()