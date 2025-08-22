import os
import subprocess
import json
import ast
import glob
import asyncio
import websockets
from langchain_core.tools import tool
from rich import print
from jsondiff import diff

# --- Config Management ---

CONFIG_FILE = "aide_config.json"
SESSION_APPROVALS = set()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

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
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return str(e)

@tool
def command_runner_tool(command: str):
    """
    A tool for running shell commands directly in the workspace.
    Requires user approval for each new command.
    """
    config = load_config()
    approved_commands = config.get("approved_commands", {})

    if command in approved_commands and approved_commands[command] == "always":
        print(f"[bold green]Executing pre-approved command:[/bold green] {command}")
        return _execute_command(command)

    if command in SESSION_APPROVALS:
        print(f"[bold green]Executing session-approved command:[/bold green] {command}")
        return _execute_command(command)

    print(f"[bold yellow]Execution approval required for command:[/bold yellow] {command}")
    print("Approve execution? (y/n, or: once, session, always)")
    approval = input().lower().strip()

    if approval in ["always", "session", "once", "y", "yes"]:
        if approval == "always":
            approved_commands[command] = "always"
            config["approved_commands"] = approved_commands
            save_config(config)
            SESSION_APPROVALS.add(command)
        elif approval == "session":
            SESSION_APPROVALS.add(command)
        
        return _execute_command(command)
    else:
        return "Command execution denied by user."

def _execute_command(command: str):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}\nExit Code: {result.returncode}"
        return result.stdout
    except FileNotFoundError:
        return "Command not found."

@tool
def build_code_map_tool():
    """Builds a map of the codebase by parsing all Python files."""
    code_map = {}
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
    """Loads a JSON API schema from the specified path."""
    try:
        with open(path, "r") as f:
            schema = json.load(f)
        print(f"[bold blue]API Schema loaded from {{path}}[/]")
        return schema
    except FileNotFoundError:
        print(f"[yellow]API Schema file not found at {{path}}. Skipping...[/]")
        return None
    except json.JSONDecodeError:
        print(f"[bold red]Error: Failed to decode JSON from {{path}}.[/]")
        return None

@tool
def websocket_test_tool(uri: str, message: str):
    """Connects to a WebSocket, sends a message, and returns the response."""
    async def _test_websocket():
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(message)
                response = await websocket.recv()
                return f"Response: {{response}}"
        except Exception as e:
            return f"Error: {{e}}"
    return asyncio.run(_test_websocket())

@tool
def run_benchmark_tool(url: str, requests: int = 100, concurrency: int = 10):
    """Runs a benchmark against a URL using 'ab' (Apache Benchmark)."""
    try:
        command = f"ab -n {{requests}} -c {{concurrency}} {{url}}"
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error running benchmark: {{result.stderr}}"
    except FileNotFoundError:
        return "Error: 'ab' (Apache Benchmark) is not installed. Please install it to run performance tests."
    except Exception as e:
        return f"Error: {{e}}"

@tool
def request_user_confirmation_tool(prompt: str):
    """Asks the user for a yes/no confirmation."""
    return f"Confirmation requested: {{prompt}}"

@tool
def validate_api_schema_tool(url: str = "http://127.0.0.1:8000/openapi.json", schema_path: str = "api_schema.json"):
    """
    Validates the running application's OpenAPI schema against the project's schema file.
    This tool should be used by the tester agent after the application has been started.
    """
    print(f"[bold blue]Validating API schema against {{url}}...[/bold blue]")
    try:
        with open(schema_path, "r") as f:
            project_schema = json.load(f)
        try:
            import requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            running_schema = response.json()
        except Exception as e:
            return f"Error fetching schema from running application: {{e}}. Make sure the service is running and accessible at {{url}}."
        differences = diff(project_schema, running_schema)
        if not differences:
            return "API schema validation successful. The running application's schema matches the project schema."
        else:
            return f"API schema validation failed. Differences found: {{json.dumps(differences, indent=2)}}"
    except FileNotFoundError:
        return f"Error: Project schema file not found at {{schema_path}}."
    except json.JSONDecodeError:
        return f"Error: Failed to decode JSON from {{schema_path}}."
    except Exception as e:
        return f"An unexpected error occurred: {{e}}"