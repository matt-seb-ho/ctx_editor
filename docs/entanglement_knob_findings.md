# Entanglement as a controllable knob: what it takes, and what it actually requires

**Status:** research note from an autonomous overnight build (2026-07-30).
**Origin:** Philippe's proposal in `neurips_review/philippe_discusion.md`.
**Artifacts:** `research/entanglement/` (code, worklog, raw metrics, figures).

## 1. The proposal

Our published work argues that LLMs *lose the plot* over multi-turn conversations and that you
can recover much of the single-turn performance by **editing the context** — surgically removing
the assistant's own erroneous, over-committed reasoning rather than accumulating it. A natural
skeptical question: *why not just delete all assistant messages?* That is the Huang et al. / ERGO
move, and it sometimes works. Philippe's insight is that whether it works depends on a hidden
variable we have never controlled: **entanglement** — the degree to which a user's turn depends on,
and refers back to, the assistant's prior response.

- **Entanglement = 0 (independent).** Every user turn is self-contained ("there are 3 more red
  marbles than blue"). This is exactly the *Lost in Conversation* (LiC) setup. You can delete all
  assistant messages *losslessly*, because no user turn points at them. Deleting assistant turns is
  a free win here — but this regime is unrealistic.
- **Entanglement = high.** User turns are phrased *relative* to the assistant ("no, reverse that",
  "use the value you got", "go with option B"). Delete the assistant turn and the user turn becomes
  uninterpretable. This is what real collaborative sessions look like.

Philippe's thesis, and the figure he wants: hold a single benchmark fixed, expose entanglement as
an explicit **knob**, and plot each context-management method as a line across entanglement levels.
The prediction: **(1)** drop-assistant only survives at low entanglement; **(2)** naive accumulation
pollutes everywhere; **(3)** a good method (decontextualize-then-edit) holds across *all* levels.

## 2. What we built

- **`EntanglementUserAgent`** (`src/ctx_editor/agents/entanglement_user_agent.py`) — a drop-in
  user simulator with an ordinal `entanglement_level` (0–3). Level 0 delegates to stock LiC. Levels
  1–3 rephrase the same shard with increasing reliance on the assistant's prior turn
  (light-anaphora → referential → relative-elliptical). Wired through Hydra
  (`config/user_mode/entangled.yaml`) and trace provenance (`entanglement_level`,
  `decontextualized`, `revealed_shard_id` recorded per user turn).
- **A recoverability instrument** (`research/entanglement/src/recoverability.py`) — the crux. For
  every entangled user turn it asks a *recoverer* LLM (a different model family, gpt-5.4-mini) to
  reconstruct the turn's stand-alone intent, then a *matcher* LLM to score that reconstruction
  against the gold shard. It does this twice:
  - **informed recoverability** = reconstruct given prior user **and assistant** turns → measures
    **faithfulness** (is the intent preserved and recoverable at all?). Should stay HIGH.
  - **blinded recoverability** = reconstruct given prior **user turns only** → measures
    **independence** (can you still recover it without the assistant?). Should FALL as entanglement
    rises.
  - **entanglement gap** = informed − blinded. A genuine, faithful knob makes this **grow**.

  The instrument is the whole point: it lets us *measure* the knob instead of asserting it, and it
  is what caught the failure below.

## 3. The negative result: you cannot retrofit entanglement onto independent shards

We ran baseline (accumulate) × entanglement {0,1,2,3} on **math** (`dev_math`) and **code**
(`dev_code`), then measured recoverability. Both benchmarks give the **same, wrong signature**:

| level | math informed | math blinded | math gap | code informed | code blinded | code gap |
|------:|:-------------:|:------------:|:--------:|:-------------:|:------------:|:--------:|
| 1     | 0.90          | 0.92         | −0.02    | 0.83          | 0.88         | −0.05    |
| 2     | 0.71          | 0.81         | −0.10    | 0.66          | 0.71         | −0.05    |
| 3     | 0.41          | 0.39         | +0.02    | 0.60          | 0.63         | −0.03    |

Informed and blinded **fall together**; the gap stays ≈ 0. This is the **difficulty-confound**
signature, not the entanglement signature. Cranking the knob does not make turns *depend on* the
assistant — it just makes them *vaguer* (destroys information), which hurts both recoverers equally.

**Why (the mechanism).** Inspecting the generated level-3 math turns makes it concrete. Shard-2's
gold is "a 5-year-old tree produces 50 fruits"; the level-3 surface turn was *"start earlier, that
normal level."* The number **50 appears in neither the user history nor the assistant history** —
the assistant turn only holds a *derived* answer (`**ANSWER: 2000**`). The information was
**destroyed, not relocated to the assistant turn**.

Stated generally: **LiC shards specify relations among the problem's own quantities/requirements
(age-6 = 3× the age-5 baseline), which are by construction independent of anything the assistant
computes.** You cannot faithfully re-express such a shard as an operation on the assistant's output,
because the assistant's output does not encode the shard's content. So the entangling generator has
only two moves, both dead ends:
1. keep the content in the words → no genuine dependence (blinded stays high, gap ≈ 0); or
2. drop the content and point at a referent → but the only available referent is the assistant's
   *derived* value, which does not carry the shard's content → the pointer resolves to nothing →
   information loss (informed **and** blinded fall, gap ≈ 0).

The instrument correctly flags both as non-entanglement. **This is a validation-of-the-validator
success: the knob is measured, not asserted, and the measurement rejected a bad knob.**

## 4. The positive result: faithful entanglement exists — it is a property of task *structure*

A recoverability gap (blinded ≪ informed) requires the intent's **content to live in the assistant
turn**. That only happens for a specific class of turns:

- **selections** among assistant-enumerated options ("go with option B"),
- **callbacks** to assistant-named entities ("the second column you proposed"),
- **corrections/edits** of an assistant-produced artifact ("drop the second helper call and return
  what came before it").

We built an existence proof (`research/entanglement/src/referent_demo.py`): 12 seeds, each an
assistant turn that *introduces a labeled referent* whose content equals a gold intent, plus four
**templated** surface turns (level 0 = full intent … level 3 = pure reference). Turns are templated
on purpose — the claim is about the *construction*, so no generator is in the loop (this also
removes the generator/recoverer self-validation threat). Same recoverability instrument:

| level | informed (faithfulness) | blinded (independence) | gap |
|------:|:-----------------------:|:----------------------:|:---:|
| 0     | 1.00                    | 1.00                   | 0.00 |
| 1     | 1.00                    | 0.96                   | +0.04 |
| 2     | 0.79                    | 0.63                   | +0.17 |
| 3     | 0.83                    | 0.42                   | +0.42 |

**This is the desired signature.** Informed stays high and roughly flat (the intent is always
recoverable *with* the assistant turn); blinded **falls monotonically** (without the assistant turn,
"go with option B" is unrecoverable); the gap **grows to +0.42**. Deleting the assistant turn here
is genuinely lossy — exactly Philippe's realistic regime.

*Robustness:* re-running with an expanded, more varied seed set (28 seeds: selections, ordinal/
pronoun references, corrections to specific artifact parts, callbacks to assistant-*computed*
values) preserves the signature — gap 0.00 → 0.05 → 0.21 → 0.23, blinded falling 0.95 → 0.41 while
informed stays higher (`artifacts/referent_demo_n28/`). Not an artifact of a dozen hand-picked cases.

![recoverability figure](../research/entanglement/artifacts/recoverability/recoverability_figure.png)

## 4.5 Philippe's method figure, measured on the referent construction

Once entanglement is *real* (the referent regime), context-management methods separate exactly as
Philippe predicted. Using recoverability-vs-gold as an **intent-survival** proxy, we score each
method per level (`research/entanglement/src/referent_methods.py`):

- **accumulate (S0)** = informed recoverability (assistant kept, referent resolvable);
- **drop-assistant (Huang/ERGO)** = blinded recoverability (assistant dropped, referent gone);
- **decontextualize-then-edit (ours)** = first rewrite the user turn to be self-contained *using*
  the assistant context (the inverse of entangling; Choi 2021), *then* drop the assistant and score
  the rewritten turn blind.

| level | accumulate | drop-assistant | decon-then-edit (ours) |
|------:|:----------:|:--------------:|:----------------------:|
| e0    | 1.00       | 1.00           | 1.00 |
| e1    | 0.96       | 1.00           | 1.00 |
| e2    | 0.75       | 0.63           | **1.00** |
| e3    | 0.71       | **0.33**       | **0.88** |

![method figure](../research/entanglement/artifacts/referent_methods/figure.png)

**Drop-assistant collapses** as entanglement rises (1.00 → 0.33): once the intent lives in the
assistant turn, dropping that turn destroys it — Philippe's prediction (1). **Decontextualize-then-
edit holds** across all levels (→ 0.88): it relocates the referent content back into the user turn
*before* the assistant is dropped, so the drop becomes lossless — prediction (3). This is the whole
argument for our method over naive assistant-omission, made quantitative. *(Robust at 28 seeds:
decon-then-edit 0.96/0.96/0.95/0.80 vs drop-assistant 0.95/0.93/0.57/**0.39**; `referent_methods_n28/`.)*

**Honest caveat about the axis.** Recoverability isolates the *drop-assistant* failure mode only. It
does **not** measure accumulation's pollution cost — that is why accumulate's line looks fine here
(its intent is trivially recoverable *because* it keeps everything). Accumulate's real weakness
(over-committed assistant reasoning polluting later turns) shows up on *task accuracy*, not on
recoverability. So this figure is the left half of the story (drop-assistant is unsafe under
entanglement, our method fixes it); the full method comparison still needs the task-accuracy sweep
on a gradable artifact-refinement benchmark (§6).

## 4.6 Judge-invariance, and the *right* discriminator

Everything above rests on one LLM judge (gpt-5.4-mini). Because the whole finding is instrument-
mediated, we re-scored both the negative (math) and positive (referent) constructions with a second,
independent judge family (**gpt-4o**, `RECOV_JUDGE_MODEL=gpt-4o_2024-11-20`). Two lessons:

1. **The *gap* (informed − blinded) is judge-sensitive.** Under gpt-4o the math retrofit even shows a
   small *positive* gap at levels 2–3 (a lenient judge scores the vague blinded reconstructions
   lower). So "gap > 0" is not, by itself, a clean judge-robust test — some retrofit turns *do*
   create a little genuine dependence ("triple *that*" pointing at the assistant's number), mixed in
   with a lot of information destruction.
2. **Faithfulness — informed recoverability staying HIGH — is the judge-robust discriminator.** It
   separates the two constructions the same way under both judges:

   | series | e1 | e2 | e3 |
   |---|:--:|:--:|:--:|
   | math informed, gpt-5.4-mini | 0.90 | 0.71 | 0.41 |
   | math informed, gpt-4o | 0.81 | 0.65 | 0.35 |
   | referent informed, gpt-5.4-mini | 0.98 | 0.79 | 0.64 |
   | referent informed, gpt-4o | 0.91 | 0.86 | **0.82** |

   The **retrofit destroys the intent** (informed decays to ~0.4 — unrecoverable even *with* the
   assistant, because the information was never anywhere); the **referent construction preserves it**
   (informed stays ~0.8 — always recoverable *with* the assistant, because the information was
   relocated there, not destroyed). Both judges agree on this contrast.

![judge-invariance figure](../research/entanglement/artifacts/recoverability/judge_invariance_figure.png)

**Refined statement of the finding:** a *faithful* entanglement knob is one that keeps informed
recoverability high while blinded recoverability falls. The primary, judge-robust certificate is
**informed recoverability (faithfulness)**; the gap is corroborating but noisier. Retrofitting onto
independent shards fails the faithfulness test (informed decays); the referent construction passes it.

## 5. Takeaway (the thing to bring back to Philippe)

**Entanglement is not a free rephrasing knob you can turn on any benchmark. It is a knob on task
structure.** It exists only when later user turns operate on content the *assistant* contributed —
selections, callbacks, corrections, edits to a shared artifact. This is *why* real coding/writing
sessions are entangled (you edit the artifact) and LiC's independent-shard tasks are not, and it is
why "just delete the assistant messages" is safe on LiC but catastrophic in practice.

Concretely, this reframes the eval we should build for the paper:

1. **Do not** retrofit entanglement onto `dev_math`/`dev_code` by rephrasing independent shards —
   the recoverability instrument shows it produces a difficulty confound, not entanglement.
2. **Do** build the sweep on an **artifact-refinement / propose-then-select** task, where a subset
   of user turns are generated *after* seeing the assistant's actual output and are phrased as
   operations on it. The referent construction above is the minimal template; the natural full
   version is a multi-turn code-editing task (the artifact is the code; turns are edits to it).
3. **Gate every entangled turn with the recoverability instrument** so the knob is *certified*
   faithful (informed high) and genuinely entangling (blinded falling), turn by turn — not assumed.

Only once entangled turns pass that gate does Philippe's method-comparison figure (drop-assistant
vs accumulate vs decontextualize-then-edit, across entanglement levels) measure what he intends. The
recoverability gap is the x-axis we actually control; task accuracy per method is the y-axis.

## 6. Open threads / next steps

- **Build the artifact-refinement benchmark** (deterministic gold, e.g. a list/string/code
  transformation pipeline, or reuse code with an explicit "edit the function you wrote" turn class)
  so the method sweep runs on turns that actually carry a recoverability gap.
- **Run the method sweep** (`baseline`, `omit_assistant`, `summarize_v1`, `context_edit_v2`) on that
  benchmark; `run_sweep.sh` + `aggregate.py` already produce the figure once the task is right.
- **Confirm the prediction**: `omit_assistant` should collapse as the gap grows; `context_edit_v2`
  (decontextualize-then-edit) should hold, *because* decontextualization is precisely the inverse of
  the referent construction (Choi et al., TACL 2021).
- **Scale N** beyond the N=5 validation pilots; current accuracy numbers are directional only.

## 7. Related-work positioning (from the context-management survey)

**Status:** added 2026-08-04 from the autonomous literature survey in `research/context_mgmt_survey/`
(42 papers, all citations verified; see that dir's `notes/` and `findings/`). This section answers the
question Matthew raised — *are we beating a strawman by centering on Huang's assistant-omit?* — and
supplies a drop-in related-work paragraph.

### 7.1 Verdict: not a strawman, but re-center the incumbent

Assistant-omit (Huang et al. 2026, `huang2026llmsbenefit`) is the clean *minimal* baseline, **not** the
foil the paper leads with. The production incumbent is **summarization/compaction** (shipped in the
Anthropic Compaction API, Cline auto-compact, Cursor `/summarize`), and the strongest *research*
compressor for stateful agents is **ACON** (`kang2026acon`, ICML 2026). Our contribution is the
**entanglement × statefulness two-axis knob** plus a **faithfulness gate**, and the unifying diagnosis
that every incumbent commits a lossy op (drop / evict / summarize / retrieve-key / archive / reset)
**before** resolving inter-turn references — *prune-then-hope* — whereas we *resolve-then-prune*
(decontextualize-then-edit).

Crucially, Huang's own paper motivates rather than opposes us. Verbatim from arXiv 2602.24287:

- It coins the problem: *"earlier assistant turns introduce errors, hallucinations, or stylistic
  artifacts that propagate into future turns. We call this phenomenon context pollution."* (§2.5)
- It quantifies the entanglement failure: *"follow-up without feedback for 33.1%"* of real WildChat +
  ShareLM turns (§2.3) — prompts that reference a prior assistant response without reproducing it, where
  blind omit hurts most.
- It concedes blanket omit is over-aggressive: *"Note that the third case requires storing only the
  relevant assistant turn."* (§2.4)
- It names our method as its own future work: *"A natural extension of this work is to develop a
  finer-grained approach for context filtering that preserves only the specific past assistant responses
  relevant to a given prompt."* (§3)
- It defers our statefulness axis: for *"multi-turn agentic systems, conversation context extends beyond
  user prompts and assistant responses to include intermediate artifacts, such as tool outputs, execution
  traces, retrieved files, and planning scratchpads … These additional outputs make context garbage
  collection an even more critical design problem."* (§4)
- It calls for our benchmark: *"the need for more carefully-curated real-world conversation benchmarks
  that reflect true multi-turn dependence."* (§4)

We build the eval that measures the two gaps Huang's authors explicitly flagged.

### 7.2 The two closest neighbors, and how we differ

- **ACON (`kang2026acon`)** — strongest *stateful* compressor; **fair comparator on the statefulness
  axis**, not a strawman (public code, AppWorld 56.5% vs 56.0% no-compression at ~26% fewer peak tokens).
  But it is *compress-then-hope*: it summarizes raw accumulated history / per-observation and relies on a
  **contrastive guideline optimizer** (a learned, distribution-dependent heuristic) to retain whatever
  cross-turn signal mattered on the *training* tasks. It never resolves inter-turn references before
  compressing. Our structural wedge: decontextualize-then-edit makes each retained segment self-contained
  *by construction*, so it holds on **novel** entanglement patterns ACON's guideline never saw. Orthogonal
  gap: ACON preserves whatever is in the history, including the assistant's *erroneous* committed
  assumptions; our analyzer specifically removes them. → distinguishing experiment: a high-coreference-
  density held-out split where ACON's learned guideline has no coverage.
- **StructFlowBench (`li2025structflowbench`, Findings ACL 2025)** — closest *scooping* risk; a 6-way
  **categorical** inter-turn taxonomy (Follow-up, Refinement, Recall, Expansion, Summary, Unrelatedness)
  scored by a GPT-4o judge on static "Golden Context." It does **not** do four things we do: (1) no
  *continuous/graded* entanglement dial (categories are nominal labels); (2) no *statefulness* axis (pure
  text history, no tools/env state); (3) no *faithfulness gate* on context edits; (4) no *context-strategy
  comparison* — it evaluates models' native ability under one fixed protocol and never ablates
  accumulate/omit/summarize/edit, nor measures task accuracy under pollution. Cite-and-distinguish.

### 7.3 Method axis for the accuracy sweep (updated)

`accumulate (S0)` · `omit_assistant (Huang/ERGO)` · `summarize_v1` (naive, production-representative) ·
**`summarize_guided`** (the O1 steelman: summarizer told to preserve every later-referenced referent +
all env state) · `context_edit_v2` (ours) · *[optional]* **ACON** on the statefulness axis. The
`summarize_guided` condition is the one objection (O1) that needs an experiment not an argument: it either
underperforms ours (generative summary can't guarantee verbatim referent/state preservation) or it
collapses into an un-instrumented resolve-then-prune (validating our mechanism). Already folded into
`docs/plans/entanglement_benchmark_spec.md`.

### 7.4 Drop-in related-work paragraph (draft)

> **Context management under multi-turn pollution.** Managing the conversational context to combat
> *context pollution* — the over-conditioning on earlier, often erroneous, model outputs
> [huang2026llmsbenefit] — has produced a spectrum of methods that we group by the lossy operation each
> commits: **dropping** assistant turns wholesale [huang2026llmsbenefit, khalid2025ergo]; **evicting** KV
> entries [zhang2023h2o, xiao2024streamingllm, li2024snapkv, cai2025pyramidkv]; **summarizing / compacting**
> the history [jiang2023llmlingua, pan2024llmlingua2, kang2026acon, kontonis2026memento]; **retrieving**
> salient turns on demand [packer2023memgpt, xu2025amem, chhikara2025mem0]; and **resetting** on an
> uncertainty signal [khalid2025ergo]. A recurring limitation unites them: each discards or compresses
> content *before* resolving how later turns refer back to it, so any inter-turn dependency that is
> elliptical ("reverse that"), stateful (an accumulated environment value), or otherwise not locally
> recoverable is silently severed. The conversational query-rewriting line [choi2021decontextualization,
> elgohary2019canard, anantha2021qrecc, wu2022conqrr] resolves such references, but only to build a
> one-shot retrieval key over a static corpus, discarding the resolution afterward. Benchmarks that probe
> multi-turn structure either treat inter-turn relationships as *categorical* labels for instruction-
> following compliance [li2025structflowbench, kwan2024mteval] or hold the shards independent by
> construction [laban2026lic], leaving the degree of dependence uncontrolled. We instead expose
> **entanglement** and **statefulness** as independently dial-able, faithfulness-gated axes on a single
> benchmark, and compare context-management strategies along them — resolving references *before* pruning
> (decontextualize-then-edit) rather than after.

*(Bibkeys resolve against `research/context_mgmt_survey/related_work.bib`, 42 verified entries.)*
