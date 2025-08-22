Step 2: Basic ReAct Loop Enhancement (Phase 0 – MVP)
Overview

In the second implementation step we extend the minimal chat agent to adopt a more structured Reason–Act–Observe (ReAct) loop. While the initial system could call tools, it had no explicit reasoning cycle and lacked any persistent memory. This step introduces a lightweight in‑memory context store and modifies the agent prompt to reflect the ReAct pattern. The system remains single‑agent but becomes more capable at solving tasks that require iterative tool usage and short‑term memory, such as identifying test failures and fixing them in subsequent edits. At the end of this step, the agent will be able to complete simple modifications to project files based on test feedback.
System Enhancements

    Context memory: Implement an in‑session context store that holds the last few tool observations (e.g., command outputs, file contents) and previous assistant thoughts. This memory must be passed back to the Gemini model via the prompt so that the agent can refer to prior actions when deciding what to do next.

    ReAct prompt structure: Update the agent’s system prompt to instruct the LLM to follow a ReAct cycle:

        Thought: The agent describes its reasoning in plain language without calling any tools.

        Action: If necessary, the agent invokes a tool by emitting a JSON object specifying the tool name and arguments.

        Observation: The system executes the tool call and returns the output. The agent stores this in memory.

        The cycle repeats until the agent determines that the task is complete.

    Short‑term plan: Encourage the agent to generate a brief plan at the start of each session that outlines the high‑level steps it intends to follow. This plan should be stored in memory and referenced as the agent works through the task.

Implementation Requirements

    Memory implementation

        Create an in‑memory buffer that accumulates the last N observations and thoughts (e.g., N = 5). When the buffer reaches capacity, discard the oldest entries.

        Modify the LangGraph node to include this memory buffer in the prompt along with the latest user question and system instructions.

        Each entry should clearly separate the “Thought,” “Action,” and “Observation” sections so that the model sees the chronological chain of events.

    Prompt modifications

        The system prompt must clearly explain the ReAct loop. For example:

            “You will think through the problem out loud in the Thought section. When you decide to use a tool, output a JSON with the tool name and parameters in the Action section. After the tool executes, you will see its output in the Observation section. Continue this cycle until you have solved the problem. Provide your final answer at the end.”

        Emphasise that the agent should not fabricate tool outputs. It must wait for the actual observation before continuing.

    Tool call format

        Standardise the tool invocation format to a single JSON object per action. For example:

        {"tool": "run", "cmd": "pytest -q"}

        The executor should parse this JSON, execute the requested tool, capture output and errors, and return the result in the Observation section.

    Testing tasks

        Use the harness with Project 1 – Knowledge Base Generator or Project 2 – Collaborative Task Board seeds to test the new system. Suitable tests include:

            Identify failing tests: Ask the agent to run pytest -q on a seed project. It should read the failing test output, reason about the cause, edit the relevant file, and rerun the tests until they pass.

            Add a simple function: Request the agent to implement a trivial function (e.g., return the number of documents in the index) and verify the tests.

        Success is defined by the agent using the ReAct loop: it should clearly articulate thoughts, call tools in the proper JSON format, observe results, and iterate until tests pass.

    Deliverables

        Updated agent code that implements the ReAct cycle and memory buffer.

        Revised prompt template reflecting the new instructions.

        Example transcripts demonstrating the ReAct pattern: these should show distinct “Thought,” “Action,” and “Observation” lines and illustrate how the agent iterates on failing tests.

Notes

While this step still relies on a single agent, the ReAct pattern and memory management lay the groundwork for the multi‑agent designs introduced in later phases. By practising iterative reasoning and tool usage, the agent becomes more reliable when addressing tasks that require multiple edits or incremental adjustments.