# T25 — Retract the Rewrite-selectivity attribution; assemble the counter-case

**2026-07-29, autonomous overnight session.** Operator asleep; no questions asked. **Zero API
calls, zero experiments** — every number below was recomputed from artifacts already on disk or
lifted from `T2B/RESULTS.md`. Writing task only.

**Inputs.** `AR/tasks/T2B/RESULTS.md` (F65–F67, commit `289de75`), `AR/tasks/T23/RED_TEAM.md`
(30 items, H1–H10 / M1–M15 / L1–L5), `AR/tasks/T2A/RESULTS.md`, `EXP/paired_analysis_results.txt`,
`RPT/post_neurips_ac3_phase{1,2}.md`, `OUT/T1/main/*/`.

**Baseline commit for all diffs: `d24a2db`.**

---

## Verdict up front

1. **The Rewrite attribution is retracted, not moved.** v5 said the paper's "we preserve what's
   correct and remove what's harmful" claim belongs to **AC3-Rewrite**. T2B measured selectivity
   causally on *naturally occurring* spans and **Rewrite keeps 0 of 66 probe-admissible spans**
   — worse than Reset's 5 of 66. The honest mechanism statement for **both** operators is
   **rebuild-from-the-user-side, not surgical excision.** Applied in five reviewer-facing places
   plus `README.md`, `CHANGES.md` and `HANDOFF.md`/PAPER-5.
2. **The counter-case is assembled.** A new subsection, *"Where AC3 separates from assistant
   omission, and where it does not"*, now sits under Common Weakness 2 in
   `00_general_response.md`, with a summary paragraph in `04_response_to_AC.md`. It follows the
   red team's four-move plan and leads with the concession (the matrix-wide head-to-head is a
   wash) so the regime-specific evidence is credible when it arrives.
3. **Nine red-team HIGH items actioned; H1 deferred to T24 by instruction.** H2, H3, H4, H5, H6,
   H7, H8, H10 applied. H9 recorded as a new `README.md` blocker with pre-drafted fallback
   wording, deliberately **not** applied to reviewer text because it is tau2-dependent and T6 is
   still running.
4. **All eight `⚠ INTERNAL` blocks are byte-identical.** Verified two ways (§6).
5. **One number in the brief was wrong and I printed the measured one instead.** The brief said
   "+21 pp over AO on database across three models". The measured value is **+18.7pp** (mean of
   9 paired triples). Printing +21 would have been a 2.3pp overstatement in our own favour, in a
   document whose entire theme is that a reviewer will check our arithmetic.

---

## 1. Part 1 — the retraction

### 1.1 What changed and why

| | T2A (constructed, injected spans) | **T2B (natural spans, causal)** |
|---|---|---|
| AC3-Reset | removal 97.6%, preservation 4.0%, edit precision 50.4% (chance 50) | keeps **5/66**, removal on harmful 100% (7/7), preservation 0% (0/4), edit precision 63.6% = base rate |
| AC3-Rewrite | removal 27.0%, preservation 38.9% → **looked selective** | keeps **0/66**, removal 100% (7/7), preservation 0% (0/4), edit precision 63.6% = base rate |
| Label path | injected spans, correct by construction | 111 spans × (14 present + 12 removed), 3,357 turns, **no detector, no judge, no LLM anywhere** |
| Aggregate test | — | Reset removed−kept = **−0.014, p = 0.85**; Rewrite not computable (kept nothing) |

**The reconciliation, which I made load-bearing in the reviewer text rather than leaving it to be
asked:** Rewrite looked selective on T2A's spans because they were short, self-contained
sentences anchored on a rare token, and a compacting operator can copy such a sentence across
verbatim. On the model's own verbose prose and code it paraphrases, and nothing distinctive
survives. **T2A flagged synthetic salience as an upper-bound caveat in its own first paragraph
and the caveat turned out to be load-bearing** — which makes T2B an *extension* of T2A, not a
contradiction of it. That framing is what stops a reviewer reading two studies as two
inconsistent results.

### 1.2 Not written up as a loss

T2B is presented as answering 5YHP's W5, including the part that cost us. The positive content
now in the reviewer text:

* **Natural pollution is real and concentrated.** SD of per-span effects **0.155** vs a
  replicate-matched parametric null's **0.125** (p = **0.0085**); **16** spans with |Δ| ≥ 0.25
  where the null predicts **9.3** (p = **0.0170**); mean effect over all spans **+0.020**
  [−0.010, +0.048] — the typical span is inert. This is the first causal characterisation of the
  phenomenon the paper is about.
* **AC3 removes 100% of causally harmful spans** (7/7, both operators), on conversations chosen
  without reference to what AC3 would do to them.
* All three controls pass: contentless span +0.033 (n.s.), T2A's validated pollutant +0.368,
  full-spec/gold-SQL span −0.447.
* Same-corpus raw accuracy: Baseline 39.3%, Reset 51.9%, Rewrite 53.1%.
* T2B's eight self-stated limits reproduced in the reply (per-span MDE 0.333 so 95/111 are
  *inconclusive* and inconclusive ≠ inert; useful spans under-detectable at low base rates;
  headroom-selected subsample; lexical probe so prose preservation is a lower bound, with the
  2×2 repeated on code spans alone; ~40% of spans unprobeable; one model / one analyzer / one
  replay turn; single-span ablation only).

### 1.3 Files changed for the retraction

| File | Change |
|---|---|
| `03_reviewer_5YHP.md` W5 | Largest edit. Reset's precision-at-chance reframed **"by construction"** (red-team M5) with the delete-everything control as its reference class; a volunteered disclosure that naming *precision* against non-injected spans was never measured (M14, partly closed for free); the full T2B block — design, three results, retraction, corrected mechanism, "what this does not withdraw", eight limits. Second `**Design.**` heading renamed to avoid a duplicate. Opening sentence changed to "we built it — twice — and it changed a claim in our paper and then changed our correction to that claim" |
| `02_reviewer_Vg97.md` Q4 | "Rewrite sits at the opposite corner — it is the selective operator" **deleted**. Replaced with a two-study bullet list and the same-mechanism-for-both statement; revision line now says *remove* the framing rather than re-attribute it |
| `04_response_to_AC.md` correction 3 | Rewritten as *"One sentence in the paper is wrong, and our first attempt to fix it was also wrong"* — the retraction is framed as a second self-correction, which is the letter's own tractability argument. Evidence table gains a T2B row and its detector row is corrected |
| `05_final_remarks.md` | Detector bullet expanded to cover both studies; correction 3 rewritten as a retraction |
| `README.md` | Concession-table row and detection guardrail rewritten; **"always attribute selectivity to Rewrite" removed**, replaced with "attribute selectivity to no operator" |
| `CHANGES.md` | Rows **3.11** and **4.16** rewritten (4.16 now labelled *"newly added — correction to a paper claim; RE-CORRECTED by T25"*); §8 cross-cutting rule 3 rewritten; new **§11** integration record; tally paragraph appended |
| `../../HANDOFF.md` | **Row 5** and the **PAPER-5** action rewritten. PAPER-5 previously read *"Restrict … to AC3-Rewrite"*; it now reads **"Delete … do not re-attribute"**, states the both-operator mechanism, and flags that the **ERGO differentiation argument changes too** — the difference is not "we are selective and they are not" |

---

## 2. Part 2 — the assembled counter-case

`RED_TEAM.md`'s closing objection: *v5's own concessions have quietly reduced AC3-Reset to
assistant omission plus a spec-extraction call, and the authors conceded every piece separately
without ever seeing it assembled.* The counter-evidence existed in four files. It is now in one
place, following the red team's four moves.

**Location:** new `###` subsection of Common Weakness 2 in `00_general_response.md` (chosen over
a new top-level "Common Weakness 6" so the five CW numbers cross-referenced from every other
file stay stable), plus a summary paragraph in `04_response_to_AC.md` before the corrections
list.

**Numbers, all recomputed by me tonight from `RPT/post_neurips_ac3_phase{1,2}.md` using
`EXP/paired_analysis.py`'s own row parser:**

| Task | Reset − AO, mean over triples | W / L / T |
|---|---|---|
| **database_v2** | **+18.7pp** | **8 / 1 / 0** |
| code_v2 | −3.8pp | 2 / 6 / 1 |
| math_v2 | −3.1pp | 1 / 7 / 1 |
| actions_v2 | −1.3pp | 4 / 3 / 2 |
| **all 36** | **+2.6pp** | **15 / 17 / 4** |

Cross-check: +2.6 = 15.9 − 13.3, the two printed rows. Per-model database pooled figures
reproduce `01`'s table exactly (Reset 72/147 = 49.0, AO 67/147 = 45.6, Baseline 33/147 = 22.4).

**The four moves as applied.**

1. **Paired, tested AO comparison in the general response** — done, *and it leads with the
   concession.* The matrix-wide head-to-head is +2.6pp on 15/17/4, i.e. a wash; I put that
   first, because a reviewer can derive it from the two printed rows and finding it themselves
   would discredit everything after it. The concentration (+18.7pp on database, 8 of 9) then
   reads as a finding rather than as cherry-picking. The math/code/actions negatives are printed
   alongside.
2. **Rewrite restored to the operator story** — the paired row is printed (H2) and Rewrite's
   evidence is pointed at WildChat (Kimi-K2.6/Rewrite 91.5% vs AO, labelled as a single-run
   n=59 cell). **Note the interaction with Part 1:** the red team wanted Rewrite restored as
   "the operator that actually *is* selective". T2B removes that role, so Rewrite's story is now
   thinner than the red team assumed — it is an operator-by-regime data point, not a
   selectivity exemplar. I did not paper over this.
3. **Preservation reframed as by-construction; detector section leads with detection and the
   causal work** — done in `03` W5 and `04` correction 3.
4. **"A decision procedure over operators indexed by referentiality, of which AO is correct in
   exactly one regime"** — stated explicitly in `00` and `04`. This is the move that is immune
   to the objection, because it *predicts* AO's successes instead of needing to beat them.

Also folded in: tau2's structural AO failure (0%, rollouts exhaust the step budget), WildChat's
every-populated-cell result with H7's corrected description, the factorial (9.3% → 59.8% with
the pollutant still present), and T2B's concentration + 100%-removal results.

---

## 3. Red-team items applied

| # | Severity | Status | What I did |
|---|---|---|---|
| H1 | HIGH | **DEFERRED — T24 owns it** | Three full-context baselines 52 points apart. Not touched by instruction; T24 is producing the reconciling clause. Recorded as `README.md` Blocker 5's sibling (Blocker 6a) |
| H2 | HIGH | **APPLIED** | AC3-Rewrite's paired row (−0.3pp, 6/6/0, n=12) printed in `00` CW2 with a dagger footnote: pre-analyzer-parity, one model, explicit "we do not claim Rewrite improves LiC accuracy", and the closing line *"we would rather show the operator that loses on LiC than present four operators and print the three that win"* |
| H3 | HIGH | **APPLIED** | Same dagger footnote explains Gated-Reset's 12-of-36. One deployment sentence now used in `00`, `01`, `02`, `03`: *always-on Reset where an intervention is cheap; Gated-Reset where an unnecessary edit carries state-disruption cost.* Removed "the configuration we recommend" (`00` CW5, `04` correction 5) and "our strongest operator overall" (`03` W5) |
| H4 | HIGH | **APPLIED** | (a) `03` W4: states the AC3 column is a per-row best, that **Rewrite** was not re-run on CollabLLM at N=3, and **withdraws rather than substitutes**. (b) `01` W1: gives **Gated-Reset**'s new database figure — the operator iNYK named — **49.7% (73/147)** on DSV4F, prefixes 44.9 / 49.0 / 55.1, against FC 22.4 and AO 45.6, computed tonight from `RPT/post_neurips_ac3_phase1.md`. (c) Selection rule stated in `00` CW1 and `01`: the 33/36 row is a **single fixed configuration**, not a per-cell maximum |
| H5 | HIGH | **APPLIED** | Defending sentences added to `00` CW2 and `04` correction 2: Table 1's 20/19/25/23 come from an arm-symmetric **pool-level pre-filter** applied before any method runs; the per-run metric touches ≤4 cells at ≤1 sample each, 2 of which favour prior work; what is withdrawn is the *reported statistic*, not the main table. This closes F62 — the biggest under-defended strength in the set |
| H6 | HIGH | **APPLIED** | `00` CW5 ERGO paragraph now applies the n≈20 standard to our own rows and points at the 36-comparison matrix as the headline evidence. **"every AC3 operator still clears the full-context baseline in every cell" deleted outright** — it is false globally (Table 2: AC3-Reset 47.0 vs Baseline 55.0 on gpt-5.4/CollabLLM) and breached our own guardrail |
| H7 | HIGH | **APPLIED** | `03` W1 now reads "four operators × four respondents, against **two** baselines, 22 populated cells … every populated cell favours AC3 — 13 against assistant omission and 9 against full context" |
| H8 | HIGH | **APPLIED** | `00` CW4 and `01` W3 now open with **"we do not have a defensible failure taxonomy for it"**, offer the reading as a hypothesis, and commit to a published rubric with a second annotator over all trials. Removes a claim that invited a demand for traces that no longer exist (F56) |
| H9 | HIGH | **RECORDED, not applied** | The "only method that improves over full context across the entire spectrum" sentence is tau2-dependent and sits outside every HOLD block. Reviewer text **deliberately unchanged** — nothing may pre-empt T6. Added as `README.md` **Blocker 5** with the pre-drafted *"remains **viable** in the stateful agentic setting"* fallback, ready to swap into `00`, `01`, `05` when T6 lands |
| H10 | HIGH | **APPLIED — new numbers, zero API calls** | AC3's own wall-clock recovered from `OUT/T1/main/*/experiment.log` first/last timestamps. 107 conversations, `max_concurrent: 5` verified identical in all six `config.yaml`s, arms run back-to-back on one machine (`db_baseline` ends 12:15:29, `db_summarize1` starts 12:15:30, and so on). Full context **578 s**; MT-OSC 587 s (+2%); **Gated-Reset 781 s (+35%)**; summariser-1 835 s (+44%); **Reset 1,051 s (+82%)**; summariser-2 1,214 s (+110%). Decomposed: most of the gap is **turn inflation** (6.9 vs 4.1 turns from `run_summary.json`), and **per turn** Reset is +9%, Gated-Reset +5%, summariser-2 **+19%**. Also restored the n=40 math numbers the old text dropped: FC 205 s, reflection 231 s, **Gated-Reset 266 s, Reset 547 s** (`neurips_review/worklog.md:102`) — the old paragraph quoted the control's 231 s and omitted AC3-Reset's 547 s, which is exactly the substitution the red team named |
| M5 | MEDIUM | **APPLIED** | "Edit precision at chance" now carries the by-construction frame in `03` W5 and `04` correction 3 |
| M14 | MEDIUM | **PARTLY APPLIED** | `03` W5 now discloses that naming precision against non-injected spans was never measured and points at the causal work as the better argument. The clean-arm naming rate itself would need a re-run of `T2A/measure.py` |
| L2 | LOW | **APPLIED** | The 554/547 sentence reworded to "the gate opened on 539 of 554 LiC conversations (97.3%); the analyzer ran on 547 turns and fired on 539 of them (98.5%)". Also fixed CollabLLM 629 → **628**/659 to match `CHANGES.md` claim 4.18 |

**Deferred, with reasons:**

* **`F-T24-1` — higher priority than several HIGH items and not mine.** T24 reports that
  `01_reviewer_iNYK.md` W2's sentence *"On the full, non-difficulty-selected pool"* is **false**:
  the 36-comparison matrix runs on `htn50_52_*`, which is explicitly baseline-failure-selected,
  with replay prefixes additionally weighted toward baseline failures. That sentence is the
  direct answer to iNYK's Q1. **It must be fixed before posting.** Left untouched to avoid two
  agents writing the same clause; recorded as `README.md` Blocker 6.
* **Need runs or re-analysis:** M11 (neutral-prompt condenser control never finished), M12
  (U-Fold on tau2 neither run nor mentioned), M6 (human validation — the third of 5YHP's three
  judge checks), M3 (bootstrap CI for the ±0.0 cells), M15 (clustered bootstrap for the sign
  test), M14's clean-arm naming rate.
* **Real but survivable, and several are tone judgements the operator may prefer to make:** M1
  (the self-correction count reads 3 / 5 / 7 / 10 across four files — note my edits did not
  change any count), M2 ("no per-benchmark tuning"; partly mitigated by the new
  observable-before-running selection rule in `00` CW1), M4, M7, M8, M9, M10 (the "since no
  reviewer raised…" clause to the AC), M13, L1, L3, L4, L5.

---

## 4. Things I changed my mind about while working

* **I nearly printed "+21pp over AO on database" from the brief.** Recomputing gave **+18.7pp**.
  A 2.3pp overstatement in our own favour, in the one document arguing that a reviewer will
  check our arithmetic, would have been self-defeating. Printed the measured value and flagged
  the discrepancy in `CHANGES.md` §11.2.
* **I decided to print the matrix-wide AO head-to-head (15 W / 17 L / 4 T) even though it is a
  loss.** The alternative — printing only database's +18.7pp — is precisely the H4 pattern the
  same red team flags, and the wash is derivable from two rows already on the page. Surfacing it
  makes the concentration argument credible and is what turns the section into the
  operator-by-regime thesis instead of a defensive list.
* **I reported AC3's wall-clock even though it is bad (+82%).** The alternative was to leave the
  reader with the control's 13%. Per-turn decomposition (+9%) is the honest mitigation and it is
  stated as a decomposition, not as a replacement for the headline.
* **I did not touch the H9 sentence.** It is tempting to pre-emptively soften it, but T6 is live
  and the standing instruction is that nothing pre-empts it. Pre-drafting the fallback in
  `README.md` gets the same protection at zero risk.

---

## 5. What a reviewer can now check that they could not before

* The fourth operator's paired row exists on the page (H2).
* Every arithmetic claim I touched reconciles: 22 populated cells = 13 vs AO + 9 vs FC (H7);
  11+1+0 = 12 of 36 is explained (H3); +2.6 = 15.9 − 13.3; database 73/147 = 49.7.
* AC3's own latency is reported, not a control's (H10).
* The FN concession has a stated boundary (H5).
* The ERGO paragraph no longer asserts orderings it has just called unresolvable (H6).

---

## 6. HOLD-block verification

Both checks run against `d24a2db`:

```
git diff d24a2db -- neurips_review/replies/v5/ | grep '^[-+].*⚠ INTERNAL'
  → only two ADDED lines, both my own §11.4 prose inside CHANGES.md. No removed HOLD line.

git diff d24a2db -U0 -- neurips_review/replies/v5/ | grep -E '^[-+]>'
  → empty. No column-0 blockquote line anywhere in v5 was added, removed or altered.
```

Stronger check — extract every `⚠ INTERNAL` blockquote per file and SHA-256 it, old vs new:

| File | blocks | result |
|---|---|---|
| `00_general_response.md` | 3 → 3 | **IDENTICAL** (`743afd85ffa8`, `cb6e8fe025ae`, `cd0fc826fc4c`) |
| `01_reviewer_iNYK.md` | 1 → 1 | **IDENTICAL** (`a6158d29e50b`) |
| `02_reviewer_Vg97.md` | 0 → 0 | — |
| `03_reviewer_5YHP.md` | 0 → 0 | — |
| `04_response_to_AC.md` | 2 → 2 | **IDENTICAL** (`b1bcaefcf4e8`, `9d2d8f4e874f`) |
| `05_final_remarks.md` | 2 → 2 | **IDENTICAL** (`3fc2a8224bbe`, `e6acef749673`) |

**All five tau2 HOLD blocks, both T19 renumbering notes and the `00` orientation preamble are
byte-identical. T6's outcome remains unknown and nothing in this task pre-empts it.**

Also confirmed: no `git checkout` was run, and `writing/overleaf_repo/` was not touched
(`git status` shows no entry for it).

---

## 7. Cost

**$0.00 in API spend. No experiments run.** All new numbers came from parsing files already on
disk: `RPT/post_neurips_ac3_phase{1,2}.md` (paired deltas, Gated-Reset database),
`OUT/T1/main/*/{experiment.log,config.yaml,run_summary.json}` (wall-clock, concurrency, turns),
`AR/tasks/T2B/RESULTS.md` (all T2B figures), `neurips_review/worklog.md` (n=40 math latency).
