# T12 + T13 — Memory order-sensitivity and train/eval-split analysis

**Owner:** autoresearch agent, overnight session 2026-07-29.
**Deliverable for:** reviewer 5YHP, W6 commitment in `neurips_review/replies/v4/03_reviewer_5YHP.md`.
**Status:** in progress (see Results at the bottom).

---

## 0. The exact promise we are honouring

`neurips_review/replies/v4/03_reviewer_5YHP.md:75-81`:

> **W6:** The memory results are mixed and not yet well characterized... the cheatsheet can introduce stale or overly general priors, which is itself a form of context pollution at the analyzer level.
>
> **Response to W6:** We appreciate this observation, and note that memory is an **optional, ablated component**: every main result in the paper holds without it, and no headline claim depends on it.
>
> We would also highlight that your diagnosis is a satisfying consistency check on our own thesis rather than a counterexample to it. A stale cheatsheet polluting the analyzer is precisely the mechanism the paper identifies, now appearing one level up. We will make this connection explicit.
>
> **Revision:** We will present memory explicitly as an optional extension with per-setting deltas, and **add order-sensitivity and train/evaluation-split analysis**.

So the deliverable is two analyses, on the memory component, in the setting the paper reports memory in.

---

## 1. What the paper actually reports for memory (archaeology)

Two memory panels exist in `writing/overleaf_repo/neurips/neurips_2026_conference.tex`:

| Panel | Where | Regime | Source |
|---|---|---|---|
| LiC `+ Memory` rows in Table 1 (`tab:main`, lines 263 / 270 / 272) | main body | **online / continual** | dev-set replay runs |
| WildChat memory ablation (`tab:wildchat-memory`, app. `app:memory-details`) | appendix | **offline, 1/3 train — 2/3 eval split** | `outputs/huang_eval/memory/2026-03-30/13-57-16` (not on disk) |

The paper states the regimes explicitly (line 709):

> "*Online*: reflections update the cheatsheet incrementally as problems are solved in batches, so later problems benefit from accumulated principles, a form of continual test-time learning. *Offline*: a set of training trajectories is used to initialize the cheatsheet ... and the frozen cheatsheet is applied at evaluation time. **On LiC, we use online learning.** On WildChat, we use the offline regime with a train/eval split (one-third training, two-thirds evaluation) **to avoid confounding memory quality with ordering effects** and to test cross-domain transfer."

Two consequences that decide the whole design of T12/T13:

1. **The LiC memory numbers in Table 1 are order-dependent by construction.** Under online learning the cheatsheet at instance *i* is a function of the instances that happened to precede *i*. The paper's own WildChat rationale names ordering effects as a thing to be avoided — and then LiC does not avoid them. T12 must therefore measure order sensitivity **in the online regime**, because that is the regime the reported numbers come from.
2. **The LiC memory numbers have no train/eval split at all.** Training data ≡ evaluation data. This is not a bug to be hidden — it is *transductive / continual test-time learning*, a legitimate and named setting — but it is exactly what a reviewer means by "has the cheatsheet memorised the eval set?", so T13 must (a) state it plainly, (b) quantify the residual self-leakage, and (c) supply a fully **inductive** (disjoint-train-set, frozen-cheatsheet) number as the clean comparison.

### 1.1 Provenance of the Table-1 LiC memory numbers

`docs/reports/memory_error_analysis.md` (2026-03-17, "v8 batch, dev set, compare-targeted memory") reports:

| Config | Math (n=20) | Code (n≈19) | Database (n=25) |
|---|---|---|---|
| S1 (Augment) | 16/20 (80%) | 10/18 (56%) | 8/25 (32%) |
| S1+mem | 18/20 (90%) | 13/19 (68%) | 11/25 (44%) |

These are exactly the Table-1 numbers (Augment 80.0/55.6/32.0; Augment+Memory 90.0/68.4/44.0). So the Table-1 memory cells come from dev-set **replay** runs of the shape in `scripts/run_replay_v8.sh:85-91`:

```
experiment=append_analysis_memory task=dev_<task> \
  execution.replay_source=data/baseline_traces_v2/<task> \
  execution.mode=batched execution.batch_size=5 \
  memory.enabled=true memory.source=continual memory.target=analyzer \
  memory.include_full_spec_q=true memory.include_ground_truth_a=true
```

Note `include_full_spec_q=true include_ground_truth_a=true`: **the reflection step sees the fully-specified question and the gold answer** of each already-completed trajectory. That is oracle grounding on evaluation instances. Disclosed below.

### 1.2 Where `data/lic_mem_learn_set.json` fits

`grep -rn lic_mem_learn_set` over the whole repo returns **zero** hits outside this worklog and RECON's file inventory. It is a 40-instance held-out learn set (10 math / 10 code / 10 database / 10 actions, git commit `62b2d77 "feat: add mem learn set"`) that was built for an offline LiC regime **that never made it into the paper**. It is nonetheless the file the task brief names, and it is the right training pool for the clean inductive arm — so T13 uses it.

---

## 2. Design decisions (and why)

**Venue = LiC-database, dev set (n=25), replay on `data/baseline_traces_v2/database`.**
Reasons: (a) it is the exact cell that produces the paper's largest memory delta (+12.0pp, 32.0 → 44.0), so an order-sensitivity result there is maximally load-bearing; (b) it is far from ceiling (baseline FC 4.0%), unlike LiC-math under gpt-5.4-mini which saturates; (c) replay is one-turn regeneration, so a 25-sample cell costs ~$0.25 and ~3 min, which is what makes 4 orderings × 2 regimes affordable. LiC-math (n=23) is run as a second venue for cross-task confirmation.

**T12 measures the online regime, not an offline one.** The brief says "vary only the trajectory ordering ... rebuild the cheatsheet each time". In the online regime the trajectory ordering *is* the sample ordering, since each evaluated instance also becomes a training trajectory. Shuffling the data file therefore does exactly the required manipulation, and it perturbs the protocol that actually generated the published numbers. `BatchedRunner._batches` (`src/ctx_editor/execution/batched.py:72`) slices `problems` in list order and `load_samples` (`run_experiment.py:87-110`) preserves data-file order through filtering, so data-file order == batch order. Verified by reading, not assumed.

**Seeds.** `cfg.seed` is inert on the LiC harness (RECON §0.1). So orderings are materialised as **separate data files** with recorded `random.Random(seed)` shuffles: `ord0` = published order, then seeds **1001, 1002, 1003**. Files: `neurips_review/autoresearch/tasks/T12-T13/data/dev_<task>_ord<seed>.json`. Generation snippet is in §5.

**No-memory reference runs with the analysis cache disabled** (`experiment.strategy.analysis_cache_dir=null`). `experiment/append_analysis.yaml` sets `analysis_cache_dir: outputs/analysis_cache` (242 cached entries on disk) while `append_analysis_memory.yaml` does not, so leaving it on would compare a cached-analysis arm against a fresh-analysis arm.

**T13 has three parts**, because the honest answer to "is the memory benefit contaminated by train/eval overlap" has three components:
1. *The measured overlap between the designated learn set and every candidate eval set* — free, no API.
2. *The actual protocol's self-overlap* — the online LiC regime trains on its own eval set (100% overlap), with a residual-leakage bound derived from the batch structure.
3. *A clean inductive number* — cheatsheet learned offline from the disjoint `lic_mem_learn_set`, frozen, evaluated on the same eval set, reported on the non-overlapping subset.

**Model / harness.** `model=gpt5_4_mini_trapi load_balancer=trapi`, `execution.max_concurrent=5`, and the mandatory `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` on every run (the default `gpt-5-mini` is not served on TRAPI and silently no-ops).

---

## 3. Overlap measurement (T13, part 1) — no API cost

Method: exact match on `task_id`; exact match on whitespace-normalised `full_spec_q`; near-duplicate = token-set Jaccard over `full_spec_q`, per eval item taking the max over all 40 learn items. (`question` is absent on code rows, so `full_spec_q`, present on every row of every file, is the join key.)

`data/lic_mem_learn_set.json` (n=40; 10 math / 10 code / 10 database / 10 actions) versus every candidate eval set:

| Eval set | n | exact `task_id` overlap | exact text overlap | max Jaccard | # items with J ≥ 0.9 |
|---|---:|---:|---:|---:|---:|
| `data/lic_eval_subset.json` (canonical `*_v2` default) | 120 | **0** | **0** | 0.416 | 0 |
| `data/lic_subset30.json` | 120 | **0** | **0** | 0.416 | 0 |
| `data/test_math_subset.json` | 9 | 0 | 0 | 0.196 | 0 |
| `data/dev_math_subset.json` | 23 | 3 | 3 | 1.000 | 3 |
| `data/dev_code_subset.json` | 25 | 3 | 3 | 1.000 | 3 |
| `data/dev_database_subset.json` | 25 | 3 | 3 | 1.000 | 3 |
| `data/dev_actions_subset.json` | 25 | 2 | 2 | 1.000 | 2 |
| `data/math_full_subset.json` | 103 | 10 | 10 | 1.000 | 10 |
| `data/rebuttal_random_math40.json` | 40 | 3 | 3 | 1.000 | 3 |
| `data/htn50_52_math_subset.json` | 50 | 3 | 3 | 1.000 | 3 |
| `data/htn50_52_database_subset.json` | 50 | 5 | 5 | 1.000 | 5 |
| `data/lic_mini_eval4.json` | 96 | 7 | 7 | 1.000 | 7 |

The max-Jaccard of 0.416 against `lic_eval_subset` is between two *different* LiveCodeBench problems and is driven by shared boilerplate (`def`, `return`, `example`, `constraints`); no near-duplicate structure survives above J = 0.5.

**Reading.** Against the canonical LiC eval subset the designated learn set is *perfectly* disjoint (0/120 by id and by text, no near-duplicates). Against the **dev subsets — which are the sets the Table-1 memory rows are actually computed on** — it is **11/98 = 11.2%** overlapping (3 math, 3 code, 3 database, 2 actions). The specific colliding ids:

- math: `sharded-GSM8K/14`, `sharded-GSM8K/237`, `sharded-GSM8K/307`
- code: `sharded-HumanEval/113`, `sharded-livecodebench/2756`, `sharded-livecodebench/2845`
- database: `sharded-spider-val-43-hard`, `sharded-spider-val-555-medium`, `sharded-spider-val-846-medium`
- actions: `sharded-BFCL/parallel_175`, `sharded-BFCL/parallel_35`

This 11.2% never contaminated a published number, because the learn set was never used for a published number. It does mean any *future* offline LiC memory arm trained on `lic_mem_learn_set` and evaluated on a dev subset must exclude those 11 ids — which is what the T13 clean-subset arm below does (database clean subset: n = 22).

### 3.1 The overlap that actually matters: the online regime trains on its own eval set

For the LiC `+ Memory` rows there is no train/eval split. `execution.mode=batched, batch_size=5, memory.source=continual` means:

- batch 1 (5 instances) is evaluated with an **empty** cheatsheet — a genuinely memory-free control that comes for free inside every online run;
- batch *b* is evaluated with a cheatsheet distilled from batches 1..*b*−1, i.e. from **5(b−1) other instances of the same evaluation set**, together with their `full_spec_q` and their gold `ground_truth_a` (both grounding flags are on);
- memory is cloned/frozen inside a batch, so **no instance ever contributes to its own prediction**: self-leakage is exactly zero.

So the correct characterisation is: *transductive, oracle-grounded, continual test-time learning across evaluation instances, with zero instance-level self-leakage*. That is what we should write, and it is checkable from the code (`batched.py:75-140`) rather than from our assurances.

The batch structure also hands us a dose–response probe for free: pooled over the four orderings of T12, each instance appears at several batch positions, so we can regress correctness on batch index. Flat ⇒ the cheatsheet is not buying anything from having seen more eval instances; rising ⇒ it is, and the transductive framing is load-bearing. Reported in §6.

---

## 4. Runs

All from `/home/t-matthewho/ac3/ctx_editor` with `. .venv/bin/activate`. Drivers:
`neurips_review/autoresearch/tasks/T12-T13/run_t12.sh`, `.../run_t13.sh`. Logs: `.../t12_<task>.log`, `.../t13_<task>.log`.
Output root: `outputs/T12_T13/<task>/`. Cheatsheets: `neurips_review/autoresearch/tasks/T12-T13/memories/<task>/`.

### T12 (online regime, 5 cells per task)

```bash
# no-memory reference
ctx-editor experiment=append_analysis model=gpt5_4_mini_trapi load_balancer=trapi \
  task=dev_database task.data_file=<...>/data/dev_database_ord0.json \
  execution.replay_source=data/baseline_traces_v2/database execution.replay_turns=1 \
  execution.mode=parallel execution.max_concurrent=5 \
  experiment.strategy.analysis_cache_dir=null \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  logging.output_dir=outputs/T12_T13/database/ref_nomem

# one per ordering ORD in {ord0, ord1001, ord1002, ord1003}
ctx-editor experiment=append_analysis_memory model=gpt5_4_mini_trapi load_balancer=trapi \
  task=dev_database task.data_file=<...>/data/dev_database_${ORD}.json \
  execution.replay_source=data/baseline_traces_v2/database execution.replay_turns=1 \
  execution.mode=batched execution.batch_size=5 execution.max_concurrent=5 \
  memory.enabled=true memory.source=continual memory.target=analyzer \
  memory.include_full_spec_q=true memory.include_ground_truth_a=true \
  memory.save_path=<...>/memories/database/${ORD}_cheatsheet.json \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  logging.output_dir=outputs/T12_T13/database/mem_${ORD}
```

### T13 (inductive arm, 1 + 4 + 4 cells per task)

1. training trajectories: `experiment=append_analysis`, `task.data_file=data/lic_mem_learn_set.json`, `task=dev_<task>` (its `filter` selects the 10 rows of that task), end-to-end (no replay), cache off → `outputs/T12_T13/<task>/train_traj/results.json`;
2. `memory.source=offline memory.offline_trajectories=<shuffled results>.json memory.offline_batch_size=5` × 4 orderings → frozen cheatsheets;
3. `experiment=append_analysis_memory memory.source=<frozen cheatsheet> execution.mode=parallel` on the *same* replay eval set as T12.

Step 2 doubles as an **offline-regime** order-sensitivity measurement, so T12 gets both regimes for the price of T13's setup.

---

## 5. Reproducing the orderings

```python
import json, random
for task, src in [('database','data/dev_database_subset.json'), ('math','data/dev_math_subset.json')]:
    d = json.load(open(src))
    json.dump(d, open(f'.../dev_{task}_ord0.json','w'))          # published order
    for seed in (1001, 1002, 1003):
        dd = list(d); random.Random(seed).shuffle(dd)
        json.dump(dd, open(f'.../dev_{task}_ord{seed}.json','w'))
```

First five ids per ordering (for audit):

| Ordering | database | math |
|---|---|---|
| ord0 | 633-medium, 982-extra, 946-medium, 497-medium, 129-extra | 1166, 435, 1190, 14, 237 |
| ord1001 | 75-medium, 695-extra, 43-hard, 972-medium, 555-medium | 237, 40, 117, 855, 576 |
| ord1002 | 389-medium, 401-hard, 846-medium, 982-extra, 494-medium | 968, 267, 315, 14, 1066 |
| ord1003 | 389-medium, 497-medium, 235-medium, 75-medium, 129-extra | 1124, 14, 855, 576, 237 |

---

## 6. Results

### 6.0 Verification that the manipulation is real (per orchestrator reminder)

- **`seed=` is not used anywhere in this task.** RECON §0.1 documents that `cfg.seed` is inert on the LiC harness. Orderings are materialised as **four physical data files per task** (`data/dev_<task>_ord{0,1001,1002,1003}.json`) whose element order differs; `load_samples` (`run_experiment.py:87-110`) preserves file order through the task filter, and `BatchedRunner._batches` (`batched.py:72`) slices `problems[i:i+batch_size]` in that order, so the file order *is* the cheatsheet-construction order. Confirmed empirically as well: the four orderings produce four **different** cheatsheets (mean pairwise content-word Jaccard 0.30, §6.3) and four different accuracies — which could not happen if the shuffle were inert.
- **`false_negative_analysis.model=gpt-5.4-mini_2026-03-17` is passed on every cell** via the `COMMON` array in both driver scripts. All FN-adjusted numbers below therefore come from a model that TRAPI actually serves. On these replay cells the FN adjustment is almost always a no-op anyway (0 user-sim-induced on 8 of 10 database cells), which is expected: replay fixes the user trajectory.

### 6.1 T12 — order sensitivity, LiC-database (n=25, the paper's biggest memory cell)

Reference: **Augment, no memory = 36.0% (9/25)**. (Paper's Table-1 Augment/database cell is 32.0% on gpt-5-mini; we get 36.0% on gpt-5.4-mini on the same 25 instances and the same replay traces — the venue replicates.)

Online (continual) memory, one cell per ordering:

| Ordering | correct | accuracy |
|---|---:|---:|
| ord0 (published order) | 5/25 | 20.0% |
| ord1001 | 7/25 | 28.0% |
| ord1002 | 7/25 | 28.0% |
| ord1003 | 9/25 | 36.0% |

**Mean ± std = 28.0 ± 6.5 pp; range 20.0–36.0 (16.0 pp spread = 4 of 25 instances).**
Delta vs no memory: **−8.0 pp on average**; the best ordering only reaches parity with no memory.
Instance-level instability: **8/25 (32%) of instances change correctness across orderings.**
Paired, pooled over the four orderings: memory fixes 6 instance-runs, breaks 14; exact sign test p = 0.115.

**This is an unflattering result and we should report it as one.** On the cell where the paper claims memory's largest LiC gain (+12.0 pp), under gpt-5.4-mini memory is (a) net harmful and (b) more sensitive to trajectory ordering than the effect size the paper attributes to it.

### 6.2 T12 — order sensitivity, LiC-math (n=20)

Reference: **Augment, no memory = 80.0% (16/20)** — an exact match to the paper's Table-1 Augment/math cell (16/20), so this venue replicates too.

| Ordering | correct | raw | FN-adjusted |
|---|---:|---:|---:|
| ord0 | 16/20 | 80.0% | 84.2% (1 user-sim-induced excluded) |
| ord1001 | 17/20 | 85.0% | 85.0% |
| ord1002 | 16/20 | 80.0% | 84.2% (1 excluded) |
| ord1003 | 16/20 | 80.0% | 80.0% |

**Mean ± std = 81.2 ± 2.5 pp (raw); 83.4 ± 2.3 pp (FN-adjusted).** Delta vs no memory +1.2 pp.
Instance-level instability: 2/20 (10%). Sign test on pooled pairs: 4 fixes / 3 breaks, p = 1.0.

Math is near-ceiling for gpt-5.4-mini (baseline Augment already 80%), so both the memory effect and its order sensitivity are compressed. Consistent with the paper's own claim that memory helps only where headroom exists — but it also means math cannot discriminate, and the discriminating venue (database) is the one that came back negative.

### 6.3 Cheatsheet divergence across orderings

Same 25 (resp. 20) trajectories, different presentation order:

| Task / regime | words per cheatsheet | mean pairwise Jaccard (content words, len>3) |
|---|---|---:|
| database, online | 813 / 907 / 1060 / 1014 | **0.300** |
| math, online | 1060 / 989 / 1075 / 932 | **0.320** |

Qualitatively: the four cheatsheets **converge thematically and diverge operationally**. All four database cheatsheets open with the same headline principle — *rebuild the task spec from user turns only; treat the latest user turn as authoritative; do not let assistant framing enter the spec.* But the structure (flat bullet list vs. numbered sections vs. prose), the granularity, and the specific operative sub-rules differ substantially, which is what a 0.30 Jaccard means. So the learner reliably recovers the *gist* and unreliably recovers the *detail* — and it is the detail that is injected into the analyzer's Query 2 and drives the 16 pp accuracy spread.

### 6.4 T13 — dose-response (free contamination probe from the online arms)

Accuracy by batch index, pooled over the four orderings (batch *b* is evaluated with a cheatsheet distilled from 5(*b*−1) **other** eval instances plus their gold answers):

| batch | prior eval instances in memory | database | math |
|---|---:|---:|---:|
| 1 | 0 (empty cheatsheet) | 4/20 = 20.0% | 18/20 = 90.0% |
| 2 | 5 | 7/20 = 35.0% | 17/20 = 85.0% |
| 3 | 10 | 5/20 = 25.0% | 17/20 = 85.0% |
| 4 | 15 | 7/20 = 35.0% | 13/20 = 65.0% |
| 5 | 20 | 5/20 = 25.0% | — |

No monotone increase in either task; math trends *down*. **There is no dose-response in exposure to other evaluation instances**, which is the strongest available evidence that the online LiC memory numbers are not driven by transductive leakage — the cheatsheet is not accumulating eval-set-specific knowledge, it is accumulating (increasingly stale, increasingly general) analyzer priors. That is exactly 5YHP's W6 hypothesis, and we can now say we measured it.

---

## 7. Incident: duplicated background chain (2026-07-29 10:13–10:52)

**What happened.** After the T12-database sweep, the follow-on runs were launched from a wrapper script whose guard was `while pgrep -f "run_t12.sh database"; do sleep 20; done`. That pattern matched the wrapper's *own* command line (the string appears in the `bash -c` that created the script), so the wrapper spun forever. Killing the visible PID killed the `bash -c` parent but **not** the detached `/tmp/chain.sh`, and a `pkill -f "^/tmp/chain.sh"` failed to match because the actual cmdline is `/bin/bash /tmp/chain.sh`. A replacement wrapper was then launched, so **two identical chains ran concurrently from 10:14 to 10:52**, both writing to the same `outputs/T12_T13/...` directories and both at `max_concurrent=5` (so 10 against the shared TRAPI cap, over the agreed budget).

**How it was detected.** `outputs/T12_T13/database/frozen_ord0/` had `metrics.json`/`results.json` reporting 10/25 correct and `run_summary.json`/`summary.txt` reporting 8/25 — an internal contradiction impossible within a single run, since both are serialised from the same `metrics` dict (`run_experiment.py:595-650`).

**Blast radius and remedy.** The T12-database sweep (09:53–10:12) predates the incident and was launched once; all five of its cells were verified internally consistent (`metrics.correct == run_summary.metrics.correct == count(results.is_correct)` for `ref_nomem`, `mem_ord0/1001/1002/1003`). Everything produced after 10:14 — `database/{train_traj,offlinelearn_*,frozen_*}`, all of `math/`, and the corresponding cheatsheets — was **deleted and re-run under a single chain with an `flock` guard**. The T12-math numbers in §6.2 and the divergence numbers for math in §6.3 are from the re-run, not from the contaminated pass.

**Lesson for other agents in this session:** do not guard a background chain with `pgrep -f <script name>`; use `flock` on a lockfile, and verify `metrics.json` agrees with `run_summary.json` before trusting any output dir.

---

## 8. Dead ends / notes

- `data/dev_math_train.json` and `data/dev_*_test.json` (referenced by `config/task/dev_*_{train,test}.yaml` and by `scripts/run_spec_curation_memory_experiment.sh`) **do not exist on disk**. The soft-attention spec-curation train/test split reported in appendix `app:soft-attention` is therefore not reproducible here; it is a separate, already-clean split and is not what W6 asks about, so it was not chased.
- No memory snapshot (`*cheatsheet*.json`) exists anywhere on the machine (confirms RECON §B.4), so every cheatsheet in this task is freshly learned. The paper-era cheatsheets cannot be diffed against ours.
- `cfg.seed` is inert on this harness; ordering had to be materialised as data files. Do not report these as "seeds" in the paper — report them as *recorded orderings*.
