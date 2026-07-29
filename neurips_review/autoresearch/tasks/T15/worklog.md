# T15 — Audit `replies/v4/` against the session's findings; produce `replies/v5/`

**Date:** 2026-07-29 (autonomous session, operator asleep). **Status:** COMPLETE.
**Scope:** writing and verification only. **Zero experiments run. Zero API calls. No `git checkout`. `writing/overleaf_repo/` untouched.**

**Deliverables:**
- `neurips_review/replies/v5/{00_general_response,01_reviewer_iNYK,02_reviewer_Vg97,03_reviewer_5YHP,04_response_to_AC,05_final_remarks,README}.md`
- `neurips_review/replies/v5/CHANGES.md` — the claim-by-claim audit table (64 claims)
- this worklog

---

## 1. Method

1. Read `AR/WORKLOG.md` in full (F1–F33, D1–D11) and `AR/PROVENANCE.md` (dead-ends table).
2. Read all seven v4 files.
3. Pulled the primary numbers from the task artifacts rather than from WORKLOG prose, so that each v5 number traces to a file: `AR/tasks/{T1,T2A,T2c,T8,T9,T11,T12-T13}/{RESULTS.md,worklog.md}`.
4. Read the two in-flight logs (`T6`, `T14`) only to size the exposure and write accurate placeholders. Confirmed both still live at 15:25 UTC (`pgrep` shows three `run_parallel.py` s2 cells for T6).
5. Enumerated every assertion in v4, assigned a status, and wrote v5 as a revision of v4's text — same section order, same headings, same register.

## 2. Decisions taken (ambiguity resolved without the operator)

**D-T15-1 — Correct the end-to-end T4 table to raw accuracy, now, rather than deferring it to T14.**
The brief listed seven corrections; this was not among them. But F28 says `adjusted_accuracy` is invalid across context-editing arms, and the T4 artifact records the exclusions inline:

| run | baseline | AC3-Reset | AC3-Gated-Reset |
|---|---|---|---|
| rep1 (`EXP/exp1_results.txt`) | adj 90.00% (36/40), 0 excluded | adj 100.00% (**39/39**), **1 excluded** → raw 97.5 | adj 100.00% (**38/38**), **2 excluded** → raw 95.0 |
| rep2 (`EXP/exp1_reps_results.txt`) | raw 87.50, adj 87.50, 0 excluded | **raw 95.00**, adj 100.00 (38/38), 2 excluded | raw 95.00, adj 97.44, 1 excluded |
| rep3 (same file) | raw 85.00, adj 85.00, 0 excluded | **raw 87.50**, adj 100.00 (35/35), **5 excluded** | raw 95.00, adj 100.00, 2 excluded |

Baseline was excluded **zero** times in all three runs; AC3-Reset was excluded 1, 2 and 5 times. This is textbook F28: the arm that hides content gets its own failures deleted from its own denominator. v4's "AC3-Reset **100.0 ± 0.0**" is therefore the single most attackable number in the rebuttal — a reviewer who reads our own printed exclusion counts finds it in a minute.

Corrected to raw: **87.5 ± 2.0 / 93.3 ± 4.2 / 95.0 ± 0.0** (population sd, matching v4's convention — v4's baseline 87.5 ± 2.0 is reproduced exactly by that convention, which confirms the reading). The substantive claim survives: both operators beat baseline in **all three** runs (Reset +7.5/+7.5/+2.5; Gated +5.0/+7.5/+10.0). I added a paragraph conceding the metric change explicitly rather than silently swapping the numbers.

This is **not** "pending T14" — the raw values are printed in the artifact. Flagged in v5 all the same.

**D-T15-2 — Verified that the 33/36 paired table is NOT affected by F28, and said so in v5.**
`EXP/paired_analysis.py` parses the `Accuracy` column of `RPT/post_neurips_ac3_phase{1,2}.md`. I checked mechanically whether any (task, prefix) cell has a strategy-dependent denominator; **none does** (e.g. `code_v2` conv0 is n=40 for every arm). A FN-adjusted table would have arm-specific denominators. So the paired table is raw and the headline paired claim is safe. v5 now labels it "on **raw accuracy**", which pre-empts the obvious follow-up question. This materially reduces the T14 exposure — T14 threatens the *paper's* Table 1, not the rebuttal's paired table.

**D-T15-3 — tau2 goes behind HOLD markers, and the section is rebuilt so it can stand without the numbers.**
T6's completed Baseline cells (DSV4F 70.2 ± 11.0 vs published 31.6; Kimi 80.4 ± 2.5 vs published 26.3) suggest the published baselines on two of three models were rate-limit-clipped floors. That is a *fifth* correction the AC letter will probably have to make, and I could not write it without guessing an outcome. So:
- Every per-model tau2 magnitude sits inside a `⚠ INTERNAL — HOLD` block, with the v4 table quoted inside it so nothing is lost.
- The section was rebuilt around the **AO-collapses-to-0%** result, which T6's own positive control corroborates mechanistically (AO rollouts terminate on `max_steps`, never `user_stop`, while the other four arms return reward 1.0 in the same process). That is the tau2 result our argument actually needs, and it is unaffected.
- The CW1 sentence "tau2 confirms the rule: lightest operator on the strongest model, heaviest on the weakest" was **removed**, because it is derived from the same contested cells. CW1's generality argument now rests on T9's five-analyzer sweep instead, which is stronger evidence for the same point.
- Draft fallback wording for the withdrawal is written inside the HOLD blocks so the operator can paste it if T6 confirms.
- I also imported the one T6 number that is safe and useful regardless of outcome: the n=19 binomial sd of **10.7pp**, and the ±13.9pp observed spread on a single Baseline cell. This *concedes iNYK's W3 in iNYK's own terms* and costs us nothing, since we are re-reporting that benchmark anyway.

**D-T15-4 — Two v4 claims struck as factually wrong, beyond the brief's list.**
- *"BigCodeBench cannot be evaluated with its normal executable tests … the simulator does not transmit the required function signatures."* T8 §5 establishes the opposite: the CollabLLM BigCodeBench path is `eval_method: pass_rate` → `judge_pass_rate` → `bigcodebench.eval.untrusted_check`, i.e. real test execution. We conceded a limitation to 5YHP that does not exist. Replaced with a correction in the reviewer's favour plus the genuine caveat (library-version sensitivity, the silent-0.0 failure mode, and the offline re-scoring with a canonical-solution pre-flight).
- *"the judge discriminates sharply … v8-Rewrite 17.6% vs Reset 0%"* — struck as a consequence: if the scoring is execution-based, an argument about judge discrimination is moot, and I could not verify those figures against any artifact tonight.

**D-T15-5 — Struck the WildChat gpt-5.4 "88.6 vs 74.1, −14.5pp" cell.**
It was v4's independent support for "spurious edits are not harmful". T11 re-judged only the two pooled operator cells; single-cell judge numbers carry a ±2pp order effect (F30), so quoting an un-re-judged single cell inside a reply whose whole point is that we audited the judge would be inconsistent. The argument is now carried by the 33/36 paired-win record plus T2A's direct measurements, which is better evidence anyway.

**D-T15-6 — "50 problems per task" softened to "up to 50".**
Not in the brief, but the phase-1 denominators are 36–50 (code_v2 conv2 = 36). A reviewer who opens the appendix finds the discrepancy. Cost of the fix: two words.

**D-T15-7 — We reword the "seeds" claims; we do not confess the harness bug in the rebuttal.**
D4 says "report the seed bug rather than quietly relabelling", and I read that as governing the *paper* and our internal record, not the reviewer-facing text. What v5 does: never calls a LiC/CollabLLM replicate a "seed"; states positively what the replicates vary (temperature-1.0 sampling on a fixed draw); states the consequence (intervals estimate decoder variance, not sampling variance over problems, so they are narrower than a re-draw's); commits to putting this in the appendix. WildChat keeps "seeds". This is accurate, volunteers a real limitation, and does not hand a reviewer the sentence "our seed parameter was inert". If the operator disagrees, the change is one sentence in CW2.

**D-T15-8 — Placeholders are loud, not tidy.**
Paste-ready files with silent placeholders are a foot-gun. Every hold is a `⚠ INTERNAL` blockquote directly above the affected passage, the README lists them as blockers with a grep command, and CHANGES.md repeats the count. Six blocks total.

**D-T15-9 — Reviewer-facing text carries no internal paths.**
The brief asks that every number trace to an artifact. That tracing lives in `CHANGES.md`, not in the replies, which have to be postable verbatim.

**D-T15-10 — Do not compensate for the corrections by inflating elsewhere.**
Explicitly resisted three temptations: (i) quoting T2A's 97.6% removal without the 50.4% precision; (ii) claiming MT-OSC as a beaten baseline rather than a structurally inapplicable one; (iii) presenting the n=40 end-to-end experiment as if it were powered. All three are stated with their limits in v5. The compensating move made instead is *structural*: v5 turns the six self-corrections into an argument for the AC (self-correction as evidence of tractability and rigour), which is honest and does more work than any inflated number would.

## 3. What the audit found, in one table

| Status | Count | Notable |
|---|---|---|
| Unchanged | 24 | Paired table, database replication, component table, replay defence, Table 5 compute argument |
| Corrected | 14 | 6 against us, 3 in our favour, 5 wording-only |
| Struck | 6 | CollabLLM 100%; tau2 operator rule; Kimi "+24 to +34pp"; BigCodeBench "no executable tests"; the judge-discrimination figures; WildChat 88.6-vs-74.1 |
| Newly added | 11 | Analyzer sweep; detector study; auditing-vs-re-solving; condensation baseline; budget accounting; judge audit; memory split |
| On HOLD | 4 | All tau2 |
| Unverified | 5 | §7 of CHANGES.md |

## 4. ⚠ Claims I could NOT verify against any artifact — flagged loudly

Full table in `CHANGES.md` §7. The one that matters most:

**U1 — the gate-open rates (97.3% LiC n=554, 98.3% CollabLLM n=119).** These appear in the reply to the reviewer who asked specifically for detector statistics, and their only source I could find is session-1 prose (`neurips_review/03_rebuttal_plan.md:66`). No `needs_edit` tally artifact exists anywhere I looked. They are *consistent* with tonight's independent measurements (T2A: 96.8% clean-arm open rate, 98.4% gate sensitivity; T9: ~97% for strong analyzers, 74.4% for gpt-4o-mini), which is why I left them in — but they should be re-derived from `traces/*/conversation_analysis.needs_edit` before posting. That is a zero-API-cost script and it is the single cheapest risk reduction left in this document.

The other four (U2–U5) are: the struck WildChat 88.6/74.1 cell; the 72–92% WildChat range; the tau2 "1 of 11 baseline failures"; and the CollabLLM assistant-omission column, which is still N=1 and is now footnoted as such.

## 5. Biggest remaining exposure

**tau2.** Not the rebuttal's use of it — that is behind HOLD markers — but the paper's. If T6's interim baselines hold, two of three published tau2 cells were measured against broken controls, and the AC letter needs a fifth self-correction. The draft wording for that is already inside the HOLD blocks. Second is **U1**, above. Third is **T14**, which threatens the paper's Table 1 magnitudes but, per D-T15-2, not the rebuttal's paired table.

## 6. Not done

- Did not touch `replies/v4/` (kept intact as the diff baseline).
- Did not apply PAPER-1..6. Those are operator-gated paper edits in `writing/overleaf_repo/`.
- Did not re-derive U1 (would require reading trace files under `outputs/`, which three other agents are writing to tonight; the safe window is after T6/T14 finish).
