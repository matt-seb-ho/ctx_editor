# htn50_52: High True-Negative Subset (Top-50) from gpt-5.2 LiC Logs

## Overview

`htn50_52` is the 50-problem-per-task expansion of [`htn20_52_subset.md`](htn20_52_subset.md). Same source data, same selection methodology, same conversation traces — just a wider net for experiments that want more samples per task.

Selection: top problems per task by **true-negative count** (incorrect AND user simulator was sufficient) across 10 lazy-sharded LiC conversations per question with `t-gpt-5.2` as the assistant. Problems with TN=0 are excluded (definitionally not hard for this model).

## Methodology recap

Identical to htn20_52:

1. **Source**: `~/l3_dir/laban_lic_logs_{task}_sharded/lazy/lazy_{task}_t-gpt-5.2.jsonl` (~100 questions × 10 lazy conversations per task).
2. **Sufficiency classification**: every incorrect conversation is judged by `gpt-5` (temp 0.0) for whether the user simulator's revealed shards were sufficient to solve the original full-spec problem. See `scripts/lic_false_negative_analysis_full.py`. Cached in `outputs/lic_false_negative_analysis/user_sim_sufficiency.json`.
3. **Ranking**: per-task ranking by TN-count descending, cached in `outputs/lic_false_negative_analysis/hard_problems.json`.
4. **Selection**: `scripts/build_htn50_52_subset.py` takes the top 50 with `TN >= 1`. Ties resolved by upstream order (stable sort); this is arbitrary but acceptable since the subset isn't sensitive to tie order.

The only difference from htn20_52 is the `TOP_N = 50` cutoff and the `MIN_TN = 1` filter that drops TN=0 problems from code's tail.

## Selection results

| Task | Problems selected | TN range | Notes |
|---|---|---|---|
| Math | 50 | 9 → 1 | No 10/10 TN problems exist. Median TN ~4. |
| Code | **44** | 10 → 1 | 6 TN=0 problems dropped from naive top-50 (gpt-5.2 solves them 10/10 or 8/10). |
| Database | 50 | 10 → 6 | 21 at 10, 11 at 8, 10 at 9, 7 at 7, 1 at 6. |
| Actions | 50 | 10 → 9 | 42 at 10/10, 8 at 9/10. |

The code task has the thinnest hard tail — only one problem in the full ~100 is at TN=10, and going past rank 50 the tail is all TN=0. If you need 50 truly-hard code problems for an experiment, this data doesn't provide them; the TN=1 entries at the bottom of the code selection are the floor of "genuinely hard."

## Files

```
data/
  htn50_52_math_subset.json       # 50 problem definitions
  htn50_52_code_subset.json       # 44 problem definitions
  htn50_52_database_subset.json   # 50 problem definitions
  htn50_52_actions_subset.json    # 50 problem definitions

  baseline_traces_htn50_52/
    math/                          # 500 trace files (50 problems × 10 convs)
      conv_manifest.json
      false_negatives.json
    code/                          # 440 trace files (44 × 10)
    database/                      # 500 trace files
    actions/                       # 500 trace files
```

Each subset sample carries an `htn50_52_stats` annotation with `{true_negatives, false_negatives, correct}`. Trace and manifest formats are identical to htn20_52 — see [`htn20_52_subset.md`](htn20_52_subset.md) for field-level documentation.

## Usage

```bash
ctx-editor experiment=context_edit_v2 task=math_v2 model=gpt5_mini \
  load_balancer=multi_endpoint \
  task.data_file=data/htn50_52_math_subset.json \
  execution.replay_source=data/baseline_traces_htn50_52/math
```

Selecting a specific conversation index works the same way as for htn20_52: copy the desired `*__conv{N}.json` files into a temp directory and point `execution.replay_source` there.

## Rebuilding

```bash
python scripts/build_htn50_52_subset.py
```

Requires `~/l3_dir/` (LiC logs) and `outputs/lic_false_negative_analysis/{hard_problems,user_sim_sufficiency}.json` to exist. Output is fully deterministic given those inputs.
