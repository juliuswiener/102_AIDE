Step 6: Real‑Time Interaction and Performance Optimisation (Phase 2 – Real‑Time & Multi‑Module)
---
**STATUS: PAUSED**

**This step is currently blocked by the requirements of Step 7. The agent's inability to reliably manage background processes for testing (e.g., starting and stopping a web server for WebSocket tests) has made it clear that a robust process orchestration system is a prerequisite. Work on this step will resume after the tools outlined in Step 7 are implemented.**
---

Overview

This step equips AIDE to handle interactive services and performance constraints. Many modern applications require real‑time communication (e.g., WebSockets) and must meet response time budgets. We extend the testing and implementation capabilities to include event‑driven systems and introduce a performance agent that monitors and suggests optimisations. At the end of this step, AIDE should reliably implement and test features involving WebSockets and should be able to diagnose simple performance issues.
System Components

    WebSocket Test Client: A tool that can connect to a running FastAPI/Starlette WebSocket endpoint, send messages, and capture server responses. This allows the tester to verify real‑time behaviour.

    Performance Agent: A new LangGraph node that runs micro‑benchmarks against endpoints or functions, measures latency and throughput, and suggests optimisation strategies based on simple heuristics.

    Updated Tester Agent: Extended to include event‑driven tests. It uses the WebSocket client to check that events are broadcast correctly and that real‑time updates arrive in the proper order. It also invokes the performance agent when relevant.

    Implementer enhancements: The implementer must now be aware of asynchronous programming patterns (e.g., async def functions) and the need to respect performance budgets (e.g., p95 latency under 100 ms).

Implementation Requirements

    WebSocket testing tool

        Implement a reusable test client (e.g., using websockets or asyncio) that can connect to endpoints like ws://localhost:8000/board/<id>.

        The tester should be able to send JSON messages, wait for responses, and assert on their contents. It should support both broadcasting to multiple clients and handling server‑initiated messages.

        Provide an API within the tester agent to specify scripts of actions (e.g., connect, send message, wait, disconnect) and expected outcomes.

    Performance agent

        Create a new node that can be invoked by the tester after functional tests pass. It runs timed requests against HTTP endpoints or functions in isolation.

        Measure key metrics: average latency, p95 latency, throughput (requests per second), and memory usage (if feasible). Use Python’s time and tracemalloc or memory_profiler where appropriate.

        Based on thresholds defined in the spec or configuration (e.g., “p95 < 200 ms”), the agent labels performance as pass/fail and suggests actions (“introduce caching,” “use asynchronous I/O,” “batch database calls”).

    Agent modifications

        Update the implementer prompt to include a note about performance goals (e.g., “Ensure that the WebSocket broadcast completes within 50 ms”). Encourage use of asynchronous constructs and efficient algorithms.

        Extend the critic to review performance reports and, if performance fails, to generate change requests aimed at optimisation.

    Testing procedure

        For Project 2 – Collaborative Task Board, implement and test the real‑time broadcast of card moves. After the functional tests pass, trigger the performance agent to measure broadcast latency under a simulated multi‑client load (e.g., 10 clients moving cards concurrently).

        Define acceptance criteria in the spec, such as “WebSocket updates must broadcast to all clients within 100 ms.”

        Observe that the performance agent detects slow broadcasts and the critic suggests optimisations. The implementer should then adjust the code (e.g., using asyncio.gather instead of sequential sends) and re‑test.

    Deliverables

        Implementation of the WebSocket testing tool and performance agent.

        Updated agent prompts and pipeline definitions.

        Example performance report and optimisation loop demonstrating improvement between iterations.

Notes

Real‑time functionality and performance tuning require careful test design. The performance agent introduced here uses heuristics rather than deep profiling; more advanced analysis (e.g., flame graphs) could be integrated later. This step ensures that AIDE produces not only correct but also responsive software, laying the groundwork for more complex scenarios in Phase 3.
