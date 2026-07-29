# T2A — Tier-A pollution-detection evaluation (constructed pollution, no judge)

**Reviewer prompt:** 5YHP W5 — "show AC3 actually *detects pollution*, not just that accuracy went up."
**Design source:** `neurips_review/experiment_todos.md` §T2, Tier A.
**Status:** in progress (2026-07-29 overnight session). Operator asleep; every ambiguity resolved here.

---

## 0. Reconnaissance (t+0 .. t+20min)

Read first, as instructed: `experiment_todos.md` §T2, `tasks/T2c/{worklog,RESULTS}.md`, `tasks/RECON/worklog.md`.

### 0.1 Trap check — `seed=`

RECON §0.1 says `cfg.seed` is inert on LiC; the task brief says a teammate fixed the dispatcher
this session and told me to **verify the fix is present before relying on it**.

How I checked (this working tree, `main` @ `4e67b96`):
```
grep -rn "seed" src/ctx_editor/run_experiment.py     -> 0 hits
grep -rn "seed" src/ctx_editor/execution/*.py        -> 0 hits
grep -rln "seed" src/ctx_editor/                     -> only run_collabllm.py, huang_eval/*, config yamls
```
**The fix is NOT on `main` in this tree.** `git log` shows `fbf91e4 chore(T8): merge main into
seed-fix branch ...`, i.e. the fix lives on a branch that was never merged back. I am told not to
`git checkout` in this tree (trap 4), so:

**Decision D0. I do not use `seed=` at all.** T2A does not need it: determinism comes from
(a) a fixed, on-disk set of injected traces that I generate once with a `random.Random(2026)` and
write to `data/t2a_injected/`, and (b) replay mode, which pins the entire conversation prefix.
The only stochastic element left is the analyzer/assistant sampling temperature, which I handle by
reporting per-run n and, where it matters, reps.

### 0.2 Artifact discovery

The pieces I need are all on disk (nothing has to come out of the blob snapshot):

| Artifact | Path | Size |
|---|---|---|
| Paper's phase-1 replay prefix pools | `data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/{database_v2,code_v2}/conv{0,1,2}` | database 50/50/50, code 41/38/37 |
| Spider SQLite DBs (restored this session) | `data/spider/databases/` | 29 entries |
| Smaller canonical replay source | `data/baseline_traces_v2/{database,code}/` | 25 each; baseline 1/25 and 3/25 correct |

Trace schema (confirmed by direct read, matches T2c §1):
`{sample_id, task_name, experiment_type, is_correct, score, models, trace:{messages, logs, num_resets}, timestamp}`
with `messages` = `[system, user, assistant, user, assistant, ...]` and `logs` carrying
`shard_revealed` / `verification` / `answer_evaluation` on a baseline trace.

**Decision D1 — venue.** LiC **database** and **code** only, per the brief. No math (ceiling +
T2c showed math is where the analyzer leaks the gold answer, which would confound detection).

**Decision D2 — replay source.** The phase-1 `valid_prefixes_htn50_52` pools, because (a) they are
the paper's own prefixes, (b) they are already curated as *valid* (conversation reached the final
turn), and (c) 150 database + 116 code prefixes is far more than `baseline_traces_v2`'s 25.
