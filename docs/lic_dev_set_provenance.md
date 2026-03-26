# Dev Set Provenance

On yuwan:
```bash
claude --resume f8b27124-f389-40c7-8962-2d28f00d48d0
```

**Created**: 2026-03-12
**Branch**: newleaf

## Source Data

Each dev set is a subset of `data/full_{task}_subset.json`, which contains the full evaluation pool for that task.

| Dev Set | File | Samples | Source Pool |
|---|---|---|---|
| math | `data/dev_math_subset.json` | 23 | `data/full_math_subset.json` (103) |
| code | `data/dev_code_subset.json` | 25 | `data/full_code_subset.json` (100) |
| database | `data/dev_database_subset.json` | 25 | `data/full_database_subset.json` (107) |
| actions | `data/dev_actions_subset.json` | 25 | `data/full_actions_subset.json` (105) |

## Selection Procedure

### Runs Used

For each task, 5 newleaf-branch baseline runs (S0, no context editing) were used:

- 3 runs with `gpt5_mini` config (gpt-5-mini assistant, gpt-4o-mini user/system)
- 1 run with `gpt5m_gpt4o` config (gpt-5-mini assistant, gpt-4o user/system)
- 1 run with `gpt5_mini_only` config (gpt-5-mini assistant, gpt-5-mini-minimal user/system)

Exception: code had only 4 usable runs (one gpt5_mini run's artifacts were lost to a directory collision where two experiments started in the same second and wrote to the same output directory).

### Criteria

For each sample in the source pool:

1. Count appearances across runs (a sample may be excluded/errored in some runs)
2. Count how many times `is_correct == False` (wrong answer)
3. Count how many times `is_correct is None` (excluded due to error)
4. Compute `valid_appearances = appearances - excluded`

A sample was selected if:
- `valid_appearances >= 3` (appeared in enough runs to be meaningful)
- `errors >= 3` (wrong in at least 3 runs)
- `errors / valid_appearances >= 0.6` (wrong at least 60% of the time)

### Ranking and Capping

Eligible samples were sorted by error rate (descending), then by raw error count (descending). The top 25 were selected per task. Math had only 23 eligible samples, so all were included.

| Task | Eligible | Selected | All-runs-wrong (100%) |
|---|---|---|---|
| math | 23 | 23 | Many (5/5 wrong) |
| code | 40 | 25 | Many (4/4 wrong) |
| database | 75 | 25 | Many (5/5 wrong) |
| actions | 55 | 25 | Many (5/5 wrong) |

## Known Limitations

### No false negative filtering

The selection used raw `is_correct` outcomes only. No error attribution or false negative analysis was applied. This means some selected samples may be "hard" for reasons unrelated to genuine assistant difficulty:

- **Extraction failures**: The assistant's actual answer was correct but the system agent extracted the wrong value
- **Strict comparison**: Semantically equivalent answers rejected by exact string matching (e.g., `6.00` vs `6`, equivalent SQL with different formatting)
- **Sharding distortion**: The incremental disclosure of problem information genuinely altered the problem's meaning, making it unsolvable as presented

From the error attribution data on the full-set baseline runs, these non-genuine error rates vary by task:
- **math**: ~25% of errors are non-genuine (mostly sharding distortion, some extraction)
- **code**: ~5% non-genuine (very clean evaluation signal)
- **database**: ~60% non-genuine (dominated by strict comparison and sharding distortion)
- **actions**: ~80% non-genuine (extraction failures and strict comparison dominate)

The dev sets inherit these biases. Database and actions dev sets likely contain a meaningful fraction of false negatives masquerading as hard problems.

### Cross-config selection may introduce bias

Using runs from 3 different user simulator configs means the dev set captures problems that are hard across different simulation conditions, which is arguably more robust. However, the different configs have different exclusion patterns (gpt5_mini_only excludes more samples), so a sample's "appearance count" depends partly on which configs successfully ran it.
