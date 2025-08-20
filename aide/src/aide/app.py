#!/usr/bin/env python
import os
import subprocess
import sys
import json
import ast
import glob
import asyncio
import websockets
import signal
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from rich import print

# --- Tool Definitions ---
@tool
def read_file_tool(path: str):
    """A tool for reading files."""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return str(e)

@tool
def write_file_tool(path: str, content: str):
    """A tool for writing to files."""
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return str(e)

@tool
def command_runner_tool(command: str):
    """A tool for running shell commands."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return str(e)

@tool
def build_code_map_tool():
    """
    Builds a map of the codebase by parsing all Python files.
    """
    code_map = {}
    # Exclude benchmark files from the code map
    for filepath in glob.glob("**/*.py", recursive=True):
        if "venv" in filepath or ".venv" in filepath or "benchmark_system_DONT_TOUCH" in filepath:
            continue
        with open(filepath, "r") as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
                code_map[filepath] = {
                    "imports": [],
                    "classes": [],
                    "functions": [],
                }
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            code_map[filepath]["imports"].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        code_map[filepath]["imports"].append(node.module)
                    elif isinstance(node, ast.ClassDef):
                        code_map[filepath]["classes"].append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        code_map[filepath]["functions"].append(node.name)
            except Exception as e:
                code_map[filepath] = {"error": f"Failed to parse: {e}"}
    
    with open("code_map.json", "w") as f:
        json.dump(code_map, f, indent=4)
    
    print("[bold blue]Code map written to code_map.json[/]")
    return code_map

@tool
def load_schema_tool(path: str = "api_schema.json"):
    """
    Loads a JSON API schema from the specified path.
    """
    try:
        with open(path, "r") as f:
            schema = json.load(f)
        print(f"[bold blue]API Schema loaded from {path}[/]")
        return schema
    except FileNotFoundError:
        print(f"[yellow]API Schema file not found at {path}. Skipping...[/]")
        return None
    except json.JSONDecodeError:
        print(f"[bold red]Error: Failed to decode JSON from {path}.[/]")
        return None

@tool
def websocket_test_tool(uri: str, message: str):
    """
    Connects to a WebSocket, sends a message, and returns the response.
    """
    async def _test_websocket():
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(message)
                response = await websocket.recv()
                return f"Response: {response}"
        except Exception as e:
            return f"Error: {e}"
    return asyncio.run(_test_websocket())

@tool
def docker_compose_up_tool(compose_file: str = "docker-compose.yml"):
    """
    Starts services using Docker Compose.
    """
    try:
        result = subprocess.run(
            f"docker-compose -f {compose_file} up -d", shell=True, capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return "Docker Compose services started successfully."
        else:
            return f"Error starting Docker Compose services: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

@tool
def docker_compose_down_tool(compose_file: str = "docker-compose.yml"):
    """
    Stops services using Docker Compose.
    """
    try:
        result = subprocess.run(
            f"docker-compose -f {compose_file} down", shell=True, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return "Docker Compose services stopped successfully."
        else:
            return f"Error stopping Docker Compose services: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

# --- Global State ---
tools = [read_file_tool, write_file_tool, command_runner_tool, build_code_map_tool, load_schema_tool, websocket_test_tool, docker_compose_up_tool, docker_compose_down_tool]
tools_map = {t.name: t for t in tools}
project_memory = {}
api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
llm_with_tools = llm.bind_tools(tools)

# --- Agent Core Logic ---
def run_agent_turn(prompt):
    messages = [HumanMessage(content=prompt)]
    context_store = []

    while True:
        result = llm_with_tools.invoke(messages)
        messages.append(result)

        if not result.tool_calls:
            final_answer = result.content
            print(f"[bold green]Assistant:[/ ] {final_answer}")
            return final_answer

        thought = f"Thought: {result.content}"
        print(f"[yellow]Thought:[/ ] {result.content}")
        context_store.append(thought)

        for tool_call in result.tool_calls:
            action = f"Action: {tool_call['name']}({tool_call['args']})"
            print(f"[cyan]Action:[/ ] {tool_call['name']}({tool_call['args']})")
            tool_output = tools_map[tool_call["name"]].invoke(tool_call["args"])
            observation = f"Observation: {tool_output}"
            print(f"[magenta]Observation:[/ ] {tool_output}")
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

# --- Agent Roles ---
def spec_generator(user_input):
    with open("aide/prompts/spec_prompt.txt", "r") as f:
        prompt = f.read().format(user_input=user_input)
    spec_json = run_agent_turn(prompt)
    try:
        # The model sometimes returns the JSON wrapped in ```json ... ```
        if spec_json.startswith("```json"):
            spec_json = spec_json[7:-4]
        spec = json.loads(spec_json)
        with open("spec.json", "w") as f:
            json.dump(spec, f, indent=4)
        print("[bold blue]Specification written to spec.json[/]")
        return spec
    except json.JSONDecodeError:
        print("[bold red]Error: Spec generator did not return valid JSON.[/]")
        return None

def planner(spec):
    with open("aide/prompts/plan_prompt.txt", "r") as f:
        prompt = f.read().format(spec=json.dumps(spec, indent=4))
    plan_json = run_agent_turn(prompt)
    try:
        if plan_json.startswith("```json"):
            plan_json = plan_json[7:-4]
        plan = json.loads(plan_json)
        with open("plan.json", "w") as f:
            json.dump(plan, f, indent=4)
        print("[bold blue]Plan written to plan.json[/]")
        return plan
    except json.JSONDecodeError:
        print("[bold red]Error: Planner did not return valid JSON.[/]")
        return None

def implementer(spec, plan, code_map, api_schema, critic_feedback=""):
    with open("aide/prompts/implementer_prompt.txt", "r") as f:
        prompt = f.read().format(
            spec=json.dumps(spec, indent=4),
            plan=json.dumps(plan, indent=4),
            code_map=json.dumps(code_map, indent=4),
            api_schema=json.dumps(api_schema, indent=4),
            critic_feedback=critic_feedback
        )
    return run_agent_turn(prompt)

def tester(spec):
    """
    Runs tests and generates a report.
    For now, it assumes pytest is installed and will run it.
    """
    # TODO: Determine test command from spec
    command = "PYTHONPATH=. .venv/bin/pytest tests/"
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        
        report = {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

        if result.returncode == 0:
            report["summary"] = "All tests passed."
        else:
            report["summary"] = "Tests failed."

    except subprocess.TimeoutExpired:
        report = {
            "command": command,
            "error": "TimeoutExpired",
            "summary": "Tests timed out.",
        }
    except Exception as e:
        report = {
            "command": command,
            "error": str(e),
            "summary": "An unexpected error occurred during testing.",
        }

    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=4)
    
    print("[bold blue]Test report written to test_report.json[/]")
    return report

def critic(spec, plan, code_map, api_schema, test_report):
    code = ""
    for deliverable in spec.get("deliverables", []):
        # This is a bit of a hack to find the code files
        if "test" not in deliverable:
            if os.path.exists(deliverable):
                with open(deliverable, "r") as f:
                    code += f.read()

    with open("aide/prompts/critic_prompt.txt", "r") as f:
        prompt = f.read().format(
            spec=json.dumps(spec, indent=4),
            plan=json.dumps(plan, indent=4),
            code_map=json.dumps(code_map, indent=4),
            api_schema=json.dumps(api_schema, indent=4),
            test_report=json.dumps(test_report, indent=4),
            code=code
        )
    print(f"[yellow]--- CRITIC PROMPT ---\n{prompt}\n--------------------[/]")
    critic_feedback_json = run_agent_turn(prompt)
    try:
        if critic_feedback_json.startswith("```json"):
            critic_feedback_json = critic_feedback_json[7:-4]
        critic_feedback = json.loads(critic_feedback_json)
        print(f"[bold red]Critic:[/ ] {critic_feedback}")
        return critic_feedback
    except json.JSONDecodeError:
        print("[bold red]Error: Critic did not return valid JSON.[/]")
        return None

# --- Main Execution Loop ---
def main():
    if len(sys.argv) < 2:
        print("Usage: ./aide/src/aide/app.py <user_request>")
        return 1

    user_input = " ".join(sys.argv[1:])
    
    spec = spec_generator(user_input)
    if not spec: return 1

    plan = planner(spec)
    if not plan: return 1
    
    code_map = build_code_map_tool.invoke({})
    api_schema = load_schema_tool.invoke({})

    critic_feedback = ""
    for i in range(3): # Max 3 iterations
        print(f"\n[bold blue]--- ITERATION {i+1} ---")
        
        implementer(spec, plan, code_map, api_schema, critic_feedback)
        
        test_report = tester(spec)
        if not test_report: return 1

        # Check for success
        if "All tests passed." in test_report.get("summary", ""):
            print(f"\n[bold green]--- IMPLEMENTATION SUCCESSFUL ---[/]")
            break
            
        critic_feedback = critic(spec, plan, code_map, api_schema, test_report)
        if not critic_feedback: return 1
    else:
        print(f"\n[bold red]--- FAILED TO FIX AFTER 3 ITERATIONS ---[/]")

if __name__ == "__main__":
    sys.exit(main())
