# Post-NeurIPS LiC Vanilla Baseline Runs

**Started**: 2026-05-16T06:36:23-07:00
**Strategy**: baseline (no context modification)
**User simulator**: gpt-4o-mini
**Subset**: htn50_52 (50/44/50/50 problems for math/code/database/actions)
**Runs per (model, domain)**: 3 sequential ctx-editor invocations
**User mode**: sharded (LiC-identical)
**Task evaluators**: math_v2, code_v2, database_v2, actions_v2 (new, includes 'accumulate' instruction)

## Models

| Model | Config | Endpoint pool | Per-model RPM cap |
|---|---|---|---|
| gpt-5.4 | `gpt5_4` | OpenAI (dl-openai-1/3) | 10000 / 2500 |
| DeepSeek-V4-Flash | `deepseek_v4_flash_foundry` | Foundry (mgalley-foundry2) | 250 |
| Kimi-K2.6 | `kimi_k2_6_foundry` | Foundry (mgalley-foundry2) | 100 |
| gpt-5.5 | `gpt5_5_foundry` | Foundry (mgalley-foundry2) | 250 |

Phi-4 was excluded — its Foundry quota is 1 RPM, making the matrix infeasible.

## Per-run table

Each row = one ctx-editor invocation. Same (model, domain) appears 3× with different run_idx.
Aggregate "(model, domain) means over the N runs" lives below.

| Started | Model | Task | Run | rc | Wall | Accuracy | Cost | Avg Turns | Output Dir | Log |
|---|---|---|---|---|---|---|---|---|---|---|
