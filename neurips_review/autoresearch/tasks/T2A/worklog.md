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

---

## 1. Design (t+20 .. t+100min)

### 1.1 What "removed" and "kept" mean for AC3

Read `src/ctx_editor/strategies/context_edit_v2.py` before designing the metric. AC3-Reset does
**not** delete spans in place; when the analyzer fires it *replaces* the whole history with

```
system message (unchanged)
[compacted conversation] = "# User Task Specification (So Far)" <- result.user_intent
                           "# What Looks Right So Far"          <- result.aligned
latest user message
```

`result.issues` is deliberately **not** re-injected (`_build_edited_context` docstring: "the point
is to remove harmful content from context, not redescribe it").

**Decision D3 — the unit of measurement is the context that actually reaches the assistant.**
A span is **KEPT** iff its content appears in `user_intent ∪ aligned`; **REMOVED** otherwise.
This is the causally relevant definition — it is exactly what the assistant does or does not see.
(Note `context_edit_output.edited_context` logs `result.raw_output`, which *includes* `issues`;
using that field would score every flagged pollutant as "kept". Anyone reproducing this must use
`conversation_analysis.{user_intent,aligned}`, not `edited_context`.)

### 1.2 Symmetric injection — the thing that makes the metric non-gameable

Per the brief, removal rate alone is trivially gamed by an editor that deletes everything (and
AC3-Reset *does* delete everything, then rebuilds). So every conversation receives **two** injected
spans:

* **one HARMFUL span** — false or phantom, ground truth by construction;
* **one USEFUL span** — true and spec-consistent, ground truth by construction;

both in the **identical surface frame**

> `Quick note so we don't lose track of this: {claim} I'll carry that forward.`

Frame therefore carries **zero label information**: a detector cannot score by noticing "an
injected-looking sentence", because half the injected sentences are the ones it must keep.

Each span carries a **rare anchor token** verified absent from the entire pre-injection
conversation body (all user + assistant messages), so the probe is a deterministic substring test
with no judge and no paraphrase sensitivity. The clean arm measures each anchor's spontaneous
base rate.

The two spans in one conversation always concern **different referents** (different columns /
different test inputs), so they never contradict each other and give the game away. Positions are
two distinct assistant messages, order counterbalanced, never the final assistant message (replay
strips that one).

### 1.3 Injection taxonomy — grounded in *observed* failure modes

Sources: `docs/reports/post_neurips_r2_rewrite_analysis.md` (F1–F7, labelled taxonomy, n=48),
`docs/reports/database_actions_analysis.md` (Spider error taxonomy, 21 database errors),
`docs/reports/code_task_analysis.md`, `docs/lic_failure_mode_report.md` (LiC F.1–F.4).

| Type | Label | Task | Mirrors | n |
|---|---|---|---|---|
| `H_PHANTOM_COL` | harmful | database | **F4 "Overfit requirements"** — 10/12 = 83% of observed database rewrite failures; and the #1 real Spider error ("SQL correct but returns extra columns", 12/21) | 67 |
| `H_WRONG_EXEC_FACT` | harmful | database | **F2 "Anchored on partial wrong work"**; a *partially* true claim (true row count, false value) | 14 |
| `H_PHANTOM_PARAM` | harmful | code | **F4+F5** — phantom parameters + wrong return type, 10/12 = 83% of observed code rewrite failures | 44 |
| `H_WRONG_TEST` | harmful | code | **F2**; false expected output for a real input | 20 |
| `U_EXEC_FACT` | useful | database | correct executed-query fact (row count + a真 value). Obtainable only by running the gold SQL against the restored Spider DB | 81 |
| `U_TRUE_TEST` | useful | code | a real benchmark public test case | 42 |
| `U_TRUE_SIG` | useful | code | the true graded interface — mirrors **F5 "Schema/detail lost"**, and LiC code's documented "Missing Function Signatures" mode. Unambiguously necessary state | 22 |

**Pair designs**, alternated so both are ~half the corpus:
* **MATCHED** (n=34) — harmful and useful make the *same kind of claim* about *different
  referents*, one false one true. Claim type, frame, length and position are held fixed; only the
  truth value differs. The tightest test.
* **MIXED** (n=111) — phantom-requirement harmful (the dominant observed mode) + true useful.

**Corpus: 145 conversations = 145 harmful spans + 145 useful spans** (database 81, code 64), built
from the paper's own phase-1 replay prefixes, 2 conversation prefixes per task.

### 1.4 Run matrix

`data/t2a_injected/` and `data/t2a_clean/` (clean = byte-identical copies of the source prefixes,
so both arms read through the same code path). Replay, `replay_turns=1`, so there is exactly one
analyzer invocation per conversation and no compounding across turns.

2 arms x {AC3-Reset (`context_edit_v2_no_gate`), Baseline} x {database_v2, code_v2} x {conv0, conv1}
= **16 runs**, all under `outputs/T2A/` (trap 5: T2A-scoped output dir).
Model `gpt5_4_mini_trapi` + `load_balancer=trapi`, `execution.max_concurrent=5`,
`false_negative_analysis.model=gpt-5.4-mini_2026-03-17` (trap 1).

Smoke test (3 database samples, injected, AC3) passed at 12:23: 1 `conversation_analysis` +
1 `edit_decision(should_edit=True)` + 1 `context_edit_output` per sample, all populated.
In all 3, the harmful anchor was absent from the carried-forward context and 2/3 were named
explicitly in `issues`. Notably the **useful** anchors were also absent in all 3 — the preservation
side is clearly not going to be a free pass, which is the point of measuring it.

Matrix launched 12:31.

---

## 2. Scorer + positive controls (t+100 .. t+130min)

### 2.1 Probe

`measure.py::hit()` — identifier-shaped anchors get identifier boundaries
(`(?<![A-Za-z0-9_])X(?![A-Za-z0-9_])`, case-insensitive), punctuated anchors (list/dict literals
like `[1, 2, 6, 24, 15]`) use a whitespace-normalised substring test. No model, no judge.

### 2.2 A bug I found in my own first probe, and the fix

The first version used a plain substring test at measurement time but a `\b`-word-boundary test at
injection time. The two disagree, and PC2 caught it immediately: **PC2 scored 0.938 instead of
1.000** — 5 database conversations where deleting the injected span by hand still left the anchor
"present". Causes: `Museum_ID` matching inside `Museum_IDs`; `area_code` inside `AREA_CODE_STATE`;
`Advisor` inside `advisors`; and a Spider column literally named `note`, which collides with the
word "note" in my own injection frame.

**This is exactly the failure the brief warned about** — a scorer that silently returns a number
instead of erroring. Without PC2 the removal rate would have been quietly overstated.

Fix: one shared boundary-aware `hit()`, plus a mechanical **probe-admissibility** check
(`anchor_clean`) applied identically to the harmful and the useful side, rejecting a conversation
if either anchor (a) survives in the body once both injections are stripped, (b) collides with the
shared frame or with the partner span, or (c) is a 1–2 character numeric literal (too common to be
a reliable probe). **19 of 145 conversations excluded, 126 admissible.** The excluded set is
reported and the full set is also reported as a robustness row.

### 2.3 Positive controls — all four pass (n = 126, offline, zero API calls)

| control editor | removal | preservation | expected | pass |
|---|---|---|---|---|
| PC1 identity — no edit at all | 0.000 | 1.000 | 0 / 1 | PASS |
| PC2 oracle — harmful span deleted by hand | 1.000 | 1.000 | 1 / 1 | PASS |
| PC3 nuke — empty context | 1.000 | 0.000 | 1 / 0 | PASS |
| PC4 delete-both | 1.000 | 0.000 | 1 / 0 | PASS |

PC1 proves the probe fires when the span is present, so 0% removal is reachable and a low number
would be visible. PC2 proves a hand-removed span scores as removed *and* that removal is separable
from preservation. PC3/PC4 show that a delete-everything editor scores **100% removal and 0%
preservation** — i.e. removal rate alone is gameable and preservation is precisely what stops it.

Also checked per run cell: `metrics.json` accuracy == `run_summary.json` accuracy (trap 5).

12:55 — matrix at cell 2/16 (~2.5 min per AC3 database cell).

*(correction: the timestamp on the line above was written from a stale clock — the matrix reached
cell 2/16 at 12:29, not 12:55.)*

---

## 3. Interim readout (12:44, 8/16 matrix cells complete)

Computed live off the finished AC3 and Baseline **injected** cells, admissible probes only:

| task | n | gate opened | removal | preservation | harmful span named in `issues` | AC3 acc | Baseline acc |
|---|---|---|---|---|---|---|---|
| database | 80 | 78 | 77/80 (96.3%) | 2/80 (2.5%) | 66/80 (82.5%) | 57.5% | 13.8% |
| code | 46 | 46 | 46/46 (100%) | 3/46 (6.5%) | 33/46 (71.7%) | 78.3% | 76.1% |

Three things follow, and I am recording them before the remaining cells land so the interpretation
is not fitted to the final numbers:

1. **Removal is near-ceiling (96–100%)** — as expected for an editor that resets. On its own this
   is close to uninformative, which is exactly why the brief demanded preservation.
2. **The analyzer names the injected span explicitly in `issues` in 72–83% of conversations.** This
   is the part that is *not* explainable by "it deletes everything": a reset editor would score 100%
   removal while naming nothing. Flagging rate is the honest detection signal for a resetting editor.
3. **Preservation is very low (2.5% / 6.5%).** AC3-Reset discards the injected *true* span almost
   always. This is a real result and it partly contradicts the paper's "we preserve what's correct"
   framing — but it is uninterpretable until we know whether the true span was worth anything. That
   is what the factorial arms (`base_harm_only`, `base_use_only`, queued) are for: they measure the
   causal value of each span on an unedited context, with no detector in the loop. If the useful
   span's main effect is ~0 it is *true but inert*, and dropping it is not a defect.

Queued behind the matrix: (a) the detector-free factorial (Baseline x {clean, harm_only, use_only,
injected}), (b) an **AC3-Rewrite (S3)** arm, which compacts instead of resetting and is therefore
the natural control for "is the removal rate just an artifact of deleting everything?".
`experiment.strategy.analysis_cache_dir=null` is forced on the Rewrite runs — the shipped config
points at `outputs/analysis_cache`, built with a different model/prompt (RECON unknown #9).

---

## 4. Full 16-cell matrix complete (13:05). Headline numbers, and one surprise.

**Primary set: 126 conversations = 126 harmful + 126 useful spans.** All four positive controls
pass on exactly this set.

| | harmful (false by construction) | useful (true by construction) |
|---|---|---|
| **AC3 removed** | 123 | 121 |
| **AC3 kept** | 3 | 5 |

- **Pollution removal rate 97.6%** (123/126), 95% CI [93.2, 99.2]
- **Preservation rate 4.0%** (5/126), 95% CI [1.7, 9.0]
- **Edit precision 50.4%** (123/244)
- **Gate sensitivity 98.4%** (124/126 injected conversations opened the gate); clean-arm gate-open
  base rate 96.8%
- Harmful span **named explicitly in the analyzer's `issues`** in 78.6% (99/126); useful span
  named there (a false alarm) in 42.1% (53/126)
- Clean-arm spontaneous base rate for *both* anchor classes: **0.0%** — the probes never fire by
  accident, so removal is not inflated and preservation is not deflated by chance hits.

Per task: database removal 96.2% / preservation 2.5%; code removal 100% / preservation 6.5%.
Removal by injected type: `H_PHANTOM_COL` 95.5%, `H_PHANTOM_PARAM` 100%, `H_WRONG_EXEC_FACT` 100%,
`H_WRONG_TEST` 100%. Preservation by type: `U_EXEC_FACT` 2.5%, `U_TRUE_TEST` 4.2%,
`U_TRUE_SIG` 9.1%.

### The surprise: injecting the *pair* made the Baseline **better**, not worse

| arm | Baseline (full context) | AC3-Reset |
|---|---|---|
| clean | 27.8% (35/126) | 65.1% (82/126) |
| injected | 36.5% (46/126) | 65.1% (82/126) |

Baseline **+8.7pp**, AC3 **+0.0pp**. Reading that as "AC3 fails to protect" would be wrong: each
conversation got *both* a false span and a true one, and the true one carries real information
(a verified result value, a real public test case, the graded signature). On an unedited context
the true span's benefit outweighs the false span's damage. AC3, which drops both, is simply
**invariant** to injected assistant-side content.

AC3-clean and AC3-injected are not the same run in disguise: 7 conversations flip each way
(112/126 identical), i.e. ordinary sampling noise, and the injected anchor appears in the
analyzer's `issues` in 78.6% of injected conversations, so the analyzer demonstrably saw the
injection.

**Cache trap checked (RECON unknown #9).** `context_edit_v2_no_gate.yaml` sets
`analysis_cache_dir: outputs/analysis_cache` (1023 entries, shared with other agents running right
now). I read `strategies/analysis_cache.py`: the key is
`sha256(trace_message_hash + analyzer_model + prompt_version + spec_only + memory flags)` — it is
**content-addressed and model-scoped**, so (a) injected and clean conversations can never share an
entry, and (b) another agent's DeepSeek analyses cannot be served to my gpt-5.4-mini runs. Safe as
configured; I forced `analysis_cache_dir=null` on the AC3-Rewrite arm anyway because that config's
default cache predates this model.

This is precisely why the single-span factorial arms were queued. Running now.
