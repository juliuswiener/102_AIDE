#!/usr/bin/env python3
import sys
import os
from .app import create_graph, AppState, get_project_path
from .utils import log_event

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m aide.src.aide.interactive_runner [--new] <user_request>")
        return 1

    args = sys.argv[1:]
    is_new_project = False
    if args[0] == '--new':
        is_new_project = True
        args.pop(0)
    
    if not args:
        print("Usage: python -m aide.src.aide.interactive_runner [--new] <user_request>")
        return 1

    user_request = " ".join(args)
    
    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    if is_new_project:
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
        "max_iterations": 10,
        "run_performance_test": False,
    }

    for event in app.stream(initial_state):
        for node, output in event.items():
            print(f"--- Node: {node} ---")
            print(output)
            input("Press Enter to continue...")

if __name__ == "__main__":
    sys.exit(main())