AIDE — Autonomous Intelligent Development Environment
Stepwise Requirements (v1.4)
This document describes the incremental build-out of AIDE, broken into eight steps. Each step concludes in a working, testable system.
Step 1 — Minimal Command-Line Chat Agent
Scope
A minimal, command-line interface (CLI) application that accepts user input and provides responses from the Google Gemini API. The agent's persona will be configured to specialize in Python programming questions.
Technology Stack
Language: Python 3.10+
LLM API: Google Gemini API (gemini-1.5-pro model) via the official Python SDK.
Interface: Standard command-line terminal. No web UI for this step.
Functional Requirements
FR1: The system shall provide a command-line prompt where the user can enter plain-text input.
FR2: The system shall send the user's prompt to the Gemini API. The system prompt/persona, which defines its role as a helpful Python expert, will be loaded from a local text file (persona.txt).
FR3: The system shall stream the model's response back to the user's terminal, rendering any markdown for readability.
FR4: The system shall log each exchange (user prompt, final model response, timestamp) as a new line in a file named aide_log.jsonl.
Log Schema: {"timestamp": "YYYY-MM-DDTHH:MM:SSZ", "prompt_text": "...", "response_text": "..."}
Non-Functional Requirements
NFR1: P95 (95th percentile) response latency for prompts under 500 tokens shall be less than 3 seconds.
NFR2: Consistent Persona. The Gemini model's temperature parameter shall be set to 0.2 to ensure high consistency in tone and style for similar prompts.
Acceptance Criteria
AC1: When the user enters the prompt "Write a Python function for factorial", the system returns a syntactically correct and runnable Python function.
AC2: After the exchange in AC1, the aide_log.jsonl file contains a new JSON object matching the specified schema.
AC3: When the same prompt from AC1 is run 3 times, all 3 responses are functionally identical and follow a similar explanatory style.
AC4: A test script confirms that the P95 latency for 20 predefined "small" prompts is below the 3-second threshold.
Step 2 — Conversational Memory
Scope
Extend the agent to maintain a short-term memory of the current conversation, allowing for contextual follow-up questions.
Technology Stack
No changes to the core stack. State management will be handled within the Python application.
Functional Requirements
FR1: The system shall maintain a rolling history of the last 5 user/assistant exchanges.
FR2: On each new prompt, the system shall prepend the conversation history to the prompt before sending it to the Gemini API.
FR3: The user can type /clear to wipe the current conversation history and start fresh.
FR4: The system shall provide a visual confirmation (e.g., "History cleared.") when the /clear command is used.
Non-Functional Requirements
NFR1: Latency with a full context window (5 exchanges) shall not exceed the Step 1 baseline by more than 50%.
NFR2: The logging format remains unchanged; only the final prompt and response are logged, not the entire history.
Acceptance Criteria
AC1: User asks, "Write a Python function for factorial." Then asks, "Now use that function to calculate the factorial of 5." The agent must use the previously generated function in its response.
AC2: After the exchange in AC1, the user types /clear. The system responds with "History cleared."
AC3: After clearing the history, the user asks, "Now use that function to calculate the factorial of 5." The agent responds that it doesn't have the context of the function.
Step 3 — File System Interaction
Scope
Grant the agent the ability to read and write files within a designated, sandboxed workspace directory. This is the first step toward interacting with a codebase.
Technology Stack
No changes to the core stack. File I/O will use standard Python libraries.
Functional Requirements
FR1: The agent can request to read a file by outputting a specially formatted command: <<READ: path/to/file.py>>.
FR2: The agent can request to write content to a file by outputting a command block: <<WRITE: path/to/file.py>>\n<code>\n<</WRITE>>.
FR3: The Python application must parse these commands from the model's output, execute the file operations, and feed the result (e.g., file contents or a success/error message) back to the model for the next turn.
FR4: All file operations are strictly limited to a ./workspace subdirectory. Attempts to access files outside this directory (e.g., ../, /etc/) must be rejected with an error.
Non-Functional Requirements
NFR1: File read/write operations must complete in under 500ms for files up to 1MB.
NFR2: The system provides clear error messages to the model (e.g., "ERROR: File not found at 'path/to/file.py'") which are then relayed to the user.
Acceptance Criteria
AC1: User prompts: "Create a file named hello.py in my workspace that prints 'Hello, World!'". The system should create ./workspace/hello.py with the correct content.
AC2: User prompts: "What is in the hello.py file?". The system should read the file and output its contents.
AC3: User prompts: "Read the file ../../my_secrets.txt". The system must refuse and state that access is denied.
Step 4 — Sandboxed Code Execution
Scope
Enable the agent to execute code it has written, capture the output (stdout/stderr), and use it as feedback for debugging and iteration. This creates the core "development loop."
Technology Stack
Sandboxing: Docker. Code execution will occur inside ephemeral Docker containers to ensure security.
Execution: Python's subprocess library will be used to invoke Docker commands.
Functional Requirements
FR1: The agent can request to execute a shell command by outputting a command: <<EXEC: python workspace/hello.py>>.
FR2: The application will execute the command inside a secure, sandboxed Docker container with the ./workspace directory mounted.
FR3: The stdout and stderr from the execution are captured and fed back to the model in the next turn.
FR4: A strict timeout (e.g., 30 seconds) is enforced on all code executions to prevent infinite loops.
Non-Functional Requirements
NFR1: Security: The execution environment must be fully isolated from the host system's file system and network, with the sole exception of the mounted workspace. This is a critical requirement.
NFR2: The overhead for container startup and execution should not exceed 5 seconds.
Acceptance Criteria
AC1: User prompts: "Write a Python script in fibonacci.py to print the first 10 Fibonacci numbers, then run it." The system writes the file and then executes it, showing the correct output.
AC2: User prompts: "Write a Python script in error.py that divides by zero, then run it." The system executes the script and correctly reports the ZeroDivisionError traceback.
AC3: Given the error in AC2, the user prompts: "Okay, fix the bug in error.py and run it again." The agent should propose a fix, write it to the file, and execute it successfully.
Step 5 — Web Search Integration
Scope
Enable the agent to perform web searches to gather external information, such as library documentation, API examples, or solutions to error messages.
Technology Stack
API: A web search API (e.g., Google Custom Search API, Tavily API).
Functional Requirements
FR1: The agent can request a web search by outputting a command: <<SEARCH: "query terms">>.
FR2: The application layer calls the designated search API with the provided query.
FR3: The application processes the search results, extracting concise snippets and source URLs.
FR4: The processed results are fed back to the model in its next turn, providing it with external knowledge.
Non-Functional Requirements
NFR1: Search API calls must have a timeout of 5 seconds.
NFR2: The formatted search results fed to the model must be token-efficient, prioritizing content over boilerplate.
Acceptance Criteria
AC1: User prompts: "What is the latest stable version of the Flask library?". The agent performs a search and returns the correct version number.
AC2: When encountering an error from Step 4 (e.g., a ModuleNotFoundError), the user can prompt: "Search for a solution to this error." The agent should search for the error string and suggest a fix (e.g., a pip install command).
Step 6 — Long-Term Memory & Project State
Scope
Implement a mechanism for persisting the agent's state between sessions, allowing it to "remember" the project context, conversation history, and key files.
Technology Stack
Storage: A local SQLite database or a structured JSON file for state management.
Functional Requirements
FR1: Before the application closes, it saves the current conversation history and a summary of the workspace file tree to a local state file.
FR2: On startup, the application loads this state file, repopulating the agent's conversational memory and awareness of the project.
FR3: The agent can request an updated summary of the workspace at any time to refresh its long-term memory.
Non-Functional Requirements
NFR1: State saving and loading operations must complete in under 1 second.
NFR2: The persisted state should not grow indefinitely; conversation history should be intelligently summarized or truncated.
Acceptance Criteria
AC1: In one session, the user has the agent create a file config.py. The user then closes the application.
AC2: The user reopens the application and prompts: "What was the file we created in our last session?". The agent correctly identifies config.py.
Step 7 — User Feedback & Clarification Loop
Scope
Empower the agent to ask clarifying questions or request confirmation before performing potentially destructive or ambiguous actions.
Technology Stack
No new technology. This is an interaction pattern built on existing capabilities.
Functional Requirements
FR1: The agent can pause its operation and ask for user confirmation by outputting a special command: <<CONFIRM: "I am about to delete main.py. Proceed? [y/n]">>.
FR2: The application layer detects this command, presents the question to the user, and waits for a y/n input.
FR3: The user's affirmative or negative response is fed back to the model, which then decides on the next action.
Non-Functional Requirements
NFR1: Confirmation prompts must be clear, specific, and present a default safe option (e.g., defaulting to 'no' on invalid input).
Acceptance Criteria
AC1: User prompts: "Delete the workspace."
AC2: The agent responds with a confirmation prompt like <<CONFIRM: "This will delete all files in the ./workspace directory. Are you absolutely sure? [y/n]">>.
AC3: User enters "y". The agent proceeds to delete the files. If the user enters "n", the agent cancels the operation.
Step 8 — Autonomous Planning & Task Decomposition
Scope
For complex, multi-step tasks, enable the agent to first generate a high-level plan, present it to the user for approval, and then execute that plan autonomously.
Technology Stack
This is an advanced prompting and state-management challenge.
Functional Requirements
FR1: When given a high-level goal (e.g., "Create a simple Flask API with a /health endpoint"), the agent's first action is to generate a step-by-step plan.
FR2: The plan is presented to the user for review and approval before any tools (WRITE, EXEC) are used.
FR3: Once the user approves the plan, the agent begins executing the steps sequentially, using its available tools and reporting its progress.
FR4: The agent must be able to handle errors during plan execution and attempt to self-correct (e.g., by debugging a script that failed).
Non-Functional Requirements
NFR1: Generated plans must be logical, ordered, and composed of actions the agent can actually perform with its tools.
NFR2: The agent must maintain an internal state of the plan's progress (e.g., which step it's on).
Acceptance Criteria
AC1: User prompts: "Create a Python package that has a function to add two numbers and include a simple test for it."
AC2: The agent produces a plan (e.g., 1. Create directory structure. 2. Write setup.py. 3. Write function code. 4. Write test code. 5. Execute tests).
AC3: After user approval, the agent executes the plan, resulting in a complete, tested Python package in the workspace.

