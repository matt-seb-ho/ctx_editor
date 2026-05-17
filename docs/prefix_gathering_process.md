# Process: Gathering Valid Sharded Prefixes for AC3 Replay

**Date**: 2026-05-16
**Goal**: For each of the (4 models × 4 tasks × ~50 problems) cells, produce
**exactly 3 valid sharded conversation prefixes** that the next round of
context-strategy experiments can replay against. "Valid" means the user
simulator revealed enough information that the assistant's failure (when
present) is attributable to the assistant, not the user-sim.

Related: [`prefix_variance_decision.md`](prefix_variance_decision.md) for why
we want 3 distinct prefixes per problem rather than 3 sampling reps.

## Why "valid" matters

The htn50_52 subset already represents problems where models tend to fail in
multi-turn settings. But a particular failed conversation may not be a fair
test if the user simulator (gpt-4o-mini) never disclosed a critical piece of
the spec — the assistant never had a chance. Replaying the last turn of such
a prefix with AC3 (or AO, etc.) and grading the new assistant turn would be
"carried-forward" user-sim error: it would penalize the intervention for the
sim's misses.

We therefore filter prefixes through the existing FN-analysis pipeline
(`identify_false_negatives.py`, also enabled inline via
`false_negative_analysis.mode=batch` in the Hydra config). For each
conversation that scored INCORRECT, the analyzer asks gpt-5-mini:
"Did the user's revealed shards collectively contain enough information to
answer the underlying full-spec question?"

A prefix is **valid as a replay seed** iff:

- the final assistant turn was scored CORRECT, OR
- the final assistant turn was INCORRECT *and* the FN analyzer ruled the
  user-sim sufficient.

## Inputs we have at process start

After the main vanilla-sharded matrix completed (and the two rounds of
re-runs to recover from the data-bug and the math-run-1 collision), we have
**3+ runs per (model, task)** under the `htn50_52` subset:

- `outputs/2026-05-16/{HH-MM-SS}/` — 48 main-matrix cells.
- `outputs/post_neurips_lic_vanilla_redo/` — 7 code redos + 3 math redos.

Every run dir contains `traces/{sample_id}.json` (the saved sharded
conversation) plus a `false_negatives.json` summary (the FN analysis).

## Steps

### 1. Tally

`scripts/tally_valid_prefixes.py` walks all the run dirs, joins traces with
the FN verdict, and produces
`outputs/post_neurips_lic_vanilla/valid_prefix_tally.json` plus a stdout
summary table. For each (model, task) it reports the per-problem
distribution of "how many valid prefixes do we have so far?" and a list of
problems short of 3.

Result of the first tally (2026-05-16): most cells are 80-95% covered.
Code is the weakest because user-sim sufficiency for code shards is
intrinsically harder (function specs are long and detail-dense, so gpt-4o-mini
omits things more often).

### 2. Fill-in launches

`scripts/run_prefix_fillin.py` reads the tally sidecar and, for each
(model, task) cell that has short problems, launches one additional
ctx-editor vanilla-sharded pass over **only the short problems**. We don't
re-run the whole 50-problem set — each fill-in pass writes a temporary subset
data file containing only the under-covered ids.

Concurrency rules match the main matrix:

- gpt-5.4 (OpenAI endpoints, high quota) runs in parallel with the foundry chain.
- The three foundry models share one endpoint at 250 RPM each — they are
  serialized (deepseek → kimi → gpt-5.5).

Each fill-in pass adds **at most 1 valid prefix per (model, problem)** in
expectation, so a single pass closes most but not all of the gap. We tally
and re-launch in a loop until either:

- every (model, problem) cell has ≥ 3 valid prefixes, or
- two passes go by and the same problems remain stuck — at which point those
  problems get a final pass with `--user-model DeepSeek-V4-Flash` to swap in
  a stronger user simulator. (gpt-4o-mini is the default user-sim and the
  cheaper option; we only escalate when needed.)

### 3. Curate the final pool

`scripts/curate_valid_prefixes.py` (to be added) reads the (now-converged)
tally and emits a canonical prefix pool:

```
data/valid_prefixes_htn50_52/
  {model}/
    {task}/
      conv0/{sample_id}.json   # one of the 3 valid prefixes per problem
      conv1/{sample_id}.json
      conv2/{sample_id}.json
      false_negatives.json     # user-sim-induced ids (should be empty by construction)
      conv_manifest.json       # which run dir each prefix originated from
```

Each `convN/` directory is a self-contained replay source. To run AC3
against the first prefix per problem for, say, gpt-5.4 on math:

```bash
ctx-editor experiment=context_edit_v2 task=math_v2 model=gpt5_4 \
    load_balancer=multi_endpoint \
    task.data_file=data/htn50_52_math_subset.json \
    execution.replay_source=data/valid_prefixes_htn50_52/gpt5_4/math/conv0 \
    execution.replay_turns=1
```

Iterate over conv0/1/2 to get the N=3 spread.

### 4. Replay-infra compatibility check

The current `ctx_editor/execution/replay.py` loader:

- Walks `replay_source` recursively for `*.json` trace files.
- Loads each as `{sample_id: trace_data}` — **last writer wins per
  sample_id**, so a directory cannot meaningfully hold multiple prefixes for
  the same problem.

This is fine for our scheme because each `convN/` directory contains exactly
ONE prefix per problem (chosen at curation time). To run all three prefixes,
we run three separate ctx-editor invocations pointing at conv0/conv1/conv2.
The aggregator then averages the three.

We do not need to modify the replay infrastructure for this batch.

**Verified end-to-end** by a 3-sample smoke test on
`data/valid_prefixes_htn50_52/gpt5_4/math_v2/conv0/`:
1/3 correct at last-turn replay (math is the hardest task to recover on a
single-turn budget), 7.3 average turns preserved from prefix, 0 errors,
$0.01 total cost. The prefix loader, the per-trace truncation
(`build_replay_trace(replay_turns=1)`), and the baseline-strategy
last-turn regeneration all worked as expected.

If we later want to fold the 3-prefix dispatch into a single invocation
(e.g., to amortize Python startup), the change is small: modify
`load_baseline_traces` to optionally return a list per sample_id and tweak
the runner to dispatch one task per (sample, prefix). Out of scope for now.

**Pre-existing infra footgun** (caught during the smoke):
`run_experiment.py` computes `outputs_root = output_dir.parent.parent` to
locate `runs.yaml`. If `logging.output_dir` is < 2 levels deep under the
repo root (e.g. a `/tmp/...` path), the ledger write tries to land at
`/runs.yaml` and crashes the run with `PermissionError`. The experiment
itself completes — metrics.json + traces are saved — but the ledger update
fails. **Always pass an `logging.output_dir` that is ≥ 2 levels deep under
the repo root** (the existing
`outputs/post_neurips_lic_vanilla*/{exp_name}_{ts}` convention is fine).

### 5. Document and commit

The final prefix pool + this process doc + the per-cell tally JSON go into
the repo. The pool directory is checked in (it's a small JSON corpus,
~600 files × ~few KB). Future strategy experiments cite this exact pool so
results are comparable across runs.

## Cost estimate

Approximate counts at the time of this writing (post first tally):

| Model | Short problems (sum across 4 tasks) |
|---|---|
| gpt-5.4 | 24 |
| DeepSeek-V4-Flash | 28 |
| Kimi-K2.6 | 27 |
| gpt-5.5 | 18 |

One fill-in pass = ~97 ctx-editor sample invocations. With ~85% sufficiency
rate per pass, expect ~83 of those to become valid prefixes — closing roughly
85% of the gap. A second pass (~14 problems still short) handles the
remainder; problems still short after pass 2 escalate to dsv4f user-sim.

Per-call costs are tiny (~$0.05 per call for foundry models, ~$0.50 for
gpt-5.4). Whole fill-in process is well under $20 total.
