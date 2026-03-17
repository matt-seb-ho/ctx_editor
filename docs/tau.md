# τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains

**Paper**: [arXiv 2406.12045](https://arxiv.org/abs/2406.12045) (June 2024)
**Authors**: Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan (Princeton / Sierra Research)
**Code**: [github.com/sierra-research/tau-bench](https://github.com/sierra-research/tau-bench)

## Motivation

Existing LLM agent benchmarks focus on tool use or instruction following in isolation, but don't test the realistic scenario where an agent must simultaneously:
1. Interact with a human user through multi-turn conversation
2. Use domain-specific API tools to take actions
3. Follow complex policy guidelines / rules

τ-bench fills this gap by emulating dynamic conversations between a simulated user and a language agent equipped with domain-specific APIs and policy documents.

## Benchmark Design

### Domains

Two real-world customer service domains:

- **Retail** — E-commerce order management and customer service (e.g., modifying orders, processing returns, updating account info). Higher success rates; tasks are more straightforward.
- **Airline** — Flight booking, reservation changes, and travel customer service. Lower success rates; tasks involve more complex policy constraints.

### Core Components

Each domain consists of:

1. **Database**: A structured backend (e.g., user accounts, orders, flights) that the agent reads/modifies via API calls. The database state is the ground truth for evaluation.
2. **Tools/APIs**: Domain-specific function-calling endpoints (e.g., look up order, cancel booking, update customer info). Agents interact via structured tool calls.
3. **Policy Documents**: Detailed rules the agent must follow (e.g., refund eligibility windows, fare class restrictions, required confirmations before actions). These create the complexity — the agent must interpret and apply rules correctly.
4. **Tasks**: Each task specifies a user persona/scenario with a goal. The annotated "goal state" defines what the database should look like after successful completion.

### User Simulation

Users are simulated by LLMs (e.g., GPT-4o) given a persona description and task instructions. Four simulation strategies are available:

- **LLM** (default) — Standard LLM-based user responses
- **ReAct** — User simulator uses explicit "Thought" reasoning steps
- **Verify** — LLM responses are validated by a verification step
- **Reflection** — Failed responses trigger reflective re-generation

### Evaluation: Database State Comparison

Rather than evaluating conversation quality or surface-level answers, τ-bench compares the **final database state** against an **annotated goal state**. This is a faithful evaluation — did the agent actually accomplish the task (modify the right records, apply the right policies) or not?

## Key Metric: pass^k

The central contribution is the **pass^k** metric, measuring agent reliability across multiple independent trials of the same task.

- **pass^1** = success rate on a single attempt (standard metric)
- **pass^k** = probability of succeeding on **all k independent attempts** of the same task

This captures **consistency/reliability**, not just peak capability. An agent that succeeds 50% of the time on one try has a pass^8 of only ~0.4% — revealing how unreliable it actually is for deployment.

The key insight: **single-pass metrics dramatically overstate real-world readiness**. An agent needs to be reliable, not just occasionally correct.

## Results

### Key Finding: State-of-the-art agents are unreliable

- **GPT-4o** (best function-calling agent at time of publication): **<50% pass^1**, **<25% pass^8** on retail
- Performance drops dramatically from pass^1 → pass^k, revealing high variance across attempts
- Agents frequently make different errors on different runs of the same task

### Leaderboard (selected, from repo):

| Model | Retail pass^1 | Retail pass^4 | Airline pass^1 | Airline pass^4 |
|-------|--------------|--------------|----------------|----------------|
| Claude 3.5 Sonnet (Oct 2024) | 0.692 | 0.462 | 0.460 | 0.225 |
| GPT-4o | ~0.50 | — | ~0.35 | — |

### Agent Strategies Tested

- **Tool-calling** (function calling) — primary evaluation mode
- **ReAct** — reasoning + acting prompting
- **Act** — action-only prompting

## Relevance to Our Work

τ-bench shares key themes with the Lost in Conversation framework:

1. **Multi-turn degradation**: Agents make errors that compound across conversation turns — similar to LiC's finding that LLMs overcommit to early incorrect assumptions.
2. **Policy adherence failures**: Agents misinterpret or forget rules mid-conversation — analogous to the "hard attention" problem where early reasoning anchors later behavior.
3. **Reliability gap**: The pass^k metric quantifies what we observe qualitatively — agents are inconsistent across attempts, suggesting the errors are not deterministic but arise from stochastic reasoning failures.
4. **Database-grounded evaluation**: Like our system agent verification, τ-bench uses objective state comparison rather than LLM-as-judge for evaluation.

The key difference: τ-bench tests single-attempt reliability (same task, fresh conversation each time), while LiC tests within-conversation self-correction (same conversation, accumulating context). Context editing addresses the LiC failure mode; τ-bench's reliability problem may require different interventions (e.g., better tool-use training, policy grounding).
