# Task Spec — NeurIPS Rebuttal Autoresearch Session

**Session start:** 2026-07-29 ~09:30 PT. Operator (Matthew) asleep, then on other work. Zero-interaction protocol (Deli_AutoResearch): resolve ambiguity autonomously, log the reasoning, never end on a question.

## Goal
Produce new experimental results that materially improve Sub. 27902's acceptance odds during the NeurIPS rebuttal/discussion window. Source of truth for what to run: `neurips_review/experiment_todos.md`.

## Compute policy
- **Primary model:** `gpt-5.4-mini_2026-03-17` on TRAPI `redmond/interactive` (free, consistent throughput). Config: `load_balancer=trapi model=gpt5_4_mini_trapi`.
- **Escalation model:** `gpt-5.2` on `dl-openai-1` — sparingly, only where a stronger model is load-bearing (e.g. Tier-C oracle judge that must be a *different family/strength* from the analyzer).
- TRAPI `max_concurrent: 20` is shared across all concurrently running experiments. Keep the aggregate under that.

## Milestones (priority order from experiment_todos.md §"Suggested order if time is short")
| ID | Item | Why it matters | Status |
|----|------|----------------|--------|
| T8 | CollabLLM N=3 w/ competent user sim | We already assert 100%/20% in `replies/v4/` off **N=1**. Exposed claim. | pending |
| T9 | Analyzer-model sensitivity | Vg97 Q3's unanswered half. Cheap, directly requested. | pending |
| T2A | Tier-A constructed pollution detection | Detector story, no judge dependence. | pending |
| T2c | Auditing vs. re-solving | 5YHP's mechanism challenge; defends the core claim. | pending |
| T1 | Condensation/summarisation baseline | Vg97 W1/Q1 + AC "limited baselines". | pending |
| T11-13 | WildChat judge checks; memory order/split analysis | Promised in v4 replies. Cheap. | pending |
| T6 | Multi-seed tau2 | Largest statistical hole, but expensive. | pending |
| T2B | Counterfactual span ablation | Gold-standard causal pollution label. | pending |

## Success criteria
1. Every claim currently asserted in `replies/v4/` off N=1 is either re-run at N>=3 or explicitly softened.
2. At least one condensation baseline reported (result direction does not matter — a negative result is reportable).
3. At least one non-circular pollution-detection measurement (Tier A minimum).
4. All numbers land in a table a reviewer could paste-check, with the artifact path recorded.

## Hard rules
- **Never** edit `writing/overleaf_repo/` without an explicit ask; it is a separate repo.
- Report failures faithfully in the worklog. A negative result is a result.
- Every subagent maintains its own worklog under `neurips_review/autoresearch/tasks/<ID>/worklog.md`; the central log links to it.
