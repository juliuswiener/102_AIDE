Step 9: Interactive Tooling, Memory, and User Collaboration
---
**STATUS: PENDING**

**This step outlines the integration of key features from the original v1.4 roadmap. The current multi-agent system bypassed these in favor of a fully autonomous workflow. This step aims to bridge that gap by re-introducing web search capabilities, state persistence, and a user-in-the-loop feedback mechanism to create a more robust, secure, and collaborative agent.**
---
Overview

The current AIDE system is a powerful autonomous agent but lacks external awareness, long-term memory, and user interaction beyond the initial prompt. This step addresses these critical omissions by integrating features that were part of the original vision: a web search tool for external knowledge gathering, a state-management system for session persistence, a secure sandboxed environment for code execution, and a confirmation loop to ensure user oversight on critical decisions. Completing this step will make the agent safer, more knowledgeable, and capable of tackling problems that require context beyond the immediate codebase.

System Components

    1.  **Web Search Tool**: A new tool that allows agents to query an external search engine (e.g., Google, Tavily) to find documentation, resolve errors, or research libraries.

    2.  **State Management Module**: A persistence layer responsible for saving the project's context (e.g., the latest spec, plan, and a summary of key files) to a local file (`aide_state.json`) on exit and loading it on startup.

    3.  **Secure Execution Environment**: A replacement for the current `command_runner_tool` that uses Docker to execute all shell commands within a sandboxed container, preventing any potential harm to the host system.

    4.  **User Confirmation Hook**: A special tool (`request_user_confirmation_tool`) that allows an agent to pause execution and ask the user for a `y/n` confirmation before proceeding with a potentially destructive or ambiguous action.

    5.  **Plan Approval Checkpoint**: A new step in the main application loop that presents the generated plan to the user for approval before the implementation phase begins.

    6.  **Queued User Input Handler**: A mechanism that allows the user to type instructions while the agent is running. These instructions are queued and injected into the agent's context at the next available opportunity in the loop, allowing for non-disruptive course-correction.

Implementation Requirements

    1.  **Web Search Integration**
        *   Implement a `web_search_tool(query: str)` in `aide/src/aide/app.py`. This tool will use a third-party search API.
        *   Add the new tool to the global `tools` list available to the agents.
        *   Update the `implementer_prompt.txt` and `critic_prompt.txt` to encourage the agents to use the search tool when encountering errors, unknown libraries, or ambiguous requirements.

    2.  **Long-Term Memory**
        *   In `app.py`, create `save_state()` and `load_state()` functions.
        *   `save_state()` will write a dictionary containing the current `spec.json`, `plan.json`, and a list of key project files to `aide_state.json` upon successful completion.
        *   `load_state()` will run at startup, loading the contents of `aide_state.json` into the `project_memory` dictionary if the file exists.
        *   The `spec_generator` and `planner` should be made aware of the loaded state to provide context for new tasks.

    3.  **Sandboxed Code Execution (Security)**
        *   Modify the existing `command_runner_tool`.
        *   The tool's implementation must be changed from `subprocess.run(command)` to a function that constructs and executes a `docker run` command.
        *   The Docker command must:
            *   Use a minimal base image (e.g., `python:3.11-slim`).
            *   Mount the current project directory as a read-write volume.
            *   Enforce a strict execution timeout.
            *   Run as a non-root user inside the container.
        *   This is a critical security upgrade to meet the original project requirements.

    4.  **User Feedback & Plan Approval**
        *   Implement a `request_user_confirmation_tool(prompt: str)` and add it to the `tools` list. When called, the main loop will intercept it, prompt the user, and return the boolean result to the agent.
        *   In the `main()` function of `app.py`, after the `planner` successfully generates `plan.json`, pretty-print the plan to the console.
        *   Prompt the user for confirmation: "Do you approve this plan? [y/n]". The program will exit if the user does not approve.

    5.  **Structured Logging**
        *   Create a new logging utility that writes structured JSON entries to a file named `aide_log.jsonl`.
        *   Log key events in the main application loop, such as the start and end of each agent's turn, every tool call made, and every user confirmation received.
        *   The log schema should be adapted for the multi-agent system: `{"timestamp": "...", "event_type": "agent_start|tool_call|user_feedback", "details": {...}}`.

    6.  **Queued User Input**
        *   The main application will use a non-blocking method (e.g., Python's `select` module) to check for user input from `sys.stdin` at the start of each main iteration loop.
        *   A new variable, `user_feedback_queue`, will be maintained throughout the main loop.
        *   If user input is detected, it will be read and appended to the `user_feedback_queue`.
        *   This queue will be passed as a new argument to the `implementer` and `critic` agents. Their prompts will be updated to instruct them to treat input from this queue as a high-priority directive that can override the current plan.

Testing Procedure

    *   **Web Search:** Provide a prompt that requires external knowledge, such as "Implement a feature using the 'beautifultable' library." The agent should fail, and the critic should suggest using the web search tool to find installation and usage instructions.
    *   **Memory:** In one session, ask the agent to create a new utility file. After it succeeds, terminate the application. Relaunch and ask it to add a new function to that same utility file. The agent should know the file exists from the loaded state.
    *   **Sandboxing:** Verify that commands are now executed via Docker by inspecting running processes or logs.
    *   **User Confirmation:** Give the agent a task and approve the plan. During implementation, if the agent decides to delete a file not mentioned in the plan, it should use the confirmation tool. Verify that the application pauses and waits for user input.
    *   **Plan Approval:** Run any task and verify that the application prints the generated plan and waits for a 'y' from the user before proceeding to the implementation loop.
    *   **Queued Input:** Start a multi-step task. While the implementer is in its first iteration, type a new instruction like "Please add comments to all functions." Verify that the *next* iteration's code generation includes comments, demonstrating the agent course-corrected based on the queued input.

Deliverables

    *   An updated `aide/src/aide/app.py` containing the new tools, state management functions, Docker-based command runner, and modified main loop.
    *   Updated agent prompts that incorporate the new capabilities.
    *   This `Step9_MissingFeatures.md` document.
