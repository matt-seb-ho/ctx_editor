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

