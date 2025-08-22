Multi-Agent Patterns Tier List for Autonomous Coding Pipelines
S-Tier (core—you'll feel them every day)

Single Supervisor → Specialists — Central brain with coder/tester/refactorer; highest control, clear logs, predictable latency.
Spec-First Agent — Turns vague asks into spec/RFC/tests; slashes rework and drift (the biggest win in autonomy).
ReAct (Reason+Act with tools) — Tight loop of think→call→check; best for bugfix, API lookups, compiler/runtime errors.
Unit-Test Synthesizer — Auto-writes/updates tests from spec & diffs; unlocks safe refactors + CI autonomy.
Code/Docs RAG Agent — Repo+docs retrieval grounding; cuts hallucinations and speeds context building.
Execution Sandbox Agent — Actually runs code, captures traces/errors; closes the loop from "writes" to "works".
Concurrent Agent Execution — Parallel task processing with synchronization; massive throughput gains for independent subtasks.

A-Tier (strong accelerators; add early)

Policy/Preference Router (e.g., Arch-Router) — Deterministic routing to {Implement|Debug|Refactor|Research} subgraphs; great for compliance & reproducibility.
Critic / Reviewer Loop — Second agent red-teams outputs (correctness/style/security); big quality lift with modest cost.
Static-Analysis Agent — Linters/types/SEMgrep; cheap, catches lots of issues pre-run.
PR Agent — Branch/commit/PR description/changelog; reduces human glue work, speeds review.
Planner–Executor — High-level plan then do; improves coherence in multi-file/features.
API-Schema Grounding — Feed OpenAPI/GraphQL/Proto; fewer invalid calls, safer integrations.
Project Memory (artifact store) — Durable plans/decisions/code maps; keeps agents consistent across sessions.
Workflow Orchestrators (Temporal/Airflow-style) — Durable execution, retries, state machines; solves reliability at scale.
Fork-Join Parallelism — Split work, parallelize, merge results; critical for multi-file changes.
Checkpoint/Resume — Pause expensive runs, migrate between models/machines; essential for long-running tasks.
Blackboard/Shared Workspace — Agents read/write to common state; enables emergent coordination without tight coupling.

B-Tier (situationally great; add when needed)

Hierarchical Supervisors ("teams of teams") — Scales for monorepos/domains; more ops overhead.
Self-Consistency / Ensemble Voting — Sample & vote for tricky tasks; boosts pass@k, costs tokens.
Graph/Tree Search (ToT/GoT) — Branch/prune solution paths; shines on algorithms/complex refactors.
Benchmark/Perf Agent — Profiles and proposes optimizations; valuable for latency/throughput tickets.
Issue Triage Agent — Labels/estimates/routes; helpful at scale, less critical for small teams.
Judge/Rater Agent (policy scoring) — Scores outputs to train routers & gate merges; needs a good rubric.
Event-Driven/Pub-Sub — Async event streams between agents; better for large-scale decoupling.
Actor Model — Message-passing, no shared state; cleaner boundaries but more complex debugging.
Pipeline with Buffering — Stages process at different rates with queues; smooths out latency spikes.
Shared Context Window Management — Efficiently share/compress/prioritize context between agents.
Reflection/Metacognition — Agent evaluates its own reasoning and adjusts strategy; powerful but token-heavy.
Migration/Upgrade Agent — Handles breaking changes, dependency updates; huge time-saver for mature codebases.
Chain-of-Verification — Self-check reasoning steps; improves reliability on complex logic.

C-Tier (nice, but lower ROI early)

Marketplace / Peer-to-Peer Agents — Exploratory swarms; hard to bound cost/latency, messy observability.
Debate / Adversarial Pair — Can help on ambiguous specs or complex algos; slower and noisy.
Mixture-of-Experts (external) — Great on server GPUs; tooling on edge and observability are weaker.
Merged-Model Experiments — Incremental gains, but adds versioning/licensing complexity.
Consensus Protocols — Multiple agents must agree; overkill unless you need Byzantine fault tolerance.
STM/LTM Split — Short vs. long-term memory; complex to tune, marginal gains in coding tasks.
Episodic Memory Replay — Learn from past runs; hard to implement well, context limits hurt.
Constitutional AI/RLAIF loops — Agents trained by other agents; research-y, not production-ready.
Program Synthesis — Generate executable planning code; brittle, often easier to use text plans.
Incremental/Streaming Processing — Process tokens as they arrive; complexity rarely worth it for coding.
Delta Encoding — Only transmit changes between states; premature optimization for most pipelines.
Attention Routing — Dynamically allocate context budget; too complex vs. simple heuristics.

Cross-cutting Ops (apply across tiers)

Guardrails / Schema-only outputs — Force JSON/YAML/AST for routers & CI glue.
Budget/Latency Controller — Token/time caps per task; prevents runaway costs.
Human-in-the-Loop Breakpoints — Require approval for spec sign-off, risky migrations, prod touches.
Contextual Bandits (shadow router) — Online cost/quality tuning once you have feedback signals.
Backpressure/Circuit Breakers — Prevent cascade failures when one agent slows; critical at scale.
WebSocket/SSE Patterns — Real-time agent communication with clients; essential for IDE integrations.

Minimal high-leverage stack (what I'd ship first)
S: Supervisor → {Implement, Debug, Refactor, Research}, Spec-First, ReAct, Tests, RAG, Sandbox, Concurrent Execution
A: Policy Router, Critic, Static-Analysis, PR Agent, API-Schema Grounding, Project Memory, Workflow Orchestrator, Fork-Join
(Then add B-tier pieces as scale/needs dictate.)

Key additions:

Concurrent Agent Execution promoted to S-tier - it's fundamental for throughput
Workflow Orchestrators in A-tier - production reliability requires durable execution
Fork-Join in A-tier - natural companion to concurrent execution
Most academic/complex patterns (Constitutional AI, Program Synthesis) placed in C-tier - interesting but not production-ready

