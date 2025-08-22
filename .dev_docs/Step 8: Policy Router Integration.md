Step 8: Policy Router Integration (Phase 3 – Job Orchestration & Resilience)
Overview

The final implementation step introduces policy‑based routing to determine which subgraph of agents and which model tier should handle a given request. Up to this point, AIDE has used fixed sequences of agents for all tasks. However, different types of tasks (implementation, debugging, refactoring, research) benefit from different prompts, models, and tool budgets. A policy router sits at the entry of the LangGraph pipeline, reads the user request, and selects a route based on a set of human‑defined policies. We will use a lightweight 1.5B‑parameter router model (e.g., Arch‑Router) to align routing with organisational preferences. This step ends with a more flexible and efficient system that can dynamically choose the best path for a task.
System Components

    Router model: A small language model trained to map a user request and a list of available policies to one of those policies. Policies are simple strings such as implement, debug, refactor, or research. You can use the publicly available Arch‑Router model or any similar routing model.

    Policy set: A human‑authored table mapping policies to subgraphs and model selection. Each policy determines which sequence of agents to run and which model or prompt to use. Different tasks benefit from specialised models and fine‑tuned prompts
    arxiv.org
    . For example:
    Policy	Subgraph	Model / Tier	Description
    implement	Spec→Plan→Implement→Test→Critic	Fast Gemini (general)	Normal end‑to‑end feature implementation
    debug	Plan→Implement→Test→Critic	Fast Gemini (debug prompt)	Rapidly fix code to satisfy failing tests
    refactor	Plan→Refactor→Test→Critic	Code‑specialised LLM¹	Large‑scale structural changes
    research	Research→Spec→Plan	Deep Gemini (research prompt)	Explore a new library or tool before coding

    ¹For instance, a code‑specialised model such as CodeLlama or another model fine‑tuned for code generation
    arxiv.org
    can be used for refactoring and complex code synthesis.

    Routing node: A new LangGraph node that ingests the user request, the policy set, and calls the router model to select the appropriate policy. The node outputs the policy identifier.

    Dispatcher: After the policy is selected, the dispatcher chooses the corresponding subgraph and model or prompt. It may decide between different tiers of the same model (e.g., fast vs. deep) or between entirely different specialised models (e.g., a general LLM vs. a code‑specific LLM). The rest of the agents then operate as configured.

Implementation Requirements

    Define policy taxonomy

        Work with stakeholders to enumerate the types of tasks AIDE must handle. At minimum include implement, debug, refactor, and research. Each policy should have a clear description and associated subgraph.

        Store the policy definitions in a JSON or YAML file that the router node will load at runtime.

    Integrate the router model

        Download or install the 1.5B router model (e.g., from the Arch‑Router paper). Ensure it can run on your hardware (CPU or GPU) within an acceptable latency (∼50 ms per request). Quantise to 4‑bit if necessary for edge deployment.

        Implement a route function that accepts the user message and the list of policies and returns a policy identifier. The function should call the router model, include the policy descriptions in the prompt, and parse the chosen identifier from the output.

    Update LangGraph pipeline

        Insert a routing node at the entry of the graph. It takes the user request and outputs the selected policy.

        Use a dispatcher to conditionally invoke one of several subgraphs (predefined sequences of agents) based on the chosen policy. Each subgraph may specify a different model tier (fast vs. deep Gemini) and a different set of tools.

        Ensure that the router’s output is logged and stored for auditing.

    Model selection and prompts

        Extend the configuration to map each policy not only to a subgraph but also to a specific model or prompt. For example, use a general Gemini for typical implementations, a debug‑tuned prompt for bug fixing, and a code‑specialised LLM for refactoring or complex generation tasks
        arxiv.org
        . The router’s output should include both the policy and the model identifier.

        Provide fallback options: if a specialised model is unavailable, default to the general model. Enable AIDE operators to override model selection via configuration.

        Document how to add new specialised models or prompts to the policy table. This encourages experimentation with emerging code LLMs without altering the routing logic.

    Fallback and overrides

        Implement a fallback mechanism: if the router model cannot determine a policy (e.g., confidence below a threshold), default to a safe subgraph such as implement.

        Allow human operators to override the router’s decision by specifying a policy manually. Provide a configuration option or command‑line flag for this purpose.

    Testing procedure

        Create a set of user requests that map clearly to different policies (e.g., “Add a new API endpoint” → implement, “Fix the failing test in file x” → debug, “Rewrite the authentication module for better structure” → refactor). Submit these to the system and verify that the router selects the appropriate policy.

        Run end‑to‑end tests on all three seed projects using different policies. For example:

            Use implement to add missing features.

            Use debug to intentionally break a test and ask the system to fix it.

            Use refactor to reorganise modules while preserving behaviour. Observe that the deep Gemini tier is used and the performance agent still monitors latency.

        Evaluate that the overall completion rate improves and that costs are optimised by routing tasks to the cheaper model tier when appropriate.

    Deliverables

        Policy taxonomy document and routing configuration.

        Implementation of the router node and dispatcher in LangGraph.

        Example logs demonstrating different routing decisions and their outcomes.

        Updated documentation explaining how to add new policies and adjust the router.

Notes

Policy‑based routing is the last major structural enhancement in the initial AIDE roadmap. It provides flexibility and efficiency by matching tasks to the appropriate agent pipelines and model tiers. Future work may explore dynamic learning of policies or multi‑objective optimisation, but this step completes the foundational architecture.