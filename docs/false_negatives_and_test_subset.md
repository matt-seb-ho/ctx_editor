# False Negative Identification & Test Subset Construction

## Motivation

The LiC simulation setup uses a **user simulator model** to reveal problem shards across turns. The user sim is instructed to rephrase shards for conversational naturalness, but this rephrasing can **distort** the original problem — omitting constraints, changing semantics, or repeating earlier info instead of conveying new shards. When evaluation marks the assistant's answer as incorrect, the failure may be attributable to the user sim rather than the assistant.

This matters because our follow-up work tests context editing on problems where the **baseline exhibits multi-turn failure**. If we include user-sim-induced failures in that set, we'd be testing our method on problems where the assistant never had a fair chance — polluting our evaluation signal.

Additionally, user-sim-induced errors are **non-deterministic** (temperature=1 sampling), so the same problem can succeed or fail across runs depending on user sim behavior. We mitigate this with 3 variance runs per task (documented in `misc/combined_variance_runs.md`).

## Pipeline Overview

```
1. identify_false_negatives.py   →   prelim_fn.json (per run)
2. build_test_subset.py          →   data/test_subset.json (aggregated)
```

### Step 1: False Negative Identification (`identify_false_negatives.py`)

For each **incorrect** sample in a run, two checks determine if the failure is the user sim's fault (false negative) or the assistant's fault (true negative):

**Check 1 (programmatic): Answer extraction**
- Did the assistant produce an extractable answer?
- If not, the last turn is classified (answer_attempt, clarification, interrogation, etc.)
- No extracted answer → flagged as false negative (we can't evaluate what wasn't produced)

**Check 2 (LLM): User sim sufficiency**
- Compares the **union of all user simulator messages** from the actual conversation trace against the original single-turn question + ground truth answer
- Also includes the **system message** (critical for database schemas and action function signatures)
- An LLM judge determines if any critical information was absent or materially distorted
- Designed to NOT flag: late arrival of info, rewordings, or info split across turns (all expected by design)

Samples flagged by either check are classified as **preliminary false negatives** (user sim's fault). All others are **true negatives** (assistant's fault).

#### Key implementation details

- Metadata (`full_spec_q`, `ground_truth_a`) is loaded from data files (`data/full_{task}_subset.json`) and joined to traces by `task_id`/`sample_id`, since trace files don't store this metadata.
- The sufficiency prompt explicitly tells the LLM judge that sharded delivery is expected — only truly missing or semantically changed information should be flagged.
- System messages are included because they contain task-critical context (e.g., database schemas for SQL tasks, available function signatures for actions).

#### Usage

```bash
# Single run
python -m ctx_editor.identify_false_negatives outputs/2026-03-06/04-56-49 --task math

# With options
python -m ctx_editor.identify_false_negatives outputs/2026-03-06/04-56-49 \
    --task math --model gpt-4o-mini --concurrency 10 -v
```

Output: `{run_dir}/prelim_fn.json`

### Step 2: Test Subset Construction (`build_test_subset.py`)

Aggregates `prelim_fn.json` results across all 3 variance runs per task to identify problems with **consistent** assistant failure:

- For each problem, counts how many runs produced a **true negative** (assistant at fault)
- Applies a threshold (default: 2 out of 3 = majority) to select problems for the test subset
- Also loads correctness for all samples (not just incorrect ones) to track always-correct problems

#### Usage

```bash
# Default threshold=2 (majority)
python -m ctx_editor.build_test_subset

# Lower threshold
python -m ctx_editor.build_test_subset --threshold 1 --output data/test_subset_t1.json
```

Output: `data/test_subset.json` (compact) and `data/test_subset_detailed.json` (per-problem breakdown)

## Results (March 2026)

### False negative rates (per run, typical)

| Task     | Incorrect | False Neg | Rate  | Main cause |
|----------|-----------|-----------|-------|------------|
| math     | 12–19     | 1–2       | ~10%  | no_answer  |
| code     | 25–29     | 0–2       | ~5%   | distortion |
| database | 62–69     | 2–4       | ~3%   | distortion |
| actions  | 48–51     | 1–6       | ~8%   | distortion |

### Test subset (threshold=2)

| Task     | Total problems | Always correct | Test subset | % |
|----------|---------------|----------------|-------------|---|
| math     | 103           | 70             | 9           | 8.7% |
| code     | 100           | 57             | 20          | 20% |
| database | 107           | 23             | 63          | 58.9% |
| actions  | 105           | 43             | 47          | 44.8% |
| **Total**| **415**       | **193**        | **139**     | **33.5%** |

With threshold=1 (at least one run): 212 problems total.

Math's small subset (9) reflects the high baseline accuracy (82–88%). Database and actions have the most failures, consistent with being harder tasks.

### True negative distribution (# runs with true neg, per problem)

This shows how consistently problems fail across runs:

| Runs | math | code | database | actions |
|------|------|------|----------|---------|
| 0    | 72   | 58   | 26       | 47      |
| 1    | 22   | 22   | 18       | 11      |
| 2    | 7    | 4    | 15       | 17      |
| 3    | 2    | 16   | 48       | 30      |

Database and actions have many problems that fail in all 3 runs (48 and 30 respectively), indicating stable failure modes rather than variance noise.

## Validation

Spot-checked 12 conversations (3 per task), covering both true negatives (pass) and false negatives (flagged). Agreed with 10/12 classifications. The 2 disagreements were both **under-flagging** (user sim distortions classified as true negatives), meaning the test subset is conservative — it may include a few user-sim-caused failures but won't miss real assistant failures.

Examples of correctly identified distortions:
- **HumanEval/36**: User sim never mentioned "divisible by 11 or 13" — completely changed the problem
- **BFCL/parallel_109**: User sim kept repeating "nucleus proteins" despite mitochondria/cytoplasm shards being revealed
- **spider-val-699**: User sim never requested the `created` column — shard was distorted into unrelated content

## Limitations

- The LLM judge (gpt-4o-mini) may miss subtle distortions where information is technically present but stated ambiguously enough to mislead. This makes the approach slightly conservative (under-flags false negatives).
- Check 1 (no extracted answer) conflates user-sim confusion with assistant over-caution. Some "no answer" cases may be the assistant's fault (refusing to commit despite having enough info).
- The 3-run variance mitigation helps but doesn't fully eliminate noise — a problem could have user-sim distortion in 1 run and genuine assistant failure in 2 runs, landing in the test subset correctly but for partially wrong reasons.
