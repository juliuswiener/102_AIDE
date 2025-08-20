# AIDE Project Roadmap

This document outlines the future direction for the AIDE project, building upon its current stable, multi-agent core. The original, granular step-by-step plans have been consolidated into this high-level roadmap.

## Phase 1: Codebase and API Awareness

The next major goal is to enhance AIDE's understanding of the projects it works on. This involves giving the agent the ability to "read" and understand the overall structure of a codebase and its external contracts.

*   **API Schema Grounding:** AIDE will be able to ingest API specifications (e.g., OpenAPI/Swagger, Pydantic models). This will allow the `Implementer` to generate code that conforms to the API contract and the `Critic` to validate compliance, preventing the agent from breaking external APIs.
*   **Code Map Generation:** The agent will build a graph of the project's structure, mapping imports, function definitions, and call relationships. This "code map" will help the `Planner` and `Implementer` make more intelligent decisions about which files to edit and how to avoid duplicating code or introducing dependency errors.

## Phase 2: Real-Time and Performance Capabilities

This phase focuses on expanding AIDE's capabilities to handle more complex, real-world application requirements.

*   **Real-Time Interaction:** The `Tester` will be enhanced with tools to test real-time features, such as WebSockets. This will enable AIDE to develop and verify interactive applications.
*   **Performance Optimization:** A new **Performance Agent** will be introduced. This agent will be responsible for running micro-benchmarks, measuring latency and throughput, and suggesting optimizations (e.g., caching, asynchronous I/O) if performance goals are not met.

## Phase 3: Orchestration and Advanced Routing

The final phase aims to equip AIDE with the ability to manage complex, multi-service applications and to make more intelligent decisions about how to approach different types of tasks.

*   **Process Orchestration:** AIDE will gain the ability to manage `docker-compose` environments. This will allow it to spin up entire application stacks (databases, message queues, etc.) to run true end-to-end and integration tests.
*   **Resilience and Chaos Testing:** The agent will be able to inject controlled failures (e.g., killing a service) to test the system's resilience and ensure it can handle real-world fault conditions.
*   **Policy-Based Routing:** A lightweight router model will be introduced at the beginning of the workflow. This router will analyze the user's request and direct it to the most appropriate team of agents. For example, a "bug fix" request might be routed to a specialized "debugger" team, while a "refactor" request might use a different set of agents and models, optimizing for both cost and performance.
