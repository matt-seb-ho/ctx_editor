# Cluster 5 — Multi-Turn Evaluation Landscape and Scooping Check

**Research question**: Has anyone already built a benchmark that treats inter-turn
dependency/entanglement OR statefulness as a controlled, dial-able variable?

**Scope**: tau-bench / tau2-bench, LiC, MT-Bench-101, MINT, MT-Eval, StructFlowBench,
ERGO, Huang et al., ToolSandbox, BFCL V3, AgentBoard, MARS-Bench, MultiChallenge.

---

## Benchmark Table

| Name | Venue / Year | What it tests | Models inter-turn dependency? | Models environment state? | Is it a KNOB (controllable)? | Verified URL |
|---|---|---|---|---|---|---|
| **tau-bench** | arXiv / 2024 | Tool-use agents on retail & airline tasks; eval = final DB state vs goal | Implicit (tasks require multi-step tracking) | Yes — database state evaluated at conversation end | No — state is fixed per task design | https://arxiv.org/abs/2406.12045 |
| **tau2-bench** | arXiv / Jun 2025 | Dual-control conversational agents (Dec-POMDP); compositional task generator | Coordination across turns required | Yes — shared world state, both agent and user use tools | Partial — "controlled complexity" via task generator, but not specifically an entanglement dial | https://arxiv.org/abs/2506.07982 |
| **LiC (Lost in Conversation)** | ICLR 2026 | Performance drop when single-turn instructions are sharded across N turns | Yes — sharding count is a variable | No | Partial — number of shards is controllable, but shards are self-contained (low user→assistant coupling by design) | https://arxiv.org/abs/2505.06120 |
| **MT-Bench-101** | ACL 2024 | Fine-grained multi-turn dialogues across 13 task types, 1388 sessions | Fixed taxonomy of turn types | No | No — taxonomy is categorical, not a dial | https://arxiv.org/abs/2402.14762 |
| **MINT** | ICLR 2024 | Multi-turn LLM interaction with tools and NL feedback; k_max controls max turns | Yes — models must use prior turns' information | Implicit (tool state between calls) | Partial — k_max controls max turns, not dependency depth | https://arxiv.org/abs/2309.10691 |
| **MT-Eval** | EMNLP 2024 | 4 interaction categories: recollection, expansion, refinement, follow-up | Yes — categories implicitly vary dependency level | No | No — fixed categories, not a continuous dial; high recollection → low expansion dependency ordering exists but is not parametric | https://arxiv.org/abs/2401.16745 |
| **StructFlowBench** | ACL Findings 2025 | Multi-turn instruction following with 6 structural inter-turn relationship types | Yes — 6 relationship types as "generation parameters for customized dialogue flows" | No | Partial — relationship types are controllable generation parameters, but focus is instruction-following compliance, not context management degradation | https://arxiv.org/abs/2502.14494 |
| **ToolSandbox** | arXiv / 2024 | Stateful tool use with "State Dependency" as a challenge type | Yes — tasks require tracking implicit state | Yes — built-in state dependencies between tools | No — state is a fixed challenge type, not a dial | https://arxiv.org/abs/2408.04682 |
| **BFCL V3** | arXiv / Sep 2024 | Multi-turn and multi-step function calling; state verified post-execution | Implicit in multi-step chaining | Yes — API/system state checked after execution | No — no explicit entanglement or statefulness dial | https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html |
| **AgentBoard** | NeurIPS 2024 | Analytical evaluation of multi-turn LLM agents; progress rate metric | Yes — partially observable environments require tracking history | Implicit (partially observable tasks) | No — fixed task set, no dependency dial | https://arxiv.org/abs/2401.13178 |
| **MARS-Bench** | EMNLP Findings 2025 | Cross-turn reasoning on sports play-by-play commentary | Yes — explicitly targets cross-turn dependency | No | No — cross-turn dependency is a targeted dimension but not a parametric dial | https://aclanthology.org/2025.findings-emnlp.314/ |
| **MultiChallenge** | ACL Findings 2025 | Realistic multi-turn failures: instruction retention, context allocation | Yes — 4 challenge categories require cross-turn instruction tracking | No | No — fixed categories, no controllable dial | https://arxiv.org/abs/2501.17399 |
| **ERGO** | ACL/UncertainNLP 2025 | Context management method: entropy-guided context reset (NOT a benchmark) | N/A (method paper) | N/A | N/A | https://arxiv.org/abs/2510.14077 |
| **Huang et al. 2026** | arXiv 2026 | Context management comparison: full context vs assistant-omit vs summarize | N/A (method/analysis paper) | N/A | N/A | https://arxiv.org/abs/2602.24287 |

---

## SCOOPING ANALYSIS

### Our Contribution Restated

We propose a multi-turn evaluation framework where two variables are independently controlled
as dials on a single benchmark:

- **ENTANGLEMENT** — the degree to which a user turn explicitly references / builds on the
  assistant's prior output (a faithfulness-gated construction ensures reference quality)
- **STATEFULNESS** — the degree to which persistent environment state must be tracked
  across turns

We then measure how four context management strategies (accumulate-all, assistant-omit,
summarize, decontextualize-and-edit) degrade as these knobs increase.

---

### Closest Prior Works

#### 1. StructFlowBench (ACL Findings 2025) — CLOSEST to entanglement knob

**What it does**: Defines 6 inter-turn relationship types (Follow-up, Refinement, Recall,
Summary, Expansion, Unrelatedness) and uses them as "generation parameters for creating
customized dialogue flows." This is the only prior benchmark that explicitly treats
inter-turn relationship type as a controllable generation parameter.

**Exactly how we differ**:
- StructFlowBench targets *instruction-following compliance* — does the model obey
  instructions that span turns? It does not study how *context management strategies*
  (accumulate-all, assistant-omit, summarize, edit) perform as structural dependency varies.
- Its "dial" is categorical (which of 6 relationship types), not a continuous entanglement
  score that can be graded from 0 to 1.
- It has no statefulness axis.
- It does not use a faithfulness-gated construction (checking that synthetic references
  are actually answerable from prior assistant content).

#### 2. LiC / Lost in Conversation (ICLR 2026) — CLOSEST to a number-of-turns knob

**What it does**: Shards a single-turn instruction into N pieces revealed across turns.
The number of shards is a controllable variable; as N increases, performance degrades.
This is the benchmark our project builds on.

**Exactly how we differ**:
- LiC shards are designed to be *self-contained* user specifications — each shard contains
  no reference to prior assistant output. This means LiC has near-zero entanglement by
  construction. The knob is about *underspecification spread*, not user→assistant coupling.
- LiC has no statefulness axis.
- The "trivial exploit" (Concat / assistant-omit) fully recovers single-turn performance,
  making LiC unsuitable for comparing context management methods that preserve vs discard
  assistant content. This is a known limitation (see project_motivation.md §2.3).
- Our construction adds entanglement (user turns that explicitly reference prior assistant
  outputs) and statefulness (persistent environment state), making the benchmark harder
  to exploit with simple assistant-omission.

#### 3. MT-Eval (EMNLP 2024) — CLOSEST to a dependency taxonomy with multiple levels

**What it does**: Four fixed interaction types that correspond to different dependency
levels: recollection (highest dependency) > refinement > follow-up > expansion (lowest
dependency). The paper explicitly studies performance degradation by interaction type.

**Exactly how we differ**:
- MT-Eval's 4 types are a fixed taxonomy, not a single parametric dial you can tune
  continuously (e.g., "set entanglement to 0.7").
- The dependency in MT-Eval is primarily *user→prior-user* (recall what was said earlier),
  not specifically *user→prior-assistant-output* coupling.
- MT-Eval does not study how context management strategies (accumulate-all, assistant-omit,
  summarize, edit) compare as dependency type changes.
- No statefulness axis.

---

### Verdict

**We are clear.** No existing benchmark (a) exposes entanglement as a continuously
controllable knob with a faithfulness-gated construction, (b) pairs it with a statefulness
axis, and (c) uses both to measure how context management strategies degrade. StructFlowBench
is the closest prior work and should be cited and distinguished precisely. LiC is our
base platform and should be acknowledged as the benchmark we extend. MT-Eval's interaction
taxonomy provides useful framing for our entanglement levels.

**Key novelty claim (exact wording suggestion)**: "Unlike prior work that categorizes
interaction types post-hoc (MT-Eval, StructFlowBench) or controls only the spread of
underspecification across turns (LiC), we expose entanglement and statefulness as
independently dial-able construction parameters, and use them to measure how context
management methods scale as both dimensions increase."

---

## References (Verified)

All URLs confirmed via web search during this survey session.

- tau-bench: https://arxiv.org/abs/2406.12045
- tau2-bench: https://arxiv.org/abs/2506.07982
- LiC: https://arxiv.org/abs/2505.06120
- MT-Bench-101: https://arxiv.org/abs/2402.14762
- MINT: https://arxiv.org/abs/2309.10691
- MT-Eval: https://arxiv.org/abs/2401.16745
- StructFlowBench: https://arxiv.org/abs/2502.14494
- ToolSandbox: https://arxiv.org/abs/2408.04682
- BFCL V3: https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html
- AgentBoard: https://arxiv.org/abs/2401.13178
- MARS-Bench: https://aclanthology.org/2025.findings-emnlp.314/
- MultiChallenge: https://arxiv.org/abs/2501.17399
- ERGO: https://arxiv.org/abs/2510.14077
- Huang et al. 2026: https://arxiv.org/abs/2602.24287
