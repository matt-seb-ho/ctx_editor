# Paper-Experiment Provenance Index

Maps each table/section in `neurips_2026_conference.tex` to its source experiment documentation and output directories.

## Paper: `writing/neurips_project/neurips_2026_conference.tex`

---

### Table 2: LiC Accuracy by Strategy (Main Results)

**Subset**: Dev set (23 math, 25 code, 25 database, 25 actions, minus user-sim exclusions)
**Data files**: `data/dev_{math,code,database,actions}_subset.json`
**Replay traces**: `data/baseline_traces_v2/{math,code,database}`, `data/baseline_traces/actions`
**Model**: gpt-5-mini, reasoning_effort: medium
**Experiment docs**:
- S0 (Baseline), S1, S2, S1+mem, S2+mem: `docs/reports/v8_batch_results.md` (v8 batch, 2026-03-16/17)
- S0+mem: Same source as S0, `docs/reports/v8_batch_results.md`
- AO, Concatenate User: `docs/reports/prior_work_baselines.md`
- Reset (S1.5), Reset+mem: `docs/reports/v10_paper_updates.md` (sans-issue-injection fix + accumulate)
- Gated Reset actions: `docs/reports/v10_paper_updates.md` (S2+accumulate NEW run)
- Augment+mem actions (9%): `docs/reports/memory_error_analysis.md`

**Key output directories** (from v8 batch):
- S0 baseline: embedded in replay traces (`data/baseline_traces_v2/`)
- S1: `outputs/2026-03-16/20-08-42` (math), `20-29-27` (code), `20-45-25` (database), `20-21-17` (actions)
- S2: `outputs/2026-03-16/20-13-03` (math), `20-33-06` (code), `20-47-53` (database), `20-23-18` (actions)
- S1.5 (sans-issue-injection): `outputs/2026-03-21/10-33-19` through `10-35-17`
- S2+accumulate actions: `outputs/2026-03-26/02-18-54`

---

### Table 4 (Appendix): Multi-Model LiC Results

**Subset**: htn20_52 (20 per task, hardest true-negatives from gpt-5.2 logs)
**Data files**: `data/htn20_52_{math,code,database,actions}_subset.json`
**Replay traces**: `data/baseline_traces_htn20_52/{math,code,database,actions}`
**Experiment docs**: `docs/reports/htn20_52_experiment_results.md`, `docs/reports/htn20_52_multi_model_results.md`
**Subset construction**: `docs/htn20_52_subset.md`

**Output directories** (gpt-5-mini S0):
- Math: `outputs/2026-03-26/21-42-24`
- Code: `outputs/2026-03-26/21-42-26`
- Database: `outputs/2026-03-26/21-49-55`
- Actions: `outputs/2026-03-26/21-54-54`

---

### Table 3: CollabLLM Results

**Experiment docs**: `docs/reports/collabllm_baseline_comparison.md`

---

### Table 5 (was Table 3 in earlier draft): WildChat Quality

**Experiment docs**: `docs/reports/huang_eval_consolidated.md`
**Example trajectory**: `docs/reports/huang_eval_example_trajectory.md`

---

### Table 6: Tau2-bench Results

**Experiment docs**: Referenced in paper, details in separate tau2-bench repo

---

### Table 5 (Appendix): Ablation -- Progressive Stripping

**Experiment docs**: `docs/reports/ablations/single_query_hard_attention.md`
**Source**: `docs/reports/v10_paper_updates.md` (Section 3, ablation restructure)

---

### Section 5.2: Memory Discussion

**Experiment docs**: `docs/reports/ablations/spec_curation_memory.md`, `docs/reports/memory_error_analysis.md`

---

## Dev Set Provenance

**Construction**: `docs/lic_dev_set_provenance.md`
- Math: 23 samples from 103-sample pool (problems in >=3 runs, failure rate >=60%)
- Code: 25 samples from 100-sample pool
- Database: 25 samples from 107-sample pool
- Actions: 25 samples from 105-sample pool

## htn20_52 Subset Provenance

**Construction**: `docs/htn20_52_subset.md`
- 20 problems per task, top true-negative count from gpt-5.2 LiC logs
- 10 conversations per problem available as separate trace files

## Run Index

Full historical index of all dev set experiment batches: `docs/reports/run_index.md`
