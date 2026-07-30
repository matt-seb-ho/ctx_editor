# Entanglement Knob — Autonomous Work Log

**Effort started:** 2026-07-30 (overnight, autonomous)
**Owner:** Matthew Ho (asleep); executing agent: Claude (Opus 4.8)
**Origin:** `neurips_review/philippe_discusion.md` — mentor Philippe's proposal.

This is the running log for an overnight autonomous research effort. Newest entries at
the **bottom** of the Log section. Decisions are tagged `[DECISION]`. Artifact locations are
recorded inline. State files live under `state/`, structured logs under `logs/`.

---

## 0. The idea (one paragraph)

Rather than comparing many benchmarks and *inferring* an ordering of how "entangled" user
turns are with assistant turns, **build a simulator that exposes entanglement as an explicit
knob on a single benchmark**. Entanglement = how much a user's turn depends on / refers to the
assistant's prior response. At the *independent* extreme (standard Lost-in-Conversation), user
turns are self-contained and you can delete all assistant messages losslessly — unrealistic. At
the *entangled* extreme, user turns are phrased relative to the assistant ("no, reverse that",
"use the value you got") and are uninterpretable without the assistant message — realistic.
Philippe's thesis, which the eval should demonstrate: **(1)** dropping assistant messages only
works at low entanglement; **(2)** accumulative context management pollutes at all levels;
**(3)** a good method (decontextualize-then-edit) must work across *all* entanglement levels.

Connected concept: **decontextualization** (Choi et al., TACL 2021) — rewriting an utterance to
be self-contained. Entangling is the inverse operation (the eval knob); decontextualizing is
what a good method does (the fix).

---

## 1. Key facts established from the codebase (grounding)

- A **sample** = `{question, answer, task_id, shards:[{shard_id, shard}], task, full_spec_q,
  ground_truth_a}`. `full_spec_q` is the single-turn upper-bound version; `ground_truth_a` grades.
- **UserAgent** (`src/ctx_editor/agents/user_agent.py`) reveals ONE shard/turn, rephrasing it
  conversationally. Crucially the shard content is **independent of the assistant** — this is
  exactly Philippe's "independent communication" extreme (entanglement = 0).
- The user agent already has the full conversation string (`trace.get_conversation_string`) in
  its prompt, so **the assistant's prior turn is already available** at reveal time — entangling
  is a prompt/generation change, not a plumbing change.
- **Strategies already implemented** map cleanly onto the method axis Philippe wants to compare:
  - `baseline.py` (S0) = accumulate everything (no management).
  - `assistant_omit.py` = **drop ALL assistant messages** (Huang et al.) — the baseline Philippe
    predicts only works at entanglement=0.
  - `context_edit_v2.py` (S2) = our analyzer-driven context rewriting = candidate "good method".
  - `append_analysis.py` (S1), `summarization.py`, `context_compaction.py` = more baselines.
- Config is **Hydra**; user agent likely selected via a `user_mode/` config. Adding an
  `entangled` user mode with an `entanglement_level` param is the intended integration point
  (confirming via impl-map subagent).
- Smallest pilot data: `data/dev_math_subset.json` (23 samples), also dev_code/database subsets.

---

## 2. TODO (concrete, actionable)

Legend: [ ] todo · [~] in progress · [x] done · [DROP] dropped w/ reason

- [x] Read discussion + protocol; orient in codebase.
- [~] Write notes + TODO (this file) + `notes/` design docs.
- [~] Exploration subagents: concept design + implementation map (running).
- [ ] **Decide the knob operationalization** (ordinal levels 0..3 vs continuous fraction). Record
      as [DECISION].
- [ ] **Build `EntanglementUserAgent`**: given the shard intent + assistant prior turn, emit an
      utterance at the requested entanglement level that (a) conveys the shard intent faithfully
      and (b) depends on the assistant turn to degree = level. Structured JSON output like the
      existing agent (`response`, `shard_id`), plus optionally a `decontextualized` field.
- [ ] **Faithfulness guard**: the entangled utterance must decontextualize back to the shard
      intent. Add a validation/measurement step (LLM judge) that scores decontextualizability so
      the knob is *measured*, not merely asserted.
- [ ] **Config wiring**: add `user_mode/entangled.yaml` with `entanglement_level`; confirm the
      instantiation path selects it. Keep changes minimal, match existing `_target_` patterns.
- [ ] **Pilot**: one benchmark (math), few samples, matrix = {entanglement 0,1,2,3} ×
      {baseline S0, assistant_omit, context_edit_v2 S2} × 1 model. Record accuracy per cell.
- [ ] **Validation experiment**: measure decontextualizability at each level to prove the knob
      moves the intended variable monotonically.
- [ ] **Figure**: performance vs. entanglement level, one line per method — the figure Philippe
      described (columns = entanglement).
- [ ] **Analysis**: does the predicted matrix hold? Where does assistant_omit collapse? Does S2
      hold up? Write takeaways.
- [ ] **Write-up**: a self-contained `docs/` design + results doc; update `docs/index.md`.
- [ ] Commit incrementally (conventional commits).

---

## 3. Open decisions to make autonomously (don't block on Matthew)

- Knob granularity & exact level definitions → default to ordinal 0/1/2/3 (independent / light
  anaphora / references assistant values / pure relative op). Will finalize after concept agent.
- Which benchmark for the pilot → **math** (cleanest grading via `\boxed{}`, smallest subset,
  cheapest). Extend to code/database later if time.
- Which model → cheapest available that actually shows the LiC gap. Default gpt-4o-mini for user
  sim + assistant; revisit if the gap is too small to be visible.
- How much to spend → keep pilot tiny (a few samples × cells) first to de-risk plumbing, then
  scale the sample count once the pipeline is proven end-to-end.

---

## 4. Log

- **2026-07-30 (start):** Read `philippe_discusion.md` and the Deli autoresearch protocol.
  Oriented in codebase: user agent, simulator turn loop, shard format, available strategies.
  Confirmed the entanglement knob is fundamentally a user-simulation change and that the strategy
  axis for the comparison already exists (`baseline`, `assistant_omit`, `context_edit_v2`).
  Set up `research/entanglement/{state,logs,artifacts,src,notes}` and this worklog. Launched two
  exploration subagents (concept design; implementation map). Next: fold their outputs into a
  plan and start building the `EntanglementUserAgent`.

- **2026-07-30 (build):** Both exploration subagents returned strong outputs
  (`notes/concept_exploration.md`, `notes/impl_map.md`). Built the full stack:
  `EntanglementUserAgent` (4 ordinal levels; L0 delegates to stock LiC), prompt
  `prompts/entanglement_user_agent.txt`, `config/user_mode/entangled.yaml`, wiring in
  `run_experiment.py`, and provenance (`entanglement_level`, `decontextualized`,
  `revealed_shard_id`) recorded into trace metadata via a small simulator edit.
  `[DECISION]` Live path = TRAPI `gpt5_4_mini_trapi` + `load_balancer=trapi` via `az login`
  (no static API keys exist on this box; `.env` absent). Smoke test passed (e0==LiC, 100% on 1).

- **2026-07-30 (faithfulness fix):** Level-3 inspection (`artifacts/inspect_lvl3`) revealed the key
  methodological risk from concept §2: level-3 turns were *realized* (uninterpretable standalone)
  and their `decontextualized` self-reports were faithful, BUT the surface turns were too vague to
  be recoverable *even with* the assistant context ("triple it later on"), i.e. information loss ≈
  difficulty confound, not pure entanglement. `[DECISION]` Strengthened the prompt with a
  gold-pinned, competent-user model + an explicit **recoverable-with-context** self-check, and
  tempered the L3 instruction (elliptical-but-anchored, not vague). Built `recoverability.py` to
  *measure* informed vs blinded recoverability (judge = gpt-5.4-mini, a different family from the
  gpt-4o generator, per threat #3).

- **2026-07-30 (validation pass):** baseline (accumulate/S0) × entanglement {0,1,2,3}, N=5, dev_math.
  Accuracy: **e0=80% · e1=80% · e2=40% · e3=20%** (clean monotonic decline;
  `artifacts/val_baseline/`). Interpretation pending recoverability: a decline for *accumulate*
  (which sees everything) means either (a) faithful entanglement adds genuine reasoning difficulty,
  or (b) info loss. Running `recoverability.py` on L1-3 to distinguish. Fixed an async-client bug
  (AsyncOpenAI rejects a callable token-provider as `api_key`; resolve to a concrete bearer token).

- **2026-07-30 (recoverability result — KEY FINDING):** Ran `recoverability.py` on the dev_math
  validation traces. By level (informed / blinded / gap):
  **e1: 0.90 / 0.92 / -0.02 · e2: 0.71 / 0.81 / -0.10 · e3: 0.41 / 0.39 / +0.02**.
  This is the **difficulty-confound signature, NOT the entanglement signature.** Desired was
  *informed flat & high, blinded falling* (gap growing). Instead **both informed and blinded fall
  together** and the gap stays ≈ 0. Diagnosis: on LiC **math**, each shard is an *independent
  factual reveal* (e.g. "there are 3 more red than blue"); the assistant's prior turn contains no
  shared artifact the next shard can genuinely *refer to*. So when we crank the knob, the generator
  can only make turns **vaguer** (info loss), not **more dependent** — vagueness hurts informed and
  blinded equally. The recoverability instrument **correctly detected this** (validation-of-the-
  validator success: the knob is measured, not asserted, and the measurement caught a bad knob).
  `[DECISION]` **Pivot the benchmark, not the tactics** (Deli principle). Math shards can't carry
  faithful high-entanglement. Move to a benchmark with a **shared evolving artifact** the user turn
  can point into — **code** (named functions / enumerable steps / "the loop you wrote") and
  **database** (the query / columns / joins). Confirmed data is present: `data/dev_code_subset.json`
  (N=25, `sharded-HumanEval/105`, dev_code→code_v2) and `data/spider/databases/` DOES hold DBs
  (academic, advising, atis — earlier memory note was wrong). Next: rerun the validation pass on
  code and re-measure recoverability, looking for the *informed-flat / blinded-falling* signature.
  Hypothesis to falsify: code shards may ALSO be independent requirement-reveals — if code shows the
  same both-fall-together pattern, the finding becomes "faithful high-entanglement needs a
  purpose-built construction (deixis into assistant-enumerated content / explicit artifact edits),"
  which is itself the design contribution to bring back to Philippe.

- **2026-07-30 (why the retrofit can't work — mechanism):** Inspected the actual generated L3
  math turns (`val_baseline/lvl3`). The generator, told to be elliptical, *drops the shard's
  quantitative content* and replaces it with a pointer to nothing concrete: shard-2 gold "50 fruits
  at age 5" surfaced as "start earlier, that normal level" — the number 50 appears in **neither**
  the user history nor the assistant history (the assistant turn only holds a derived
  `**ANSWER: 2000**`). So the information is **destroyed, not relocated to the assistant turn** →
  both informed and blinded fall. Mechanism, stated crisply: **LiC shards specify relations among
  the problem's OWN quantities/requirements (age-6 = 3× age-5-baseline), which are independent of
  the assistant's DERIVED running answer. You cannot faithfully re-express such a shard as an
  operation on the assistant's output, because the assistant's output doesn't encode the shard's
  content.** A recoverability gap (blinded < informed) requires the intent's *content* to live in
  the assistant turn — which only happens for **selections among assistant-proposed options,
  callbacks to assistant-named entities, and corrections of assistant-produced artifacts.** That is
  a property of TASK STRUCTURE, not of phrasing. `[DECISION]` Reframe the deliverable: (a) the
  negative retrofit result (math+code) + (b) a positive *existence proof* that faithful entanglement
  IS constructible when intent routes through assistant-introduced referents, measured by the same
  recoverability instrument. Built `src/referent_demo.py` (12 templated referent seeds ×
  levels 0-3; templated on purpose so no generator is in the loop — removes the
  generator/recoverer self-validation threat and isolates the *construction*).

- **2026-07-30 (code validation):** baseline × entanglement {0,1,2,3}, N=5, dev_code.
  Accuracy **e0=20% · e1=60% · e2=60% · e3=20%** (`artifacts/val_baseline_dev_code/`; noisy at N=5,
  no clean trend — code standard-LiC e0 is already hard). Running recoverability on the code L1-3
  traces to check whether code's richer assistant artifacts (actual code) yield any informed-flat/
  blinded-falling gap vs math's terse numeric answers. Results pending (`recoverability/code_lvl*`).

- **2026-07-30 (RESULTS — the three-way story):** Both measurements landed.
  **Code recoverability** (`recoverability/code_lvl*`): L1 0.83/0.88/−0.05 · L2 0.66/0.71/−0.05 ·
  L3 0.60/0.63/−0.03. Informed and blinded fall together, gap ≈ 0 — **same difficulty-confound as
  math, in a different domain.** So the failure is about *independent-shard task structure*, not the
  math domain. **Referent existence proof** (`referent_demo/result.json`): L0 1.00/1.00/0.00 ·
  L1 1.00/0.96/+0.04 · L2 0.79/0.63/+0.17 · L3 0.83/0.42/**+0.42**. Informed stays high & ~flat,
  blinded **falls monotonically**, gap **grows** — **the desired signature.** Faithful entanglement
  IS constructible; it just requires the user turn's *content* to live in the assistant turn
  (selections / callbacks / corrections on assistant-introduced referents). Built the comparison
  figure (`recoverability/recoverability_figure.png`, 3 panels: math / code / referent) via
  `src/recoverability_figure.py`. `[DECISION]` Deliverable is complete as a research note:
  wrote `docs/entanglement_knob_findings.md` (proposal → instrument → negative retrofit result →
  positive referent result → reframed eval plan for Philippe), updated `docs/index.md`.

- **2026-07-30 (bottom line for Matthew/Philippe):** **Entanglement is a knob on task STRUCTURE,
  not phrasing.** You cannot retrofit it onto LiC's independent shards — the recoverability
  instrument (built here) proves the retrofit produces a difficulty confound, not dependence. The
  faithful knob requires a task where later user turns operate on assistant-contributed content
  (artifact-refinement / propose-then-select). Next concrete step: build that benchmark (deterministic
  gold) and run the method sweep (`omit_assistant` should collapse as the gap grows; `context_edit_v2`
  = decontextualize-then-edit should hold, since decontextualization is the inverse of the referent
  construction). `run_sweep.sh` + `aggregate.py` are ready for that sweep once the task exists.

- **2026-07-30 (Philippe's method figure — measured):** Rather than wait on a new gradable
  benchmark, measured the method comparison directly on the referent construction, using
  recoverability-vs-gold as an intent-survival proxy (`src/referent_methods.py`,
  `artifacts/referent_methods/`). accumulate = informed; drop-assistant = blinded;
  decontextualize-then-edit = rewrite-using-assistant then score blind. Result by level
  (accumulate / drop-assistant / decon-then-edit): e0 1.00/1.00/1.00 · e1 0.96/1.00/1.00 ·
  e2 0.75/0.63/**1.00** · e3 0.71/**0.33**/**0.88**. **Exactly Philippe's predicted matrix:**
  drop-assistant collapses with entanglement; decon-then-edit holds across all levels. `[NOTE]`
  Honest caveat recorded in the doc: recoverability isolates the drop-assistant failure ONLY; it does
  not price accumulation's pollution (accumulate looks fine here because it keeps everything). The
  full method comparison still needs a task-accuracy sweep on a gradable artifact-refinement task.
  This figure is the left half (drop-assistant unsafe under entanglement; our method fixes it).

