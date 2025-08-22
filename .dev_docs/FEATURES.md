Based on my review of the project documentation, here is a structured list of the features implemented in the AIDE project:

### Core Agent Capabilities

These features define the agent's fundamental abilities to interact, learn, and perform tasks.

*   **Conversational AI:** A command-line interface for interacting with the Gemini Pro model, with a persona focused on Python development.
*   **Conversational Memory:** The agent maintains a history of the last five exchanges, allowing for contextual follow-up questions.
*   **File System Interaction:** The agent can read and write files within a sandboxed `workspace` directory, enabling it to work with a codebase.
*   **Sandboxed Code Execution:** The agent can execute shell commands within a secure Docker container, allowing it to run and test the code it writes.
*   **Web Search Integration:** The agent can perform web searches to find information about libraries, APIs, and error solutions.
*   **Long-Term Memory & Project State:** The agent can persist and load its state, including conversation history and file summaries, allowing it to resume work across sessions.
*   **User Feedback & Clarification:** The agent can ask for user confirmation before performing potentially destructive actions.
*   **Autonomous Planning & Task Decomposition:** The agent can take a high-level goal, create a step-by-step execution plan, and present it to the user for approval before implementation.

### Development Workflow & Tooling

These features describe the multi-agent system and the tools that enable the agent to develop software autonomously.

*   **Multi-Agent Architecture:** The agent's workflow is divided among specialized roles:
    *   **Code Mapper:** Scans the project and creates a `code_map.json` file to provide context to other agents.
    *   **Spec Generator:** Translates user requests into a machine-readable `spec.json`.
    *   **Planner:** Creates a step-by-step `plan.json` from the specification.
    *   **Implementer:** Writes and modifies code based on the plan and code map.
    *   **Tester:** A deterministic function that runs `pytest` to verify the code.
    *   **Critic:** Analyzes test results and provides feedback to the Implementer.
*   **Self-Correcting Feedback Loop:** The agent can loop through the implementation, testing, and criticism phases up to three times to autonomously fix its errors.
*   **Codebase and API Awareness:** The agent uses `code_map.json` and can ingest an `api_schema.json` to understand the existing codebase and APIs.
*   **Deterministic Testing:** The agent uses `pytest` in a correctly configured environment to ensure reliable and accurate test results.
*   **Enhanced User Experience:** All output is color-coded for readability using the `rich` library.
