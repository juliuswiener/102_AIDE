Step 5: API Schema Grounding and Code Map (Phase 2 – Real‑Time & Multi‑Module)
Overview

The fifth implementation step expands AIDE’s awareness of project structure and external contracts. As we progress into larger, multi‑module systems and interactive services, it becomes crucial that the implementer does not inadvertently break API contracts or misjudge cross‑file relationships. This step introduces two key enhancements:

    API Schema Grounding: Provide the implementer with explicit knowledge of API specifications (e.g., OpenAPI/Swagger definitions or Pydantic models). By grounding the LLM on these schemas, we reduce invalid endpoint implementations and parameter mismatches.

    Code Map Generation: Build a graph of imports, function definitions, and call relationships across the project. The implementer can consult this map to avoid duplicating functions, misnaming identifiers, or breaking dependencies. The code map also assists the planner in identifying which files need to change for a given task.

System Components

    API Schema Loader: A tool or agent that reads JSON/YAML OpenAPI files (or Pydantic model definitions) from the project, validates them, and makes them available to other agents. This can run at the start of each session or on demand.

    Code Map Builder: A process that statically analyses the Python codebase, extracting function names, class definitions, imports, and call relationships. The output is a simple graph representation (e.g., adjacency lists) stored in the project memory.

    Enhanced Implementer Agent: Modified to accept API schemas and code maps as context. It must consult these resources when editing or creating endpoints, ensuring that signatures and responses match the defined schema.

    Validators: Lightweight checks that can assert whether the current code conforms to the API schema (e.g., using datamodel-code-generator or Python type hints). These checks run after each change and feed into the tester and critic.

Implementation Requirements

    API Schema ingestion

        Define a new tool, load_schema, that accepts a path to an OpenAPI specification or a module containing Pydantic models. The tool reads and validates the schema, storing it in memory.

        At the start of an implementation session, automatically call load_schema on all API definition files (e.g., openapi.yaml, schemas.py).

        Expose a summarised version of the schema to the LLM (e.g., names of endpoints, input and output parameters) to avoid exceeding context limits.

    Code map generation

        Implement a script or tool, build_code_map, which parses Python files using ast or a static analysis library. It should record:

            Modules imported and their aliases.

            Classes and functions defined in each file.

            Calls from one function or method to another (within the project).

        Store the resulting map in a machine‑readable format, such as code_map.json. Update this map after each code change.

        Provide a summarised view of the map to the implementer (e.g., “api.py defines get_documents, which calls search_documents in services/search.py”).

    Agent modifications

        Augment the implementer’s prompt to include a section summarising the API schema and code map. For example:

            “Available endpoints: GET /documents → returns list of documents (fields: id, title, summary) defined in openapi.yaml.
            Your edits must conform to this specification.”

        Modify the critic’s prompt to check that changes maintain API contract compliance. If a mismatch is detected (e.g., missing parameter), the critic must generate a change request.

    Validation checks

        After each iteration, run validation scripts that compare the implemented endpoints against the schema. Report any deviations in the test_report.json or a separate schema_report.json.

        The tester agent should incorporate these reports into its summary of failures.

    Testing procedure

        Use Project 2 – Collaborative Task Board as a testbed. This project exposes multiple REST and WebSocket endpoints. Delete or rename one of the endpoints and ask the system to restore it based on the OpenAPI definition.

        Observe that the implementer references the schema and code map to locate where to insert or adjust functions.

        Verify that the final implementation passes both the unit tests and the schema validation.

    Deliverables

        Implementation of load_schema and build_code_map tools.

        Updated agent prompts and pipeline wiring to include API schema and code map context.

        Example code_map.json output for a seed project and demonstration of the implementer using it to make targeted changes.

Notes

Grounding the assistant in explicit API definitions and code relationships is a powerful way to align its outputs with user expectations and existing code. It also reduces hallucinations about endpoint names or parameters. This step sets the foundation for more advanced routing and multi‑module planning in subsequent steps.

---

## Completion Summary

The **Code Map Generation** portion of this step has been fully implemented.

*   A new tool, `build_code_map_tool`, was added to `aide/src/aide/app.py`. It uses Python's `ast` and `glob` modules to scan the project for `.py` files and generate a `code_map.json` file. This file details the imports, classes, and functions within each Python source file.
*   The main execution loop in `app.py` was updated to call this tool at the beginning of each run, ensuring the agent always has an up-to-date view of the codebase.
*   The `implementer` and `critic` agent prompts (`implementer_prompt.txt` and `critic_prompt.txt`) were updated to include the `code_map.json` as context, enabling them to make more informed decisions.
*   The `build_code_map_tool` is configured to ignore files in `venv`, `.venv`, and `benchmark_system_DONT_TOUCH` directories to avoid parsing irrelevant code.

The **API Schema Grounding** portion of this step has not yet been implemented and will be the focus of the next development cycle.