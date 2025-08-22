#!/usr/bin/env python
import sys
import json
import os
import re
import subprocess
import difflib
import argparse
from datetime import datetime, timezone
from rich import print
import requests
from aide.graph import create_graph, AppState
from aide.utils import log_event as log_event_util

def get_project_path(user_request: str) -> str:
    """Creates a sanitized and truncated directory name from the user request."""
    sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', user_request).lower()
    sanitized = re.sub(r'\s+', '-', sanitized)
    return os.path.abspath(sanitized[:50])

def log_event(event_type, details):
    log_event_util(event_type, details)

def save_state(state):
    with open("aide_state.json", "w") as f:
        json.dump(state, f, indent=4)

def load_state():
    if not os.path.exists("aide_state.json"):
        return {}
    with open("aide_state.json", "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def read_file_tool(file_path):
    if not os.path.exists(file_path):
        return f"[Errno 2] No such file or directory: '{file_path}'"
    with open(file_path, "r") as f:
        return f.read()

def write_file_tool(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"

def docker_command_runner(command, network_disabled=False):
    try:
        if os.path.exists("Dockerfile"):
            print("--- Building Dockerfile ---")
            build_command = "docker build -t aide-sandbox ."
            build_result = subprocess.run(build_command, shell=True, capture_output=True, text=True)
            if build_result.returncode != 0:
                return f"Error building Dockerfile: {build_result.stderr}"
            image_name = "aide-sandbox"
        else:
            image_name = "python:3.11-slim"

        docker_command = f"docker run --rm"
        if network_disabled:
            docker_command += " --network=none"
        docker_command += f" {image_name} {command}"

        result = subprocess.run(
            docker_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}\nExit Code: {result.returncode}"
        return result.stdout
    except FileNotFoundError:
        return "Docker not found. Please ensure Docker is installed and in your PATH."

def command_runner(command):
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

def command_runner_network_disabled(command):
    return docker_command_runner(command, network_disabled=True)

def build_code_map_tool():
    code_map = {}
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__", "node_modules"]]
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        content = f.read()
                        # A simple way to find classes and functions
                        classes = [line for line in content.split('\n') if line.strip().startswith('class ')]
                        functions = [line for line in content.split('\n') if line.strip().startswith('def ')]
                        code_map[path] = {
                            "classes": {c.split(' ')[1].split('(')[0]: {"methods": {}} for c in classes},
                            "functions": [f.split(' ')[1].split('(')[0] for f in functions],
                        }
                    except Exception as e:
                        code_map[path] = {"error": f"Failed to parse {path}: {e}"}
    with open("code_map.json", "w") as f:
        json.dump(code_map, f, indent=4)
    return "Successfully built and saved code map to code_map.json"

def docker_compose_up_tool():
    result = command_runner("docker-compose up -d")
    if "Error" in result:
        return f"Error starting Docker Compose services.\n{result}"
    return f"Docker Compose services started successfully.\n{result}"

def docker_compose_down_tool():
    result = command_runner("docker-compose down")
    if "Error" in result:
        return f"Error stopping Docker Compose services.\n{result}"
    return f"Docker Compose services stopped successfully.\n{result}"

def docker_compose_logs_tool(service="", lines=100):
    command = f"docker-compose logs --tail={lines} {service}".strip()
    return command_runner(command)

def validate_api_schema_tool(remote_schema_url):
    try:
        response = requests.get(remote_schema_url)
        response.raise_for_status()
        remote_schema = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error fetching remote API schema: {e}"

    try:
        with open("api_schema.json", "r") as f:
            local_schema = json.load(f)
    except FileNotFoundError:
        return "Could not find local API schema file: api_schema.json"
    except json.JSONDecodeError:
        return "Could not decode local API schema file: api_schema.json"

    diff = list(difflib.unified_diff(
        json.dumps(local_schema, indent=2).splitlines(keepends=True),
        json.dumps(remote_schema, indent=2).splitlines(keepends=True),
        fromfile='local_schema.json',
        tofile='remote_schema.json',
    ))

    if not diff:
        return "API schema validation successful."
    else:
        return "API schema validation failed.\n" + "".join(diff)

def get_project_path(user_request: str) -> str:
    """Creates a sanitized and truncated directory name from the user request."""
    sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', user_request).lower()
    sanitized = re.sub(r'\s+', '-', sanitized)
    return os.path.abspath(sanitized[:50])

import argparse

def main():
    parser = argparse.ArgumentParser(description="AIDE - The AI Developer Agent")
    parser.add_argument('--new', action='store_true', help='Start a new project in a new directory.')
    parser.add_argument('--max-iterations', type=int, default=10, help='Set the maximum number of iterations.')
    parser.add_argument('--no-performance-test', action='store_true', help='Skip the performance test.')
    parser.add_argument('user_request', nargs='+', help='The user request for the agent.')
    
    args = parser.parse_args()

    user_request = " ".join(args.user_request)
    
    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    if args.new:
        project_path = get_project_path(user_request)
        print(f"--- Creating new project directory: {project_path} ---")
        os.makedirs(project_path, exist_ok=True)
        os.chdir(project_path)
    
    log_event("session_start", {"user_request": user_request})

    app = create_graph()
    
    initial_state: AppState = {
        "user_request": user_request,
        "app_root": app_root,
        "user_feedback_queue": [],
        "critic_feedback": "",
        "iteration_count": 0,
        "max_iterations": args.max_iterations,
        "run_performance_test": not args.no_performance_test,
    }

    final_state = app.invoke(initial_state)

    print("\n[bold green]--- Run Complete ---")
    if final_state.get("final_summary"):
        print(f"[bold green]Status:[/bold green] {final_state['final_summary']}")
    else:
        print("[bold red]Status:[/bold red] Failed to complete after maximum iterations.")

if __name__ == "__main__":
    sys.exit(main())