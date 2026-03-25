# Huang et al. Evaluation: Consolidated Results

## Setup

**Evaluation.** Reproduces Huang et al. "Do LLMs Benefit from Their Own Words?" on 30 WildChat conversations (179 turns). Compares four context management strategies against FC (full context) and AO (assistant-omitted) baselines using Huang's pairwise LLM judge on Quality and On-Topic dimensions.

**Data.** 30 conversations from allenai/WildChat-1M, filtered per Huang: English, technical (math/coding keywords), 5-10 rounds, non-toxic. seed=42, max_scan=10000.

**Models.** gpt-5-mini for all roles (respondent, judge, classifier, analyzer).

**Conditions.**

| Label | Strategy | Analyzer | Gating | Post-reset context | LLM calls per turn |
|-------|----------|----------|--------|--------------------|--------------------|
| FC | Full context (S0) | -- | -- | -- | 1 (generation) |
| AO | Assistant-omitted | -- | -- | -- | 1 (generation) |
| S1.5 | Programmatic reset | v8 (hard attention) | Always reset | Programmatic template from analysis | 3 (Q1 + Q2 + generation) |
| S2 | Gated context edit | v11 (mid-task reflection) | Only when issues found | Programmatic template from analysis | 3 (Q1 + Q2 + generation) |
| S3 | LLM compaction | v8 (hard attention) | Always reset | LLM-written compaction | 4 (Q1 + Q2 + compaction + generation) |

## Phase 1: FC vs AO (Reproducing Huang)

**Turn type distribution (n=179):**

| Type | Count | % |
|------|-------|---|
| no_feedback | 69 | 38.5% |
| new_ask | 67 | 37.4% |
| feedback | 43 | 24.0% |

Huang reported 33.1% no_feedback; our 38.5% is in the same range.

**FC vs AO by turn type (quality):**

| Turn Type | n | FC wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 67 | 34.3% | **56.7%** | 9.0% |
| feedback | 43 | 37.2% | **60.5%** | 2.3% |
| no_feedback | 69 | **53.6%** | 42.0% | 4.3% |
| Overall | 179 | 42.5% | 52.0% | 5.6% |

**Key finding:** Reproduces Huang's result. AO wins overall (context pollution removal helps), but FC wins on no_feedback turns (where user messages depend on prior assistant outputs). 76 turns (42.5%) identified as AO failures (FC > AO on quality).

## Phase 2: Our Methods vs Baselines

### AO Failure Subset (turns where FC > AO on quality)

These are the turns Huang identifies as problematic for AO -- where blanket assistant omission actively hurts.

**Quality win rates:**

| Strategy | n | vs AO | vs FC | Edit rate |
|----------|---|-------|-------|-----------|
| S1.5 (v8, always reset) | 76 | **90.8%** | **86.8%** | 100% |
| S2 (v11, gated) | 75 | **93.3%** | 82.7% | 68.0% |
| S3 (v8, LLM compaction) | 75 | 85.3% | 84.0% | 90.7% |

**On-topic win rates:**

| Strategy | n | vs AO | vs FC |
|----------|---|-------|-------|
| S1.5 | 76 | 73.7% | 71.1% |
| S2 | 75 | 78.7% | 65.3% |
| S3 | 75 | 73.3% | 76.0% |

### All Turns (Unconditional -- no selection bias)

**Quality win rates:**

| Strategy | n | vs AO | vs FC | Edit rate |
|----------|---|-------|-------|-----------|
| S1.5 (v8, always reset) | 176 | 83.0% | 83.5% | 100% |
| S2 (v11, gated) | 173 | **86.1%** | **83.8%** | 72.3% |
| S3 (v8, LLM compaction) | 178 | 82.6% | 80.3% | 84.3% |

**On-topic win rates:**

| Strategy | n | vs AO | vs FC |
|----------|---|-------|-------|
| S1.5 | 176 | 68.8% | 68.2% |
| S2 | 173 | 74.6% | 71.1% |
| S3 | 178 | 68.5% | 67.4% |

**By turn type (quality vs AO, all turns):**

| Turn Type | n | S2 wins | S3 wins |
|-----------|---|---------|---------|
| new_ask | ~65 | 87.5% | 84.8% |
| feedback | ~43 | 85.7% | 81.4% |
| no_feedback | ~68 | 85.1% | 81.2% |

**S2 edit rate by turn type:**

| Turn Type | Edit rate |
|-----------|-----------|
| new_ask | 78.1% |
| feedback | 78.6% |
| no_feedback | 62.7% |
| Overall | 72.3% |

## Key Takeaways

**1. All our methods dramatically outperform both FC and AO.** S2, S3, and S1.5 all achieve 82-93% quality win rates against AO and 80-87% against FC. The core hypothesis holds: surgical context editing that preserves useful assistant history while removing harmful content outperforms both keeping everything (FC) and discarding everything (AO).

**2. S2's gating is valuable.** S2 achieves the best overall numbers (86.1% vs AO) while editing only 72.3% of turns. On the ~28% of turns where v11 finds no issues, S2 correctly falls back to FC. This is especially relevant for the no_feedback turns (62.7% edit rate), where the conversation is more often on track and a reset would be counterproductive.

**3. AO's failure mode is real and targetable.** On the 76 AO failure turns, our methods achieve 85-93% quality win rates against AO. These are exactly the cases Huang et al. identify as problematic (stateful turns, user depending on prior assistant output) and where they call for "finer-grained context filtering."

**4. Format bias caveat.** Win rates are uniformly high across turn types, which suggests the compacted format (structured task spec + progress headers) may give our methods a presentation advantage the judge rewards. The relative comparisons between our methods are less affected since they share similar output formats.

## Output Locations

| Run | Output |
|-----|--------|
| Phase 1: FC vs AO (30 conv) | `outputs/huang_eval/phase1/2026-03-24/02-22-57/` |
| S3+S1.5 on AO failures (76 turns) | `outputs/huang_eval/phase2/2026-03-24/02-54-36/` |
| S3 on all turns (178 turns) | `outputs/huang_eval/phase2_full/2026-03-25/01-39-43/` |
| S2+S3 on AO failures (75 turns) | `outputs/huang_eval/phase2_s2_failures/2026-03-25/04-53-30/` |
| S2+S3 on all turns (173 turns) | `outputs/huang_eval/phase2_s2_full/2026-03-25/06-13-04/` |
| S1.5+S3 on all turns (176 turns) | `outputs/huang_eval/phase2_s15_full/2026-03-25/09-05-26/` |

## Prompt Versions

| Prompt | File | Used by |
|--------|------|---------|
| Task spec (v8) | `strategies/prompts/analyzer_v8_task_spec.txt` | S2, S3, S1.5 |
| Compare (v8) | `strategies/prompts/analyzer_v8_compare.txt` | S3, S1.5 |
| Compare (v11) | `strategies/prompts/analyzer_v11_compare.txt` | S2 |
| Compaction (S3) | `strategies/prompts/context_compaction.txt` | S3 only |
| AO system message | `huang_eval/prompts/ao_system_message.txt` | AO |
| Turn classifier | `huang_eval/prompts/turn_classifier.txt` | All (classification) |
| Pairwise judge | `huang_eval/prompts/pairwise_judge.txt` | All (evaluation) |

## Run Configs

All Phase 2 runs share:
```
--respondent-model gpt-5-mini --judge-model gpt-5-mini --analyzer-model gpt-5-mini
--max-concurrent 5 --seed 42
```

Strategy-specific flags: `--run-s2`, `--run-s15`. S3 always runs (default).
Full-turn runs use `--turns-file outputs/huang_eval/phase1/2026-03-24/02-22-57/all_turns.json`.
Failure-subset runs use the default `ao_failure_turns.json`.
