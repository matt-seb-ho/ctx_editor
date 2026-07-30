# Plan: gradable artifact-refinement benchmark for the entanglement method sweep

**Status:** proposed (not yet implemented). **Prereq reading:** `docs/entanglement_knob_findings.md`.
**Why:** the recoverability results (that doc) show entanglement is a knob on *task structure*: it
is real only when later user turns carry intent *through* assistant-introduced content. We have an
existence proof (`research/entanglement/src/referent_demo.py`) and a method figure on the
recoverability axis. What is still missing is a **gradable** task so the *full* method sweep —
including accumulation's pollution cost, which recoverability does not measure — can run on
**task accuracy**. This plan specifies that benchmark.

## Design goal

A benchmark where (a) later user turns genuinely depend on the assistant's prior turns (so
drop-assistant is lossy), (b) the dependence is **faithful** (informed recoverability stays high —
gate every turn with `recoverability.py`), and (c) the final answer is **deterministically
gradable** (no judge needed for the headline metric). The entanglement level must be a **knob**, and
raising it must *not* leak task difficulty (the confound that killed the LiC retrofit).

## The task family: "propose → select/edit → resolve"

Each episode is a short multi-turn build on a shared artifact. Three roles as today
(`UserAgent`-analog, assistant, `SystemAgent` grader). Per turn:

1. **Assistant proposes labeled structure.** The assistant is prompted (or the turn is constructed)
   to surface a *labeled enumeration* — options `(A)/(B)/(C)`, numbered steps, named artifact parts.
   This is what creates referents. In natural coding turns this happens for free (named functions,
   numbered requirements); we make it reliable by asking for it.
2. **User turn references a label at the chosen entanglement level.** Level 0 states the intent in
   full ("use quicksort"); level 3 carries it purely by reference ("go with option B"). The gold
   intent is fixed; only the *surface form's reliance on the label* changes. This is exactly the
   referent construction, now generated live instead of templated.
3. **Deterministic resolution + gold.** The episode's ground truth is computed by applying the
   *sequence of gold intents* to a deterministic engine, independent of phrasing. Grading compares
   the assistant's final artifact to that gold.

### Concrete instantiation A — list/pipeline transforms (cheapest, fully deterministic)

- Seed: an initial list of integers (given in turn 1).
- Each subsequent turn selects ONE transform from an assistant-proposed menu and/or edits a prior
  choice. Transforms: reverse, dedupe, filter `>k`, sort asc/desc, take-first-`n`, map `*c`, drop
  index `i`, etc. The assistant each turn *enumerates* the applicable transforms as labeled options
  and echoes the current list.
- Entanglement: at level 3 the user says "apply option C to what you have and then undo the step
  from two turns ago" — uninterpretable without the assistant's enumeration + running artifact.
- Gold: apply the gold transform sequence to the seed list in code → exact-match grade on the final
  list. **No judge needed.**
- Difficulty control: hold the *number and kind* of transforms fixed across entanglement levels;
  only the *phrasing/reference density* varies. This is what prevents the difficulty confound —
  verify it by checking informed recoverability stays flat across levels (it must, by construction).

### Concrete instantiation B — code refactor chain (more realistic, judge-lite)

- Seed: a base function. Each turn = an edit referencing an assistant-named entity ("make the helper
  you added recursive", "the second branch should return None"). Assistant echoes the current code.
- Gold: a reference final function + a small hidden test suite; grade by running the tests
  (deterministic). Edits chosen so the reference passes and common misreadings fail.
- Higher fidelity to the paper's coding setting; more authoring effort than A.

**Recommendation:** build **A first** (a day of work, fully deterministic, isolates the mechanism),
then **B** if A shows the predicted method separation.

## What to measure

Run `run_sweep.sh` with `METHODS="baseline omit_assistant summarize_v1 context_edit_v2"` × levels
{0,1,2,3} on the new task. `aggregate.py` already emits the matrix + `figure.png`. Predictions
(now with a real gradable y-axis, not just recoverability):

- **omit_assistant**: fine at level 0, **collapses** as level rises (referents destroyed).
- **baseline (accumulate)**: degrades from *pollution* as turns accumulate — the failure mode
  recoverability could not see. Should now be visible on accuracy.
- **context_edit_v2 (decontextualize-then-edit)**: holds across levels — it resolves references
  against the assistant turn *before* editing/dropping, so it neither loses referents (unlike
  omit) nor accumulates pollution (unlike baseline). This is the paper's headline.

## Faithfulness gate (do not skip)

Every generated entangled turn must pass the recoverability instrument **before** it enters a
scored episode: keep a turn only if informed recoverability ≈ 1 (faithful) and, for level ≥ 2,
blinded recoverability is meaningfully lower (genuinely entangled). Report *informed recoverability*
as the faithfulness certificate (it is judge-robust; the raw gap is not — see findings §4.6).
Regenerate or down-level turns that fail. This is what makes the knob *measured*, not asserted, and
it is the methodological contribution.

## Build checklist

- [ ] `data/entangle_pipeline_subset.json` — N≈30 episodes, seed list + gold transform sequence per
      episode (instantiation A). Deterministic gold via a tiny transform engine.
- [ ] Transform engine + exact-match evaluator (a `task=...` config + evaluator, following the
      v2-evaluator pattern in `config/task/*_v2.yaml`).
- [ ] Extend `EntanglementUserAgent` to the propose-select setting: read the assistant's labeled
      enumeration from the prior turn and phrase the gold transform at the requested level as a
      reference into it (it already has the assistant turn; add label-extraction + reference
      templating; reuse the level ladder).
- [ ] Assistant system prompt that reliably enumerates labeled options and echoes the running
      artifact (so referents exist every turn).
- [ ] Faithfulness gate wired in (call `recoverability.py` scoring per turn; drop/regen failures).
- [ ] Run `run_sweep.sh` × 4 methods × 4 levels, N≥30, ≥3 seeds; `aggregate.py` for the figure.
- [ ] Write results into `docs/entanglement_knob_findings.md` (new §7) + a `docs/reports/` entry.

## Open design questions for Matthew / Philippe

1. **Deterministic-A vs realistic-B first?** (Recommend A — isolates the mechanism cleanly, no judge
   variance in the headline number.)
2. **Entanglement level as ordinal 0–3 (current) vs a continuous reference-density fraction?** The
   figure Philippe sketched has discrete columns, so ordinal is fine; continuous would let us plot
   a smooth curve if we want the crossover point where omit_assistant overtakes/undershoots.
3. **Should the assistant enumeration be model-generated (realistic, adds variance) or
   template-fixed (clean, less realistic)?** Suggest template-fixed enumerations for A, model-
   generated for B.
