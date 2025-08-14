Step 1: Minimal Chat Agent (Phase 0 – MVP)
Overview

The goal of the first implementation step is to produce a basic programming assistant that can respond to simple coding requests. At this stage the system is intentionally minimal: a single large language model (LLM) node backed by Gemini acts as a chat agent. The system exposes only two tools to the agent: a file system interface for reading and writing files within a project workspace, and a command runner for executing shell commands such as running unit tests. There is no planning or multiple agents yet; the agent simply converses with the user and can use the tools in a simple ReAct loop. This step should end with a working system capable of performing trivial tasks, such as creating a file and running a provided test harness.
System Components

    LLM node: A single chat agent using the fast tier of the Gemini model. The agent operates within a LangGraph graph but uses only one vertex.

    File system tool: Exposes read/write access to files under a sandboxed working directory. The agent can create or modify files (e.g., project/index.py), read source files, and list directory contents. File operations outside the working directory are prohibited.

    Command runner tool: Allows the agent to run commands in the working directory. For example, it can execute pytest -q to run unit tests, python file.py to run a script, or ls to inspect the workspace. Each command execution must be sandboxed with a timeout to prevent runaway processes.

    Conversation interface: The user sends a natural language task description. The agent replies with a concise plan and uses the available tools to fulfil the request. After tool use, the agent returns the final answer to the user.

Implementation Requirements

    Project structure

        Implement the system using LangGraph. A minimal graph with a single vertex representing the Gemini chat agent is sufficient. The vertex should be configured to call the Gemini API. Future steps will add more vertices.

        Include two tool definitions: one for file operations (read_file, write_file, list_files) and one for running shell commands (run). Each tool must enforce sandboxing by restricting the working directory and applying execution timeouts (e.g., 30 seconds per command).

        Provide a main.py or serve.py entrypoint that starts the chat loop. The entrypoint should create a workspace directory (e.g., ./workspace) and mount the file system tool there.

    Gemini configuration

        Use the fastest (cost‑efficient) Gemini chat model available. Set a sensible temperature (e.g., 0.2) to favour determinism for reproducible results.

        Ensure the Gemini API key is supplied via environment variable or configuration file. The key should not be hard‑coded in the repository.

    Agent behaviour

        The agent should follow a simple ReAct pattern: think (analyse user request), act (call tool), observe (parse tool response), then produce an answer. There is no separate planning phase; the logic can be coded directly into the prompt given to the agent.

        The prompt must instruct the agent to produce clear, concise messages and to call tools when necessary. For example, to run tests, it should call the command runner with pytest -q.

        At the end of the interaction, the agent returns its final answer to the user, such as “All tests passed” or a description of the implemented feature.

    Testing criteria

        After completing this step, the system should be able to handle simple tasks like “Create an empty Python file called main.py” or “Run the tests.”

        To verify functionality, use the harness provided with the seed projects:

            Copy one of the benchmark projects into the workspace directory (e.g., the Knowledge Base Generator seed from project1_kb.zip).

            Ask the agent to run the project’s test suite by calling pytest -q. The agent should use the command runner tool and then report the results.

            Ask the agent to create or modify a file and check that the file appears in the workspace.

        Successful completion of these tasks demonstrates that the file system and command runner tools are correctly wired and that the agent can interact with them.

    Deliverables

        Source code implementing the LangGraph graph with a single Gemini node and the two tools.

        README documenting how to run the system locally. It should describe how to supply the Gemini API key, how to start the server, and how to interact with the agent via the command line or an HTTP endpoint.

        Example transcripts demonstrating use of the file system and command runner tools.

Future Work

This minimal agent establishes a foundation for more advanced capabilities. Subsequent steps will introduce specialised agents for planning, implementation, testing, and critique, along with richer memory management and routing logic. Each step will build on this foundation to produce a progressively more autonomous programming system.