# Entanglement as a Knob: Concept Exploration

Status: design note (conceptual, no code). Author: overnight research agent, 2026-07-30.
Audience: Context Editor team. Related: `docs/project_motivation.md`, `docs/simulation.md`,
Choi et al. 2021 (decontextualization, TACL), Huang et al. 2026, Laban et al. 2025 (LiC).

---

## 0. The core construct in one paragraph

LiC makes multi-turn hard by *underspecification*: a full task is sharded and revealed one
shard per turn. But LiC shards are deliberately **independent** of the assistant — each shard is
a self-contained slice of the ground-truth spec, so you could delete every assistant message and
still reconstruct the task from the user turns alone. That property is *exactly* what lets ERGO
and Huang "win" on LiC by throwing away assistant messages (see `project_motivation.md` §2.3,
the "exploit problem"). Real conversations are not like this: users say "no, reverse that",
"use the value you got", "the second option". Those turns are **entangled** with the assistant's
prior response and become uninterpretable if you drop it. Philippe's proposal: stop treating
independence-vs-entanglement as an accident of which benchmark you picked, and instead make it a
**continuous, controllable axis on a single benchmark**. Then plot methods × entanglement levels.
The thesis falls out visually: drop-assistant collapses as entanglement rises; naive accumulation
is polluted everywhere; only decontextualize-then-edit holds across the whole axis.

**Key reframing.** Entanglement is the *dual* of decontextualizability. A user turn is highly
entangled iff it is hard to decontextualize (rewrite into a stand-alone form) without reading the
assistant turn. So we get the measurement instrument for free: **decontextualization-recoverability**
is our independent validator of the knob.

---

## 1. Operationalizing "entanglement level" as a controllable knob

We want a scalar/ordinal `e ∈ {0, 1, 2, 3}` (or continuous `e ∈ [0,1]`) that we *set* when
generating each user turn, and that we can *independently measure* after the fact to confirm the
generator actually produced turn-text at the requested level. Three candidate operationalizations;
I recommend a hybrid anchored on #1.

### 1.1 (RECOMMENDED) Decontextualization-recoverability gap

**Definition.** For a user turn `u_t` produced in context `H_t` (which includes assistant turn
`a_{t-1}`), define a *recoverer* R — a frozen LLM whose only job is: given `u_t` **without** the
assistant turns, produce a stand-alone paraphrase `û_t` of the user's intent. Entanglement is how
badly R degrades when the assistant turn is hidden:

```
e(u_t) = 1 - Recover(û_t^{-A}, s_t)     # -A = assistant-blinded recoverer
```

where `s_t` is the *original* ground-truth shard (the intent the turn is supposed to encode), and
`Recover(·, s_t) ∈ [0,1]` scores whether the blinded reconstruction still carries shard `s_t`'s
content. `e ≈ 0`: intent fully recoverable without the assistant (independent, LiC-like).
`e ≈ 1`: intent unrecoverable without the assistant (fully entangled).

**How to score `Recover`.** Two independent scorers, use both and report agreement:
- *Intent-match judge*: an LLM-judge asked "does `û_t` express the same task-relevant content as
  shard `s_t`?" on a 0–1 rubric. Cheap, but judge-noisy.
- *Answerability delta*: feed the assistant-blinded reconstruction into the actual task pipeline
  and measure whether the ground-truth answer is still derivable. This is the most honest metric
  because it grounds "intent preserved" in the task's own success signal, not a judge's opinion.

**Why recommended.** It directly measures the thing the paper is about (can you drop the assistant
and still know what the user wants?), it is model-agnostic, and it *is* the axis along which the
competing methods succeed or fail. The knob and the phenomenon are the same ruler.

### 1.2 Reference-resolution load (counting operationalization)

**Definition.** Count, per turn, the number of *cross-turn referring expressions that resolve into
the assistant turn* — pronouns, definite descriptions, deictics, elided arguments, and relative
operators whose antecedent/operand lives in `a_{t-1}` rather than in the user's own prior turns or
world knowledge. Normalize by turn length or clip to buckets.

```
e_count(u_t) = (# expressions resolving into assistant turns) [ / content-word count ]
```

**Independent measurement.** Run a coreference/discourse parser (or an LLM annotator with a fixed
schema) over the turn and tag each referring expression with its antecedent's *source*
(user-side / assistant-side / world). Entanglement = fraction pointing assistant-side. This gives
a linguistic, interpretable count that does *not* depend on task success, so it cross-validates 1.1:
if `e_count` and the recoverability gap disagree, the generator is doing something suspicious
(e.g., using assistant-referring words that are actually semantically vacuous).

**Weakness.** Counting is brittle: "double it" is a single short expression but catastrophic for
recoverability, whereas three resolvable pronouns may be harmless. So counts must be *severity-
weighted* (see taxonomy §3), which pushes you back toward 1.1 anyway.

### 1.3 Ablation-collapse of task success (behavioral operationalization)

**Definition.** Define entanglement of a *level* (not a single turn) behaviorally: run a fixed
reference assistant on the conversation twice — once with assistant turns present, once with
assistant turns replaced by a placeholder ("[response omitted]", à la Huang's AO) — and measure
the drop in final task accuracy attributable to blinding.

```
e_behav(level) = Acc(full) - Acc(assistant-blinded)      (at that generation level)
```

**Independent measurement.** This *is* a measurement, but it is downstream and confounded: it mixes
the intrinsic entanglement of the turns with the assistant's own competence. Use it as a **sanity
check on the whole level**, not as the per-turn knob. At `e=0` this delta should be ≈0 (blinding is
free — LiC territory); at `e=3` it should be large. If your generator claims high entanglement but
`e_behav ≈ 0`, the entanglement is cosmetic.

### 1.4 Recommendation

Use **1.1 as the primary knob and headline validator**, **1.2 as a cheap linguistic cross-check
that entanglement is realized in the surface form**, and **1.3 as a per-level behavioral audit**.
Generate turns *targeting* an ordinal level via prompt templates keyed to the taxonomy (§3), then
*verify* each generated turn's realized `e` with 1.1/1.2 and discard/regenerate turns that miss
their target band. This makes the knob **validated, not asserted** — which is the single most
important methodological point in the whole design.

---

## 2. The faithfulness constraint (why the eval is only valid if you nail this)

**The constraint.** Entangling a shard changes *only its interpretability/phrasing*, never its
*intent*. The ground-truth answer for the fully-assembled task must be identical whether the turns
were generated at `e=0` or `e=3`. Otherwise entanglement level is confounded with task difficulty
and every column of the result matrix measures a different problem — the comparison is meaningless.

**Concrete threat.** The lazy way to make a turn "refer to the assistant" is to let the turn's
meaning *depend on what the assistant actually said*. E.g., assistant proposes value 42; user says
"add ten to that". Now the intended number is 52 — but only because the assistant said 42. If the
assistant had said 40, the user "means" 50. The intent is no longer a fixed function of the shard;
it is a function of a *model output*, so ground truth is undefined. **This is fatal and must be
forbidden.**

**The fix — intent is fixed, reference is cosmetic.** Entanglement must be *anaphoric over form,
not compositional over the assistant's content*. Construction rule:

1. Fix the shard `s_t` and its stand-alone realization `u_t^{ind}` (the `e=0` version).
2. Build the entangled version `u_t^{ent}` so that a *correct-enough* assistant turn licenses the
   reference, but the **referent is pinned to the ground-truth entity**, not to whatever the
   assistant happened to output. The reference is a *pointer to a fact that is true regardless of
   the assistant*, phrased relative to the discourse.

Two safe patterns:
- **Correct-conditioned reference.** "reverse the string you just printed" is safe *only if* the
  string the assistant printed equals the ground-truth string; then reversing it yields a
  deterministic, assistant-independent target. Enforce by construction: entanglement is injected
  against a *reference (gold) assistant transcript*, and the referent expression resolves to a gold
  entity. If the assistant-under-test said something different, the pointer still denotes the gold
  entity (the *user knew* the right value), not the model's wrong one.
- **Self-referential-to-user-intent.** "the second constraint I mentioned" — points at the user's
  own prior shard, not the assistant. This is entanglement w.r.t. the *conversation* but keeps the
  ground truth trivially fixed. Lower severity, but a clean building block.

**Guarantee mechanism (do all three).**
1. *Generate against gold, resolve against gold.* Entangling templates are filled using the gold
   answer/entities, so the intended target is well-defined a priori.
2. *Faithfulness gate.* After generating `u_t^{ent}`, run an **oracle recoverer with the gold
   assistant transcript visible** and check it reconstructs `u_t^{ind}` (same intent as the shard).
   If the fully-informed recoverer cannot recover the original shard, the turn is *unfaithful* (it
   changed the intent) — regenerate. Contrast with the *blinded* recoverer of §1.1: gap between
   informed-recoverable (must be ≈1, faithfulness) and blinded-recoverable (varies with `e`,
   entanglement) is precisely the clean 2×2 we want.
3. *Answer invariance test.* Assemble the full task from `{u_t^{ent}}` and from `{u_t^{ind}}`;
   confirm the gold answer is identical and that an oracle solver with all turns + gold assistant
   context lands on it at both `e=0` and `e=max`. Any accuracy gap under oracle conditions = leak.

**Why critical.** Faithfulness is what separates this from "make the turns harder to read."
Without it, "entanglement" degenerates into "add difficulty/ambiguity," and Philippe's clean figure
becomes an artifact of difficulty scaling. The whole scientific claim ("a good method must be robust
to *entanglement specifically*, holding task fixed") rests on faithfulness being airtight.

---

## 3. Taxonomy of entanglement types (ranked by decontextualization severity)

Ordered low → high severity, where *severity* = how much intent is lost when the assistant turn is
hidden (i.e., how much it raises `e` in §1.1). Each maps to a generation template and to a Choi-style
edit that a *good method* would have to invert.

| # | Type | Example (user turn) | Referent lives in | Blinded-recoverable? | Severity |
|---|------|---------------------|-------------------|----------------------|----------|
| 1 | **User-side anaphora** | "the second constraint I mentioned earlier" | prior *user* turn | Yes (from user turns) | ★ low |
| 2 | **Discourse markers / cohesion** | "also, it should be case-insensitive" | discourse relation | Mostly (marker is droppable) | ★ low |
| 3 | **Assistant-entity reference (definite NP)** | "use the helper function you wrote" | assistant turn (named entity) | Partially | ★★ med |
| 4 | **Deixis / ordinal into assistant list** | "the third option", "that approach" | assistant turn (enumerated) | No (needs the list) | ★★★ high |
| 5 | **Pronominal anaphora to assistant** | "reverse it", "make that recursive" | assistant turn (pronoun) | No | ★★★ high |
| 6 | **Relative operations on assistant values** | "double the value you computed", "add a column to that query" | assistant turn (operand) | No (needs the base) | ★★★★ very high |
| 7 | **Corrections / repair ("no, I meant")** | "no — reverse that, I want descending" | assistant turn (polarity/scope) | No, *and* inverts prior state | ★★★★ very high |
| 8 | **Ellipsis over assistant structure** | "same but for the negatives" | assistant turn (elided predicate) | No (predicate is gone) | ★★★★★ extreme |

Notes for construction:
- Types 1–2 are the "warm-up" band: entanglement w.r.t. the *conversation* but trivially faithful,
  because the referent is user-side or purely rhetorical. Good for the `e=1` column.
- Types 3–5 are the heart of the phenomenon: the referent is an assistant-introduced entity or list
  position. These are where "drop all assistant messages" starts to break.
- Types 6–8 are the **money-shot generators** for the high-`e` columns and for corrections. Note
  type 7 (repair) is doubly important because it is *also* the LiC failure mode: the assistant
  anchored on a wrong assumption and the user is now correcting it. Entanglement severity and the
  pollution mechanism coincide here — this is the cell where the paper's thesis is most vivid.
- Severity ranking is w.r.t. **blinded recoverability**, which is what makes it the right ordering
  for building ordinal levels: pack low-severity types into low levels, high-severity into high.

**Building ordinal levels from the taxonomy.** Don't set entanglement per-type; set it per-turn by
*sampling from a severity-bounded pool*:
- `e=0`: all turns stand-alone (pure LiC; types none).
- `e=1`: mild — types 1–2 only.
- `e=2`: moderate — inject types 3–5 on ~half the turns that *can* carry them.
- `e=3`: heavy — types 4–8 wherever licensed, corrections (type 7) forced on turns that follow a
  premature assistant assumption.

---

## 4. The method side: decontextualize-then-edit vs. drop vs. accumulate

Three method families in the columns-and-rows figure:

- **Accumulate (S0 baseline).** Keep everything. Suffers *context pollution* at every entanglement
  level (the LiC/Huang finding): early wrong assumptions stay in context and anchor the model.
  Entanglement doesn't help or hurt it much — it's polluted regardless.
- **Drop-assistant (ERGO / Huang-AO).** Delete/placeholder assistant turns; keep user turns. Great
  at `e=0` (recovers Concat/single-turn, ~95% of Full — the exploit). **Collapses as `e` rises**,
  because the surviving user turns ("reverse it", "double that") are now *uninterpretable* — the
  referent it needed lived in the deleted assistant turn. This is the predicted diagonal collapse.
- **Decontextualize-then-edit (OURS).** Before pruning, *decontextualize* each entangled user turn:
  rewrite "double the value you computed" into a stand-alone "compute 84" (= 2 × the gold 42),
  resolving the reference against the (edited/verified) assistant content — then surgically remove
  the *harmful* assistant content while preserving the *decontextualized user intent* and correct
  partial work. Equivalent to Philippe's **"summarize-and-restart"**: collapse the conversation into
  a fresh self-contained instruction and continue in a clean context.

**What makes decontextualize-then-edit different from ordinary compaction/summarization?**
1. **Reference-resolving, not just compressing.** Generic summarization shortens text but preserves
   its *contextual* phrasing ("the user then asked to reverse it"). Decontextualization actively
   *resolves* the anaphora/ellipsis/relative-op into a stand-alone form ("the user wants the string
   'olleh'"). It is the *inverse operator* of the entangling generator in §3 — a clean adversary/
   defender duality. Ordinary compaction leaves entanglement intact (just shorter), so the compacted
   turn is *still* uninterpretable once you prune the assistant. Decontextualization removes the
   dependence itself, which is the only thing that makes subsequent pruning safe.
2. **Selective preservation, not wholesale drop.** Unlike ERGO/AO it keeps *correct* assistant work
   (valid sub-computations, right code skeleton) while removing wrong assumptions — the §3.1.2
   argument in `project_motivation.md`. So it cannot trivially recover Concat; gains must come from
   genuinely good edits.
3. **Faithfulness-checkable.** Because decontextualization has a well-defined correctness criterion
   (does the stand-alone rewrite preserve intent?), the edit is *auditable* — you can run the §1.1
   recoverer on the method's own output. Summarization has no such intrinsic correctness target.

The punchline: **decontextualize-then-edit is drop-assistant made safe by first paying off the
entanglement debt.** At `e=0` it reduces to drop (nothing to decontextualize) and matches the
exploit; at high `e` it is the only family that both removes pollution *and* keeps user turns
interpretable.

---

## 5. Predicted 2D result matrix (methods × entanglement)

Cells are qualitative accuracy predictions (H/M/L relative to single-turn Full). Columns are
entanglement levels; the task is held fixed (faithfulness §2).

| Method \ Entanglement | e0 (independent) | e1 (mild) | e2 (moderate) | e3 (heavy/corrections) |
|-----------------------|------------------|-----------|---------------|------------------------|
| **Single-turn Full** (ceiling ref) | H | H | H | H |
| **Accumulate (S0)** | L (polluted) | L | L | L (worst; anchors on repairs) |
| **Drop-assistant (ERGO/AO)** | **H (exploit)** | H– | **M ↓** | **L ↓↓ (collapse)** |
| **Naive summarize/compact** | H | M–H | M | L–M (entanglement survives compaction) |
| **Decontextualize-then-edit (OURS)** | H | H | **H–M** | **M–H (holds)** |

**Reading the matrix / the money shots:**
- **The drop-assistant diagonal collapse** (top-right of that row going H → L) is the central
  evidence that drop-based methods are *benchmark exploits*, not solutions. This single row kills
  the "just delete the assistant" narrative that LiC accidentally rewards.
- **The bottom-right cell (OURS @ e3)** is the paper's thesis in one number: the *only* method that
  stays high where turns are both polluted *and* entangled (esp. corrections, type 7). If this cell
  isn't clearly above drop-assistant and accumulate, the paper has no story.
- **The e0 column** is the credibility check: OURS must *tie* drop-assistant here (it reduces to it),
  proving we don't pay a tax for robustness; and drop-assistant must *win vs. accumulate* here,
  reproducing the known LiC exploit so reviewers trust the setup.
- **Naive-summarize row** exists to preempt "isn't this just compaction?": it should track OURS at
  low `e` but *fall off* at high `e` because compaction preserves entanglement (§4.1). The gap
  between OURS and naive-summarize at e3 = the value of *decontextualization specifically*.

---

## 6. Failure modes / threats to validity (and mitigations)

1. **Difficulty confound (the big one).** Entangling might make turns intrinsically harder, not just
   more assistant-dependent, silently scaling difficulty across columns.
   *Mitigation:* §2 faithfulness gate + oracle answer-invariance test; report oracle-solver accuracy
   per column (should be flat ≈ ceiling). If oracle accuracy drops with `e`, difficulty leaked.

2. **Entanglement is cosmetic (knob asserted, not realized).** Generator adds assistant-referring
   words that are semantically vacuous, so `e_behav ≈ 0` despite high requested level.
   *Mitigation:* §1.3 behavioral audit per level; require the assistant-blinded ablation to actually
   drop accuracy at high levels, else regenerate.

3. **Circularity between generator and validator.** If the same model family entangles and measures
   recoverability, you validate the generator against itself.
   *Mitigation:* use *different* models for entangling generator, blinded recoverer, and judge; add
   a small human-annotated audit set for `e` and faithfulness; report inter-scorer agreement (1.1
   judge vs. 1.2 count vs. 1.3 behavioral).

4. **Reference-to-a-wrong-assistant paradox.** If the assistant-under-test emits a *wrong* value and
   the next user turn says "double that," what is correct? The gold pointer (§2) says double the
   *gold* value; but a literal reader doubles the wrong one.
   *Mitigation:* pin referents to gold entities by construction; the user "knows" the right value.
   Document this explicitly — it is a modeling choice (the user is competent), and it is exactly the
   realistic case where the assistant must *reconcile* its wrong output with the user's grounded
   reference. Arguably a feature: it stresses the correction mechanism.

5. **User-simulator drift.** LiC's UserAgent rephrases shards conversationally already (`simulation.md`).
   Layering an entanglement generator on top may double-paraphrase and lose the shard.
   *Mitigation:* fold entanglement *into* the UserAgent as an extra conditioning variable (target
   level + prior assistant turn), not a post-hoc rewrite; re-run the shard-coverage check LiC already
   uses.

6. **Order/interaction effects.** Corrections (type 7) only make sense *after* a premature wrong
   assistant turn; you can't schedule them independently of assistant behavior.
   *Mitigation:* make high-`e` correction turns *reactive* — inject them conditionally when the
   reference assistant made an assumption — rather than at fixed positions. Keep a fixed RNG seed and
   log the realized schedule so columns are comparable.

7. **Ceiling/floor compression.** If Full is ~100% and Accumulate ~floor on the chosen task, columns
   can't separate methods.
   *Mitigation:* pick tasks with mid-range multi-turn accuracy (math/code from LiC are good); report
   both accuracy and LiC's aptitude/unreliability decomposition so effects show even under compression.

8. **Only one benchmark.** Single-benchmark design (the whole point) invites "does it generalize?"
   *Mitigation:* run the knob on 2 LiC tasks (e.g., math + database) as a robustness appendix; the
   *shape* of the curves (drop-collapse, ours-flat) is the claim, not absolute numbers.

---

## 7. What Choi et al. (2021) actually give us (and how to reuse it)

Their abstract page is thin, but the paper's operationalization (well-known) transfers directly:

- **Definition we adopt verbatim in spirit:** decontextualization = "taking a sentence together with
  its context and rewriting it to be interpretable *out of context* while *preserving its meaning*."
  Note the two clauses map exactly onto our two axes: *interpretable out of context* ⇒ our blinded-
  recoverability (§1.1); *preserving meaning* ⇒ our faithfulness constraint (§2). Choi already
  separates the two; we should keep them separate for the same reason.

- **Feasibility as a first-class label.** Choi annotate whether a sentence is
  **FEASIBLE / INFEASIBLE / UNNECESSARY** to decontextualize. This is *precisely* our entanglement
  ordinal in disguise: UNNECESSARY ≈ `e=0` (already stand-alone), FEASIBLE ≈ mid `e` (recoverable
  with edits), INFEASIBLE ≈ `e=max` (cannot be made stand-alone from available context). We should
  *report the feasibility distribution per generated level* as an external, human-interpretable
  validation that our knob lands where we claim. Borrow their label set outright.

- **Edit-type taxonomy → our entanglement taxonomy (inverse).** Their annotated edit categories —
  name completion, pronoun/NP-swap (coreference), bridging, discourse-marker handling, *global
  scoping* (prepend a scoping phrase), addition, deletion — are the *repairs* a decontextualizer
  performs. Our §3 entanglement types are the *damage* those repairs undo. Concretely: their
  "global scoping" edit ↔ our missing-scope deixis (type 4); "pronoun swap" ↔ our pronominal
  anaphora (type 5); "bridging"/"addition" ↔ our ellipsis (type 8). So our generator and our method
  can both be *specified in Choi's edit vocabulary*, giving a principled, citable basis rather than
  ad-hoc categories.

- **Evaluation practice to copy.** They evaluate rewrites with (a) automatic edit-overlap metrics
  (SARI-style, sentence match/length) and (b) human judgment of fluency + meaning preservation, and
  they show *downstream utility* (decontextualized sentences improve open-domain retrieval as
  stand-alone units). Our analogues: (a) recoverability score §1.1, (b) human faithfulness audit §2,
  (c) *downstream* = the actual task-accuracy matrix §5 — the strongest evidence, matching their
  "utility on a real task" argument.

- **One caution they teach.** Choi find a nontrivial INFEASIBLE fraction: some sentences *cannot* be
  decontextualized from their context. Implication for us: at extreme `e` (type 8 ellipsis, some
  type 7 repairs) a *turn in isolation* may be genuinely unrecoverable — but our method sees the
  *whole conversation*, not one turn, so it can still resolve references the single-sentence Choi
  setting cannot. Frame this as an advantage: multi-turn decontextualization has more context to
  work with than sentence-level decontextualization, so "INFEASIBLE-in-isolation" ≠ "INFEASIBLE-for-us."

---

## 8. Primary design recommendation (opinionated summary)

1. **One benchmark, one task family first** (LiC `math` or `code`), mid-range difficulty.
2. **Knob = 4 ordinal levels** `e∈{0,1,2,3}`, realized by folding an *entanglement conditioning
   variable* into the existing `UserAgent`, drawing from the severity-ranked taxonomy (§3), against
   a **gold reference assistant transcript** so referents pin to gold entities.
3. **Validate the knob three ways per generated turn/level:** blinded-recoverability gap (§1.1,
   primary), assistant-side reference count (§1.2, cheap cross-check), behavioral ablation-collapse
   (§1.3, per-level audit). Regenerate turns that miss their band.
4. **Enforce faithfulness with a gold-informed recoverer gate + oracle answer-invariance test**
   (§2). This is non-negotiable; it is what makes the columns comparable.
5. **Report feasibility distribution (Choi's FEASIBLE/INFEASIBLE/UNNECESSARY) per level** as an
   external validation of the knob.
6. **Five method rows:** Full (ceiling), Accumulate (S0), Drop-assistant (ERGO/AO), Naive-summarize,
   Decontextualize-then-edit (ours). The naive-summarize row is essential to prove ours ≠ compaction.
7. **The figure:** columns = `e0..e3`, one line per method. Success criterion = drop-assistant line
   collapses left-to-right, ours stays flat-and-high, accumulate flat-and-low, naive-summarize decays.
   Bottom-right (ours @ e3) and the drop-assistant collapse are the two cells the paper lives or dies on.

The elegance of the design is the duality: the **entangling generator** (§3) and the
**decontextualizing method** (§4) are inverse operators expressed in the *same* (Choi) vocabulary,
and the **knob** (§1.1) and the **method's own correctness check** are the *same* ruler. Build the
generator and validator once; the method and its audit come almost for free.
