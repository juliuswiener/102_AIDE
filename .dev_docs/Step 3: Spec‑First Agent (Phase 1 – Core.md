Step 3: Spec‑First Agent (Phase 1 – Core Autonomy)
Overview

The third implementation step introduces a dedicated Spec‑First agent, marking the transition from a simple chat bot to a structured autonomous programming assistant. The goal of this step is for AIDE to produce an explicit specification from a user’s high‑level request before writing any code. This mini‑spec includes a clear objective, acceptance criteria, non‑goals, and an initial test plan. The Spec‑First agent will operate as the first node in a multi‑agent LangGraph pipeline. At the end of this step, the system will produce a machine‑readable specification document for any request, enabling subsequent agents to implement and test against it.
Motivation

Writing code without a clear specification often leads to misunderstandings and rework. By forcing the system to articulate what it will build, we reduce ambiguity and provide a durable artifact that later agents and human reviewers can inspect. A machine‑readable spec also allows automatic test generation and planning in later steps.
System Components

    Spec‑First node: A new LangGraph node that receives the user prompt and returns a specification document.

    Specification schema: A defined JSON structure for the spec. Fields should include:

        title: A one‑sentence summary of the desired software.

        description: A paragraph outlining the overall purpose and user value.

        acceptance_criteria: A list of bullet points describing what constitutes a successful solution (e.g., “search endpoint returns relevant documents sorted by score”).

        non_goals: (optional) Items explicitly out of scope for this request.

        deliverables: List of artifacts to be produced (files, endpoints, CLI commands).

        tests_to_run: Names of tests or test suites (if known) that must pass. Initially this may be empty; later phases will update it.

    Storage of spec: The spec should be written to the project workspace (e.g., spec.json or spec.yaml) and stored in the project memory component for later retrieval.

    LLM configuration: Use the same Gemini model as earlier phases but with a prompt instructing it to produce well‑structured specs.

Implementation Requirements

    Add the Spec‑First node to the graph

        Introduce a second vertex in the LangGraph pipeline that runs before the implementation and test agents.

        The new node should accept the user’s high‑level request and produce the spec as output. It does not have access to file or command tools; its job is purely analytical.

        Ensure the node’s output is passed downstream in a structured format (e.g., as a dict or JSON string) rather than free text.

    Prompt design

        Provide a system prompt that instructs the LLM to ask clarifying questions if the request is ambiguous. However, for this step we assume simple tasks so clarifications may not be needed.

        The model must adhere strictly to the specification schema. Use JSON with named fields, and require bullet lists for the criteria.

        Example prompt excerpt:

            “You are a specification writer. Given a short description of a piece of software, produce a JSON document with keys title, description, acceptance_criteria, non_goals, deliverables, and tests_to_run. Use bullet points in lists. Do not invent details not present in the input; instead, ask for clarification if necessary.”

    Specification storage and validation

        After generating the spec, write it to a file in the workspace (e.g., spec.json). This ensures persistence across different agent calls.

        Validate the JSON against a schema to ensure required fields are present and correctly typed. If validation fails, the agent should attempt to rectify or ask the user for clarification.

    Testing procedure

        Use a simple user prompt such as “Build a CLI tool to add two numbers” and verify that the Spec‑First node outputs a sensible spec with acceptance criteria and deliverables.

        Test that the spec file is created in the workspace and that its structure matches the expected schema.

        For seed projects, run the Spec‑First agent on the existing prompts; ensure the output spec reflects the project goals (e.g., indexing documents, searching, tagging for the KB generator).

    Deliverables

        Updated LangGraph pipeline with a Spec‑First node and single downstream chat node (the implementer will come in a later step).

        JSON schema definition for the spec document.

        Documentation describing the purpose of the Spec‑First agent and how it interacts with other nodes.

Outcome

Upon completion of this step, AIDE will produce explicit specifications for user requests before any implementation begins. This artifact will enable more predictable development in later stages and sets the stage for automated planning and testing.