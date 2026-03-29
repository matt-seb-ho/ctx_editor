# htn20_52: High True-Negative Subset from gpt-5.2 LiC Logs

## Overview

The htn20_52 subset contains the 20 hardest problems per task (math, code, database, actions) as measured by true-negative frequency across 10 independent LiC conversations with gpt-5.2 as the assistant. These are problems where gpt-5.2 consistently fails in multi-turn settings, and the failures are genuinely the assistant's fault (not user-simulator-induced).

## Construction Process

### 1. Source data

Original LiC (Lost in Conversation) logs from `~/l3_dir`, produced by the Microsoft Research `run_simulations.py` pipeline. Each task has ~100 questions with 10 independent "lazy" sharded conversations per question using `t-gpt-5.2` as the assistant model.

### 2. False negative analysis

For every incorrect conversation across all 10 runs per question, we ran a user-simulator sufficiency check using gpt-5 as the LLM judge (`scripts/lic_false_negative_analysis_full.py`). This determines whether the user simulator's messages contained all information needed to solve the original single-turn problem.

- **True negative**: Incorrect AND user sim messages were sufficient (assistant's fault)
- **False negative**: Incorrect AND user sim messages were insufficient (user sim's fault)
- **Correct**: Model got it right

Analysis cost: ~$9.58 for 1,895 LLM calls (574 reused from initial 3-run analysis + 1,321 new).

### 3. Problem selection

For each task, problems were ranked by true-negative count (descending) and the top 20 selected. This produces a set biased toward problems where context pollution consistently causes failure.

**Quality of the selected problems:**

| Task | TN range (of top 20) | Notes |
|---|---|---|
| Actions | All 20 at 10/10 TN | Perfect: every run fails, never user sim's fault |
| Database | All 20 at 10/10 TN | Same: rock solid |
| Math | 9/10 to 5/10 TN | No 10/10 TN exists; some variance |
| Code | 10/10 to 4/10 TN | Only 1 at 10/10; weaker signal below top 5 |

### 4. Replay trace conversion

LiC log conversations were converted to the ctx_editor replay trace format. All 10 conversations per question are available as separate trace files (`{problem}__conv{0-9}.json`) enabling controlled replay on specific conversation instances.

## Files

```
data/
  htn20_52_math_subset.json        # 20 problem definitions
  htn20_52_code_subset.json
  htn20_52_database_subset.json
  htn20_52_actions_subset.json

  baseline_traces_htn20_52/
    math/                           # 200 trace files (20 problems x 10 convs)
      conv_manifest.json            # Maps sample_id -> conv metadata list
      false_negatives.json          # Empty (pre-vetted)
    code/
    database/
    actions/
```

### conv_manifest.json structure

Maps each `sample_id` to a list of conversation entries:

```json
{
  "sharded-GSM8K/123": [
    {
      "conv_id": "uuid-...",
      "index": 0,
      "trace_file": "sharded-GSM8K_123__conv0.json",
      "is_correct": false,
      "score": 0.0,
      "user_sim_sufficient": true,
      "is_true_negative": true
    },
    ...
  ]
}
```

## Comparison with dev subsets

The existing dev subsets were not optimized for hardness on any particular model:

| Task | Dev subset avg TN | htn20_52 avg TN |
|---|---|---|
| Math | 3.6/10 | 6.8/10 |
| Code | 3.2/10 | 5.8/10 |
| Database | 7.8/10 | 10.0/10 |
| Actions | 9.6/10 | 10.0/10 |

The dev math and code subsets contain many problems that gpt-5.2 solves easily or that have high false-negative rates, making them noisy for measuring intervention effectiveness.

## Usage

### Replay experiment
```bash
ctx-editor experiment=context_edit_v2 task=math_v2 model=gpt5_mini \
  load_balancer=multi_endpoint \
  task.data_file=data/htn20_52_math_subset.json \
  execution.replay_source=data/baseline_traces_htn20_52/math
```

### Selecting specific conversations
By default, replay matches the first available trace per `sample_id`. To replay a specific conversation (e.g., conv 3 for all problems), copy only the desired `*__conv3.json` files into a temp directory and point `execution.replay_source` there.

## Scripts

- `scripts/lic_false_negative_analysis.py` -- Initial 3-run false negative analysis
- `scripts/lic_false_negative_analysis_full.py` -- Full 10-run analysis (reuses prior results)
- `scripts/build_htn20_52_subset.py` -- Builds subset files and replay traces from analysis output
