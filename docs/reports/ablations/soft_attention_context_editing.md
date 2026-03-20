# Ablation: Can Context Editing Rescue Soft-Attention Analysis?

**Date**: 2026-03-17
**Branch**: `newleaf2`
**Commit**: `6d8930b`
**Depends on**: [Hard Attention ablation](single_query_hard_attention.md), [V8 batch results](../v8_batch_results.md)

## Motivation

The hard attention ablation showed that soft-attention analysis (where the analyzer sees assistant messages when building the task spec) performs at or below baseline in the S1 (append) setting. But S1 appends analysis to the *full* conversation — the assistant still sees all the bad context that led it astray.

This raises a question: **is the soft-attention analysis itself useless, or is it being drowned out by the polluted context it's appended to?**

If context editing (removing the bad conversation history) can rescue soft-attention analysis, that would be evidence that context editing is a valuable operation for handling context pollution — even when the analysis is imperfect. This matters because hard attention (hiding assistant messages from the analyzer) is a LiC-specific trick: user messages alone fully specify the task. In realistic multi-turn scenarios, the task spec is NOT recoverable from user messages alone, so we need analysis approaches that work with the full conversation.

## Design

We test two context-editing strategies on top of the two soft-attention analysis variants from the previous ablation:

| Strategy | Description | LLM calls |
|----------|-------------|-----------|
| **S1.5** (programmatic) | Reset conversation; template analysis fields (task spec + aligned) into compacted context; issues injected as `<context_edit_notes>` in system message | 0 extra |
| **S3** (LLM compaction) | Reset conversation; an LLM reads the full conversation + analysis output and writes optimized compacted context (controls task spec presentation) | 1 extra |

S3's rationale: the soft-attention analysis may produce a contaminated task spec. An LLM compaction step has access to the raw conversation as material and the analysis as *guidance*, so it can potentially produce a cleaner presentation than just templating a contaminated spec.

### Full matrix: 3 tasks × 2 analysis sources × 2 context prep = 12 runs

**What's controlled across all runs:**
- Same model (gpt-5-mini) for assistant and S3 compaction
- Same v2 evaluators, same dev subsets, same replay traces (depth=1)
- Same false negative filtering
- All runs use pre-computed analysis from the hard attention ablation's S1-single and S1-soft traces

## Results

### Complete Table

| Task | S0 | S1-single (1q) | S1-soft (2q) | S1.5-single | S1.5-soft | S3-single | S3-soft |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Math** | 12/20 (60%) | 11/20 (55%) | 8/20 (40%) | 11/20 (55%) | 8/18 (44%) | 11/20 (55%) | 10/20 (50%) |
| **Code** | 3/19 (16%) | 4/19 (21%) | 2/19 (11%) | 5/19 (26%) | 2/17 (12%) | 4/18 (22%) | 2/18 (11%) |
| **Database** | 1/25 (4%) | 1/25 (4%) | 2/25 (8%) | 1/24 (4%) | 2/25 (8%) | 3/25 (12%) | 2/25 (8%) |

S0 and S1 columns are from the [hard attention ablation](single_query_hard_attention.md) for reference.

Note: Several runs had timeout errors reducing denominators (S1.5-soft math: 18, S1.5-soft code: 17, S1.5-single database: 24, S3-single code: 18, S3-soft code: 18). Raw counts are reported; percentages reflect actual denominators.

### Compared to Hard-Attention Context Editing (V8 batch)

For contrast, here is what context editing achieves when the analysis is *clean* (hard attention):

| Task | S0 | S1 (hard) | S1.5 (hard) | S2 (hard) |
|------|:---:|:---:|:---:|:---:|
| **Math** | 12/20 (60%) | 16/20 (80%) | 16/20 (80%) | 15/20 (75%) |
| **Code** | 3/19 (16%) | 10/18 (56%) | 11/16† (69%) | 13/18 (72%) |
| **Database** | 1/25 (4%) | 8/25 (32%) | 10/25 (40%) | 11/25 (44%) |

†Denominator reduced by timeout errors.

With clean analysis, S1.5 and S2 provide +8–16pp over S1 on code and database. With contaminated analysis, context editing provides 0pp.

## Key Findings

### 1. Context editing cannot rescue contaminated analysis

Neither S1.5 nor S3 meaningfully improves over the S1 append-only results on any task. The soft-attention analysis — whether from 1 query or 2 — is contaminated by the assistant's incorrect reasoning, and no amount of context restructuring fixes this.

| Setting | Math Δ vs S1 | Code Δ vs S1 | Database Δ vs S1 |
|---------|:---:|:---:|:---:|
| S1.5-single vs S1-single | +0pp | +5pp | +0pp |
| S1.5-soft vs S1-soft | +4pp | +1pp | +0pp |
| S3-single vs S1-single | +0pp | +1pp | +8pp |
| S3-soft vs S1-soft | +10pp | +0pp | +0pp |

Deltas are small and inconsistent across tasks — no systematic improvement.

### 2. S3's LLM rewrite doesn't outperform S1.5's templating

S3 was designed to give the compaction LLM a chance to clean up a contaminated task spec by re-deriving it from the raw conversation. In practice, S3 ≈ S1.5 across the board. The compaction LLM is subject to the same contamination problem — it reads the same polluted conversation and produces similarly contaminated output.

### 3. The bottleneck is analysis quality, not delivery mechanism

Combining all evidence:

| Analysis quality | Append (S1) | Reset (S1.5) | Edit (S2/S3) |
|-----------------|:---:|:---:|:---:|
| **Clean** (hard attention) | Strong gains | Additional gains | Best results |
| **Contaminated** (soft attention) | At/below baseline | At/below baseline | At/below baseline |

Context editing is a **force multiplier** on analysis quality. With clean analysis, it provides meaningful lift. With contaminated analysis, there is nothing to multiply.

### 4. Soft-attention contamination is the fundamental barrier

The consistent pattern across all experiments is that when the analyzer sees assistant messages during task spec construction, the resulting analysis reflects the assistant's errors rather than correcting them. This contamination is:

- **Not rescued by context removal** (S1.5) — removing the conversation doesn't help when the replacement context is also contaminated
- **Not rescued by LLM rewriting** (S3) — the rewriting LLM is subject to the same contamination
- **Amplified by two-query chaining** (S1-soft worse than S1-single) — a contaminated spec passed to Query 2 as authoritative ground truth produces compounding errors

## Implications

1. **Context editing is valuable, but conditional on analysis quality.** The hard-attention results (S1.5/S2 beating S1 by 8-16pp on code/database) confirm that removing polluted context helps. But the benefit requires accurate identification of what's right and wrong.

2. **The hard attention trick is load-bearing and not easily replaceable.** In LiC, we can hide assistant messages because user messages alone fully specify the task. In realistic scenarios where the task spec depends on assistant-generated content (e.g., iterative refinement, multi-step reasoning), a different approach to decontamination is needed.

3. **Future directions for soft-attention analysis:**
   - A more capable analyzer model that can resist assistant anchoring
   - Explicit chain-of-thought that separates "what did the user specify" from "what did the assistant do"
   - Adversarial prompting that instructs the analyzer to distrust the assistant's claims
   - Hybrid approaches: soft attention for `aligned`/`issues` (which need assistant context) but hard attention for task spec

## Run Details

**Model**: `gpt-5-mini` (assistant, analyzer, S3 compaction), `gpt-4o-mini` (user/system agents in original S1 traces)
**Task configs**: `dev_math`, `dev_code`, `dev_database` (all v2 evaluators)
**Replay**: depth=1, false negatives skipped
**S3 prompt**: `src/ctx_editor/strategies/prompts/context_compaction.txt`

### Source Trace Directories (S1 analysis)

| Source | Dir |
|--------|-----|
| S1-single math | `outputs/2026-03-17/03-02-33` |
| S1-single code | `outputs/2026-03-17/03-02-34` |
| S1-single database | `outputs/2026-03-17/03-02-35` |
| S1-soft math | `outputs/2026-03-17/04-12-12` |
| S1-soft code | `outputs/2026-03-17/04-12-14` |
| S1-soft database | `outputs/2026-03-17/04-12-14` |

### Output Directories

| Run | Result | Dir |
|-----|:------:|-----|
| S1.5-single math | 11/20 (55%) | `outputs/2026-03-17/10-54-13` |
| S1.5-single code | 5/19 (26%) | `outputs/2026-03-17/10-54-57` |
| S1.5-single database | 1/24 (4%) | `outputs/2026-03-17/10-56-39` |
| S1.5-soft math | 8/18 (44%) | `outputs/2026-03-17/11-01-36` |
| S1.5-soft code | 2/17 (12%) | `outputs/2026-03-17/11-06-39` |
| S1.5-soft database | 2/25 (8%) | `outputs/2026-03-17/11-12-11` |
| S3-single math | 11/20 (55%) | `outputs/2026-03-17/11-12-57` |
| S3-single code | 4/18 (22%) | `outputs/2026-03-17/11-15-05` |
| S3-single database | 3/25 (12%) | `outputs/2026-03-17/11-21-29` |
| S3-soft math | 10/20 (50%) | `outputs/2026-03-17/11-22-54` |
| S3-soft code | 2/18 (11%) | `outputs/2026-03-17/11-26-25` |
| S3-soft database | 2/25 (8%) | `outputs/2026-03-17/11-32-34` |

### Files Added/Modified

- Prompt: `src/ctx_editor/strategies/prompts/context_compaction.txt`
- Script: `scripts/run_s15_experiment.py` (added `--mode s3`)
- Run script: `scripts/run_soft_attention_s15_s3.sh`
