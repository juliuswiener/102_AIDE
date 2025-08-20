# AIDE - Autonomous AI Developer

AIDE is an autonomous AI developer agent that takes high-level user requests, generates a technical specification and plan, and then implements the required code through a robust, iterative loop of writing, testing, and self-correction.

## Current State

The project's core is a sophisticated multi-agent system built with Python, Langchain, and Google's Gemini models. The system features a hardened feedback loop for code generation and is now aware of the codebase it is modifying.

The output is color-coded for readability using the `rich` library.

### The Agentic Workflow

The `aide/src/aide/app.py` script orchestrates a sequence of roles:

1.  **Code Mapper:** Before the main loop begins, the agent scans the project directory and builds a `code_map.json` file. This file outlines the imports, classes, and functions in each Python file, giving the other agents essential context.
2.  **Spec Generator:** Takes a natural language request and produces a detailed, machine-readable `spec.json` file.
3.  **Planner:** Reads the `spec.json` and creates a concrete, step-by-step `plan.json`, which includes establishing a `tests/` directory for clean code organization.
4.  **Implementer:** Executes the plan by writing and modifying code. It consults the `code_map.json` to understand the existing codebase and avoid redundancy.
5.  **Tester:** A deterministic function (not an LLM) that runs `pytest` on the `tests/` directory. It correctly sets the `PYTHONPATH` to ensure modules are found, producing a clean and accurate `test_report.json`.
6.  **Critic:** Analyzes the test report, code, and code map to provide specific, actionable feedback to the `Implementer` if tests fail.

This entire process can loop up to three times, allowing the system to autonomously recover from implementation errors and converge on a correct solution.

## How to Run

The agent is executed from the command line.

1.  **Set up the environment:**
    ```bash
    # Create a virtual environment
    python -m venv .venv
    
    # Install dependencies
    .venv/bin/pip install -r aide/requirements.txt
    
    # Set your API key
    export GEMINI_API_KEY="YOUR_API_KEY"
    ```

2.  **Run the agent:**
    ```bash
    .venv/bin/python aide/src/aide/app.py "Your feature request here"
    ```
    For example:
    ```bash
    .venv/bin/python aide/src/aide/app.py "Create a python script that adds two numbers from the command line"
    ```

## Project Roadmap

The project is following the detailed plans in the `Step X` markdown files. The next phase of development is the "API Schema Grounding" portion of `Step 5`.
