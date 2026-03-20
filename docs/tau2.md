# τ²-bench: Evaluating Conversational Agents in a Dual-Control Environment

**Paper**: [arXiv 2506.07982](https://arxiv.org/abs/2506.07982) (June 2025)
**Authors**: Victor Barres, Honghua Dong, Soham Ray, Xujie Si, Karthik Narasimhan (Princeton)

## Motivation

τ-bench tests agents in "single-control" settings — only the AI agent has tools; the user is a passive information provider. But real-world interactions often require **both parties to take actions**. For example, a telecom support call where the agent modifies account settings while the user toggles airplane mode or reseats their SIM card.

τ²-bench introduces **dual-control environments** where both agent and user possess distinct tools operating on a shared, dynamic world state. This reveals a new failure mode: **coordination failures** between agent and user, separate from pure reasoning errors.

## What's New vs. τ-bench

| Aspect | τ-bench | τ²-bench |
|--------|---------|----------|
| Control | Single (agent only has tools) | Dual (both agent and user have tools) |
| Domains | Retail, Airline | + Telecom (new) |
| User simulator | LLM-prompted | Tightly coupled with environment via tool constraints |
| Task generation | Manually authored | Compositional generator from atomic components |
| Failure analysis | Overall pass rate | Reasoning vs. communication/coordination decomposition |
| Formalism | Implicit | Dec-POMDP (Decentralized Partially Observable MDP) |

## Benchmark Design

### Dec-POMDP Formulation

Interactions are modeled as Decentralized POMDPs:
- **Message space (M)**: Natural language exchanges between agent and user
- **State space**: Decomposed into agent database, user database, and interaction history
- **Action spaces**: Each party can either send a message OR make a tool call (mutually exclusive per turn)
- **Observation spaces**: Each party sees tool results or peer messages (partial observability)
- **Reward**: Based on task completion verification via assertion functions

### Telecom Domain

A troubleshooting domain with meaningful dual-control:

**Agent tools** (CRM side):
- Customer lookup, service management, account modifications

**User tools** (phone side):
- Toggle airplane mode, reseat SIM card, check phone state

**Task types**: 3 user intents — `service_issue`, `mobile_data_issue`, `mms_issue`

**User personas**: None, Easy, Hard — testing communication across expertise levels (e.g., a "Hard" user may not understand technical instructions well)

**Scale**: 15 atomic task groups → 2,285 potential tasks; 114 used in evaluation

### Compositional Task Generator

Tasks are programmatically assembled from atomic components:
1. **Initialization functions** — set the problem state (e.g., disable a service, put phone in airplane mode)
2. **Solution functions** — specify the required fix sequence
3. **Assertion functions** — verify success conditions on the final state

This enables systematic complexity scaling and automatic verification of task correctness — a significant improvement over τ-bench's manually-authored tasks.

### Improved User Simulator

Key innovation: the user simulator is **tightly coupled with the environment** through tool constraints rather than relying solely on natural language prompting. The user simulator can only take actions that the environment permits (e.g., can only toggle airplane mode if their phone has that capability).

This dramatically reduces simulation errors:
- **Telecom**: 6% critical error rate (3/50 conversations)
- **Retail**: 12% critical error rate (6/50 conversations)
- **Airline**: 13% critical error rate (13/100 conversations)

The telecom domain's lower error rate demonstrates that grounding user behavior in tool affordances is more reliable than prompt-only simulation.

## Results

### Performance Across Domains

| Model | Telecom pass@1 | Retail pass@1 | Airline pass@1 |
|-------|---------------|--------------|----------------|
| GPT-4.1 | 34% | 74% | 56% |
| O4-mini | 42% | — | — |
| Claude 3.7 Sonnet | 49% | — | — |

Telecom is significantly harder than retail/airline, primarily due to the dual-control coordination requirement.

### Critical Finding: Reasoning vs. Coordination

Ablation studies isolating the two failure modes:

| Setting | GPT-4.1 | O4-mini |
|---------|---------|---------|
| **No-User** (pure reasoning, no coordination) | 52% | 59% |
| **Default** (full dual-control) | 34% | 34% |
| **Performance drop from coordination** | **-18%** | **-25%** |

~20% absolute performance drop comes purely from **communication and coordination requirements** — not from reasoning about the task itself. This is a major finding: current LLMs struggle with coordinating actions between parties even when they can reason about the task correctly in isolation.

### Complexity Effects

- Performance degrades sharply with action count — near-zero for tasks requiring >7 actions
- Multi-stage issues (e.g., mobile data requiring both service checks and phone-side fixes) are substantially harder
- "Hard" user personas reduce success rates vs. "Easy" personas

### Policy Format Impact

Workflow-based (flowchart) policies improved performance in Default and No-User modes but **hurt** Oracle Plan performance — suggesting that ground-truth action sequences can conflict with flowchart-style guidance.

## Relevance to Our Work

τ²-bench introduces coordination complexity that's distinct from but related to the LiC/context editing problem:

1. **Communication failures as a distinct failure mode**: Like LiC's finding that conversation history causes errors, τ²-bench shows that the *interaction itself* (not just accumulated context) degrades performance. The ~20% coordination penalty is conceptually similar to the multi-turn penalty in LiC.

2. **User simulation quality matters**: Their finding that tool-constrained user simulation is more reliable than prompt-only simulation is relevant to our UserAgent design. Our sharded-disclosure approach is a form of constrained user behavior.

3. **Compositional task generation**: Their programmatic task generator with assertion-based verification is a more scalable approach than manual task authoring. Could be useful if we expand our evaluation suite.

4. **Dec-POMDP framing**: The formal framework clarifies that multi-turn agent problems involve partial observability and decentralized control — both parties act with incomplete information. Context editing can be seen as improving one party's (the assistant's) observability by cleaning up misleading signals in the shared history.

5. **Evaluation cost**: ~$40 per full-domain trial with GPT-4.1 — comparable cost profile to our experiments.
