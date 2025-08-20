# GEMINI Project Guide: AIDE

This document provides essential context and instructions for AI developers working on the AIDE project.

## Project Goal

The primary goal of AIDE is to create a sophisticated and autonomous AI developer agent. This agent should be capable of understanding high-level user requests, formulating a technical plan, and executing that plan by writing, testing, and debugging code until the user's goal is achieved. The system is designed around a multi-agent architecture where specialized agents collaborate to produce a correct and robust final product.

## Current State

The project has successfully implemented its core architecture and codebase awareness features. The current system is a functional multi-agent application (`aide/src/aide/app.py`) that features a hardened, self-correcting feedback loop.

The key components are:
*   **A multi-role agentic workflow:** Spec Generator, Planner, Implementer, Tester, and Critic.
*   **Codebase and API Awareness:** The agent builds a `code_map.json` and can ingest an `api_schema.json` to ground its understanding of the project.
*   **Deterministic Testing:** The `Tester` is a reliable function that runs `pytest` in a correctly configured environment.
*   **Focused Criticism:** The `Critic` agent provides specific, actionable feedback based on clean test reports.
*   **Robust Conventions:** The system enforces a `tests/` directory structure.
*   **Enhanced UX:** All output is colorized for readability using the `rich` library.

## Development Roadmap: The "Step" Files

The canonical development plan for this project is detailed in the series of markdown files named `Step X: ....md`.

*   **Current Status:** Steps 1 through 5 are complete. However, attempts to implement Step 6 (Real-Time Interaction) revealed a critical gap in the agent's ability to manage background processes for testing.
*   **Strategic Pivot:** As a result, **Step 6 has been paused**. The project is now proceeding directly to **Step 7: Process Orchestration and Resilience** to build the foundational tools needed for managing complex, multi-service applications. Once Step 7 is complete, work on Step 6 will resume.

## Core Directive for AI Developers: Plan-Then-Execute

As an AI developer working on this project, you **must** adhere to a structured, plan-first workflow for every task you undertake. The core principle of AIDE is to avoid monolithic, un-plannned implementation. You are to mirror this principle in your own work.

**For any new task, you must follow these steps:**

1.  **Understand the Goal:** First, ensure you have a clear understanding of the user's request.
2.  **Formulate a Plan:** Before writing or modifying any code, you must create a detailed, step-by-step plan.
3.  **Present the Plan:** Share this plan with the user for confirmation before you begin execution.
4.  **Execute the Plan:** Once the plan is approved, execute each step methodically.

This deliberate, spec-first approach is crucial for the success of the project. It reduces errors, ensures clarity, and aligns with the foundational philosophy of the AIDE agent itself.