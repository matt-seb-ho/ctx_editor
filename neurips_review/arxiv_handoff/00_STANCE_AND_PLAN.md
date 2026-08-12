# AC3 — Stance & arXiv-Update Handoff

**Written:** 2026-08-03, at the close of the NeurIPS discussion period.
**Audience:** a fresh session whose job is to update the paper draft into an arXiv version that reflects everything we now have.
**This is the entry point.** Read it first, then follow the pointers. Do not re-derive edits that are already specified in `autoresearch/PAPER_EDITS.md`.

---

## 1. Current stance (where the project is)

The NeurIPS rebuttal is **done and posted**. All reviewer threads and the AC have been answered in the `replies/v6/` discussion-period comments (posted: `01` Vg97 followup, `03` final note to AC, `04` 5YHP detector-eval followup). Submission 27902 came in at 3× borderline-reject; Vg97 (Rating 3, conf 4) is the swing vote. Realistic posture: **rebut honestly, but plan for ICLR / arXiv** — outcome is uncertain and out of our hands now.

Substantively we are in a **stronger and more honest** place than at submission. During the rebuttal we (a) added the baselines reviewers asked for (matched-compute condenser, MT-OSC), (b) built the analyzer-as-detector evaluation with no judge in the label path (Tier A + Tier B), (c) scaled N and added paired statistics, and (d) corrected several of our own numbers against ourselves. The corrections narrowed some claims (notably tau2) but the **central LiC claim held under every metric variant we could construct**, and the mechanism is now characterized causally rather than asserted.

The job now: **land all of this in the paper `.tex`** so the arXiv version is consistent with what we told reviewers and includes the new evidence. Plant the flag before it goes stale.

---

## 2. What is now settled and public (the paper must match these)

The posted v6 replies are the binding public record. The arXiv draft must not contradict them.

- `replies/v6/01_reviewer_Vg97_followup.md` — matched-compute condenser baseline; MT-OSC reimplementation; unit-of-analysis (item-level McNemar); random-subset correction (87.5/93.3/95.0); **tau2 magnitude claim withdrawn**; "one method" reframed to **"at least one AC3 operator improves in every evaluated regime."**
- `replies/v6/03_final_note_to_AC.md` — the three-pillar summary (robustness/scale, baselines, pollution-measured-directly).
- `replies/v6/04_reviewer_5YHP_followup.md` — the detector eval (Tier A 97.6% removal; Tier B causal span ablation, 3,357 turns, removes 100% of causally-harmful natural spans); **mechanism stated as "detect, discard the assistant side, reconstruct the specification from the user side"** (rebuild, not surgical excision).
- Prior context: `replies/v5/` is a full unposted revision; its wording is vetted and reusable, but **v5 was never posted** — only v4 (initial) and the v6 followups are public.

---

## 3. The canonical claim set (what changed — do not regress)

These are the conclusions that moved during rebuttal. The arXiv draft must reflect the corrected form. Full location inventories are in `autoresearch/PAPER_EDITS.md`; this is the summary.

1. **tau2 improvement is withdrawn** (PAPER-11). Re-measured full matrix at N=3 (899 rollouts): two of three published baselines were rate-limit-clipped floors. Corrected baselines: DeepSeek-V4-Flash **31.6 → 70.2 ± 11.0**, Kimi-K2.6 **26.3 → 78.9 ± 0.0**, gpt-5.4 reproduces at **68.4**. With corrected baselines no AC3 operator beats full context on tau2. **What survives and should be the tau2 story:** (a) Assistant-Omission collapses to **0% on all three models, structurally** (exhausts the step budget; deletes tool state living only in assistant turns); (b) Gated-Reset holds parity (Δ −7 to −12pp, all p>0.14). Also disclose the unexplained gpt-5.4 AC3 cell (84.2 → 47.4 with baseline reproducing).
2. **Mechanism: rebuild, not surgical preservation** (PAPER-5). Retract "preserve what's correct and remove what's harmful" from abstract/intro. Tier B shows neither operator is span-selective (Reset keeps 5/66, Rewrite 0/66; preservation on useful spans 0%). Honest statement: AC3 **detects, discards the assistant side, and reconstructs the spec from the user side**; the gain comes from that rebuild.
3. **No universal "every operator beats baseline."** 6 sub-baseline cells exist. Correct claim: **best operator per cell**, and **"at least one operator improves in every evaluated regime."** Replace "the only method robust across the spectrum" with "improves over full context" phrasing.
4. **ERGO denominators corrected** (PAPER-7). ERGO was scored on unfiltered pools in `tab:main`; correcting raises the competitor (math 69.6 → **80.0**; code ≈43.9; database 12.0 unchanged; **actions uncorrectable — print as interval or drop**). This was the v5 posting-blocker; it must be applied before arXiv.
5. **Random-subset correction.** AC3-Reset was posted as 100.0 ± 0.0 (an FN-adjusted denominator artifact). Raw: **87.5 / 93.3 / 95.0**; both operators still ahead of full context every run.
6. **WildChat honest numbers.** Order-balanced after full re-judge with position-bias analysis: **Reset 87.8 ± 2.1**, **Augment 91.2 ± 2.1**; per-cell win-rate envelope **72–92%** quoted as a consistency check, not an effect range. "on the same prefixes" is false (PAPER-8) — 35 shared, McNemar p=0.125.
7. **CollabLLM.** Do not claim AC3 beats assistant-omission on BigCodeBench (margin inside noise). Claim: both beat full context. MATH-Hard AC3-Augment **matches** full context (not 100). BigCodeBench scored by real test execution, not a judge (correct the paper's statement); report the scoring environment.
8. **Memory demoted** (PAPER-3) to an optional, ablated add-on; contamination measured at zero; single-trial rows softened.

---

## 4. New evidence to fold in (strengthens the paper)

These did not exist (or were only promised) at submission and are now real, several of them posted:

- **Matched-compute condenser baseline.** A faithful per-turn condenser at matched budget does not close the LiC gap (database 47.7–53.3% vs 56.1%; AC3-Reset 75.7%), and by instrumentation over-consumed AC3 (1.02–1.19× calls, 1.62–2.14× tokens). Neutral-prompt variant reproduces (51.4%). Answers Vg97's #1 concern and the AC's "experimental evidence" pillar.
- **MT-OSC reimplementation** at published w=4 on LiC-database: 60.7% vs 56.1% (+4.7pp, p=0.383); a near no-op at LiC length (edits 6/107 conversations). Scoped evidence, not a verdict on its long-horizon regime.
- **Analyzer-as-detector, Tier A + Tier B** (5YHP W5, now posted). Tier A: constructed injection, ground-truth labels, removal 97.6%, names pollutant 78.6%. Tier B: causal counterfactual span ablation, no LLM in the label path, 111 natural spans / 30 conversations / 3,357 turns; natural pollution is real and **concentrated** (minority of spans), AC3 removes 100% of causally-harmful spans. Artifacts: `autoresearch/tasks/T2A/RESULTS.md`, `T2B/RESULTS.md`. This is the strongest evidence for the "validity of theoretical assumptions" pillar; give it its own subsection.
- **Analyzer robustness.** 5 analyzers across 4 model families, all positive (+12.9 to +39.9pp) with respondent held fixed — the shared component behaves as a shared component.
- **Statistics/scale.** Item-level McNemar **+15.4pp [+11.5, +19.4]** over 1,668 items; LiC scaled to n≈113–150/cell; 33-of-36 paired wins for always-on Reset.
- **Selection rule** to be made explicit in Section 3 (the AC/Vg97 generalizability ask): heavier operators for higher pollution / weaker models, lightest for strong-baseline stateful settings; keyed on baseline strength, observable a priori.

---

## 5. The authoritative edit spec — use it, don't reinvent it

`autoresearch/PAPER_EDITS.md` specifies **PAPER-1 through PAPER-11** with exact locations, current text, paste-ready replacements, finding IDs, and artifact paths. `autoresearch/HANDOFF.md` and `RESULTS_SUMMARY_2026-08-03.md` are the deeper background; `STATE_2026-08-03.md` is the running state; `PER_REVIEWER_CONCERNS.md` maps each concern to status.

**Status of each (from PAPER_EDITS status board):**
- Paste-ready mechanical: PAPER-7 (ERGO), PAPER-9 (difficulty disclosure), PAPER-1 (seeds limitations line), PAPER-8 (WildChat "same prefixes"), PAPER-3 (memory softening), PAPER-6 (false-neg appendix), PAPER-10 (optional caption).
- Closed / no paper edit: PAPER-4, PAPER-2.
- **Judgement calls needing Matthew:** PAPER-5 (mechanism retraction — 4 sites mechanical, 2 authorial), PAPER-11 (tau2 withdrawal — 25-location inventory, 3 authorial decisions). Do not attempt the PAPER-11 rewrite mechanically from that doc; it lays out options, not a single answer.

⚠ **Verify before applying.** `PAPER_EDITS.md` was written 2026-07-29 and states "nothing applied," but a 2026-07-09 honest-framing pass (inner-repo `ef40b01`) and a later overclaim-softening commit (`b1a629a`) did touch the `.tex`. **Diff the current `.tex` against each PAPER-N's "current text" quote first** to avoid double-applying or missing an edit.

---

## 6. Recommended order for the arXiv pass

1. Pull the paper repo, then diff current `.tex` against PAPER_EDITS "current text" quotes (§5 caveat). Establish what's already applied.
2. Apply the mechanical, paste-ready items: PAPER-7 (ERGO — highest priority; it's the one whose numbers a reader checks against the PDF), PAPER-9, PAPER-8, PAPER-1, PAPER-3, PAPER-6, PAPER-10.
3. Do the two judgement-call items with Matthew: PAPER-5 (mechanism = rebuild) and PAPER-11 (tau2 withdrawal).
4. Add the new-evidence subsections (§4): condenser + MT-OSC baselines; the detector-eval (Tier A/B) subsection; analyzer-robustness; item-level McNemar; the explicit selection rule in Section 3.
5. Reconcile Figure 1 art with the tau2 caption (see risks).
6. Final consistency sweep against the guardrails (§7) and against the posted v6 replies (§2).

---

## 7. Guardrails (numbers/claims not to reintroduce)

- Never "every AC3 operator beats baseline" → **best operator per cell**.
- tau2: no magnitude improvement claim. Canonical baselines are the **N=3 re-measured** values (§3.1). tau2 canonical = n=19 Azure Foundry sweep, not the older n=20 OpenRouter one.
- Kimi tau2: do not quote +47pp (clipped baseline).
- No "preserve what's correct" mechanism framing → **rebuild from the user side**.
- WildChat: order-balanced numbers only; 72–92% is a consistency envelope, not an effect range.
- No em dashes in prose the co-authors will read (house style this cycle).

---

## 8. Mechanics (paper-repo workflow)

- **Edit only** `writing/overleaf_repo/neurips/neurips_2026_conference.tex`. The `writing/neurips_project/` copy is stale; the `_v2.tex` is historical.
- `writing/overleaf_repo/` is a **separate git repo** (Overleaf-connected). Run all its git from inside: `git -C writing/overleaf_repo …`. **Pull before editing** (`pull origin main`) — Lianhui/Michel may have pushed. Conventional Commits. **Confirm with Matthew before pushing** (collaborator-visible on Overleaf).
- No LaTeX toolchain on this machine → not compile-checked locally. Overleaf remote has been intermittently unreachable — if `pull` fails, commit locally and note it.
- COLM equivalent if ever needed: `writing/overleaf_repo/colm/colm2026_conference.tex`.

---

## 9. Open items / risks

- **Figure 1 art** (`assets/ctxe_story.drawio.png`) may still draw AC3 ≈ vanilla at the tau2 end, which now contradicts the corrected tau2 caption — eyeball / redraw.
- **U-Fold** and a **high-pollution self-reflection arm** are still not run; both were committed for camera-ready. For arXiv, present as stated future work, not as done.
- **Gated-Reset "safe default"** line must be qualified — it loses to always-on Reset on strong-model text (WildChat gpt-5.4) and to baseline on tau2 gpt-5.4. Honest claim: best operator per cell, gated default only where the gate rarely closes wrongly.
- **Hyphenation** "Gated Reset"/"Gated-Reset" is mixed — deferred copyedit.
- **ERGO gating note:** in this session's AC note we deliberately withheld the ERGO-competitor-correction talking point pending the `tab:main` fix landing. For arXiv that gate is moot — apply PAPER-7 and let the corrected table stand.

---

## 10. Key artifact paths

- Posted replies: `neurips_review/replies/v6/` (public); `replies/v5/` (vetted, unposted); `replies/v4/` (initial, public).
- Edit spec: `neurips_review/autoresearch/PAPER_EDITS.md`. Background: `autoresearch/HANDOFF.md`, `RESULTS_SUMMARY_2026-08-03.md`, `STATE_2026-08-03.md`, `PER_REVIEWER_CONCERNS.md`.
- Detector eval: `autoresearch/tasks/T2A/RESULTS.md`, `T2B/RESULTS.md`.
- tau2 N=3 traces: `/home/t-matthewho/ac3/tau2_ctxe/ctx_edit/outputs/T6_reps/<model>_<arm>/traces/*.json`.
- Prior arXiv-push work: `docs/arxiv_push/` (worklog, debate, followup_experiments); `docs/jun1_megatable_findings.md`.
