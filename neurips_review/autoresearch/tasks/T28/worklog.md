# T28 — Apply T27's verified wordings; inoculate `RED_TEAM.md`; land the T6 tau2 withdrawal

**2026-07-29, autonomous overnight session.** Operator asleep; no questions asked; **zero API
calls** (this was a writing task throughout). Scope grew mid-task: the orchestrator routed **T6's
landing** here rather than dispatching a second agent, because two writers on `replies/v5/` is the
double-write pattern that corrupted output directories earlier in the session.

**Inputs:** `tasks/T27/worklog.md` §6 (the drop-in specification), `WORKLOG.md` F74–F77 and D20,
`tasks/T23/RED_TEAM.md`, `tasks/T6/worklog.md`, `replies/v5/{CHANGES.md,README.md}` and all six
reply files.

**Outputs:** `replies/v5/` (six reply files + `CHANGES.md` + `README.md`), annotated
`tasks/T23/RED_TEAM.md`, this worklog, and `hold_baseline.txt`.

**Compliance:** no `git checkout`; `writing/overleaf_repo/` untouched; no experiments, no API
calls, no `outputs/` writes.

---

## 0. Verdict up front

1. **All eight of T27's resolved items are applied**, using T27's §6 wording, with two
   adaptations recorded in §3 below.
2. **`RED_TEAM.md` is inoculated.** Its two measured-false suggested fixes (M3's cache clause,
   M11's budget-mechanism sentence) now carry inline `⚠ SUPERSEDED — DO NOT APPLY` notes with the
   correct measured answers; the originals are kept. A top-of-document banner states the D20 rule.
   Three further items (M12, M15, M6) got shorter `✅ RESOLVED` notes so the document stops reading
   as an open to-do list, and M15's own factual error about where the item-level data lives is
   corrected in place.
3. **T6 landed and it goes against us. The tau2 improvement claim is withdrawn.** All five
   `⚠ INTERNAL — HOLD` blocks and both `⚠ INTERNAL — T19 renumbering` notes are resolved and
   removed. Red-team **H9** is closed by applying README Blocker 5's pre-drafted fallback.
4. **HOLD verification is in two phases and both are recorded** (§5). Phase 1: per-block SHA-256,
   all nine regions byte-identical through the T27 pass. Phase 2: deliberate, instructed unsealing.
5. **Three reconciliations were needed**, not one. §3.

---

## 1. Part 1 — T27's items, as applied

| Item | Applied to | Note |
|---|---|---|
| **M11** — neutral-prompt condenser | `00` CW5 (replaces the "did not finish in the window" concession), `02` Q1, `04` addition table (new row), `05` condensation bullet, `00` "Summary of New Evidence" item 4 | Verbatim from T27 §6.5 except the second paragraph — see §3.1 |
| **M11 (b)** — budget ordering | `00` CW5, `02` Q1 | Reframed from a withdrawal to a "do not read this as a mechanism" note — see §3.1 |
| **M12** — MT-OSC w=2 | `00` CW5 (paragraph **and** a new `MT-OSC (w=2)` row in the results table), `02` Q1, `04` MT-OSC row, `05` condensation bullet | The `04` and `05` one-liners previously rested on "structurally cannot engage" alone; both now lead with the measured w=2 result |
| **M12 (b)** — U-Fold offer | `02` Q1 | Verbatim from T27 §6.6 |
| **M15** — item-level + clustered CI | `00` CW2 (full five-row table), `02` Q2 (full table — Vg97 is who asked), `01` Q2 (one-line version), `04` addition table, `05` paired bullet | Verbatim from T27 §6.2 |
| **M15 (b)** — AO head-to-head | `00` CW2 AO subsection, `04` AO paragraph, `05` paired bullet | Guardrail enforced — see §2 |
| **M3** — the `95.0 ± 0.0` cell | `00` CW3, `01` Q1 | Measured answer only; the proposed cache clause is **not** written anywhere |
| **M6** — human validation | `03` W4, as a new bullet after the temperature disclosure | Verbatim from T27 §6.4, undressed |

**M11's "0/340" is the sentence carrying that item**, not the 51.4%. It is in `00` CW5, `02` Q1
and `04`'s table row. A summariser does not audit whatever you instruct it to do; that is why
deleting the clause changes nothing, and it is a better answer to the fairness objection than a
2pp move would have been.

## 2. The M15 guardrail, carried into three places

**Never quote the matrix-wide AC3-vs-AO item-level McNemar (p = 0.010) as a win.** It treats
1,668 items as independent when they are 191 problems x up to 9 correlated replicates. Enforced:

* **In the reply text** — `00` CW2, `04` and `05` all print the clustered interval
  **+2.8pp [−0.3, +5.9]** with the explicit "not distinguishable from zero, which is why we do not
  claim it", and the database interval **+18.6pp [+10.7, +26.6]**. The p-value appears nowhere.
* **In `CHANGES.md`** — new cross-cutting rule **6b** in §8, plus a row in §12.1.
* **In `README.md`** — a new accuracy guardrail bullet.
* **In `RED_TEAM.md`** — inside the M15 resolution note, since that is where a future reader
  would go looking for the statistic.

**Consistency with the CW2 subsection a teammate already wrote (T25 §11.2):** checked directly.
That subsection says the matrix-wide head-to-head is "close to a wash" at **+2.6pp, 15 W / 17 L /
4 T** (cell level) and concentrates the separation on database at **+18.7pp, 8/9**. T27's
item-level pass gives **+2.8pp** and **+18.6pp** — the same conclusion from an independent data
path, agreeing within rounding. **The two do not disagree, and the new paragraph is worded to say
so rather than to present a second number for the same quantity.** Had I quoted p = 0.010, they
*would* have disagreed: T25's text says "wash", the p-value says "significant".

## 3. Places where two sections needed reconciling

### 3.1 M11's second paragraph — v5 never made the claim T27 proposed withdrawing

T27 §6.5 drafts "**Second, we withdraw the budget ordering we previously drew from this table.**"
I checked all six reply files (`grep -rn "more budget|degrades with|budget ordering"`): **v5 does
not assert a budget-degradation mechanism anywhere.** It prints −2.8 and −8.4 as two table rows
and says only "summarisation moves accuracy down". The claim T27 is withdrawing is one the *red
team proposed adding* (M11's suggested revision), not one we posted.

Posting "we withdraw the ordering we previously drew" would therefore describe an internal
deliberation the reviewer never saw, and would read as confessing to something we did not print.
**Adapted:** the substance is kept in full — replicate value, both p-values, the ±6pp floor, and
the "neutral-to-negative at either budget" conclusion — but framed as *"a note on the two budget
rows, because the ordering in them is tempting to read as a mechanism and we do not think it
survives"*. Nothing is softened; the reviewer is still handed the replicate that kills the reading.

### 3.2 "This experiment alone is not powered for significance" vs. a p = 0.023

M3's bootstrap puts AC3-Gated-Reset at **+7.5pp [+1.7, +15.0], p = 0.023** — which sits directly
beside a sentence in `00` CW3 (and its twin in `01` Q1) reading "this experiment alone is not
powered for significance". As printed those contradict each other. Both are reworded to *"we do
not rest our headline significance on it"*, which is true, keeps the modesty, and does not deny
the interval we just printed. T27 §3.3 anticipated the tension; this is the minimal fix.

### 3.3 Correction counts, and the two renumbering notes

The tau2 withdrawal is a genuine numbered correction, so `04` goes 5 → **6** and `05` goes 7 → **8**
— **exactly the numbering both `⚠ INTERNAL — T19 renumbering` notes predicted**, which is why they
are discharged rather than carried forward. `04`'s lead sentence moves from "five corrections …
four move against our own numbers" to "six … five move against our own numbers". `README.md`'s
concession count moves ten → **eleven** and its rhetoric-plan paragraph seven → **eight**.
Red-team **M1** (the count reads 3 / 5 / 7 / 10 across four files) is *not* closed by this and I
did not attempt it — it is a deliberate tone judgement the operator may want to make.

Separately, `CHANGES.md`'s tally table had drifted before I touched it: T25's increment from 15 to
16 corrections was recorded in prose but never applied to the table, and the printed total of 67
did not equal the sum of its own rows (65). The table is now the sum of its rows, with an explicit
bookkeeping note saying so.

## 4. Part 2 — `RED_TEAM.md` inoculation

The document reads as a to-do list, so someone could apply either false fix verbatim without
knowing. **Nothing was deleted** — the record of what was proposed and why it was wrong is the
point.

* **Top-of-document banner.** States that the *attacks* are verified but the *suggested wordings*
  are hypotheses requiring verification, cites D20, and points at the two superseded items.
* **M3 — `⚠ SUPERSEDED — DO NOT APPLY`.** "The analyzer cache was disabled for these runs" is
  **false**: `context_edit_v2_gated.yaml:18` sets `analysis_cache_dir: outputs/analysis_cache` and
  `run_exp1_reps.sh` never overrides it (contrast `tasks/T1/run_t1_main.sh`, which passes
  `analysis_cache_dir=null` explicitly); the runs' own `config.yaml` confirms the path. The note
  gives the true, stronger measured answer (39/39 differing analyzer outputs, intersection-0
  failing pairs, 7/40 and 5/40 turn and answer differences) and records that the *bootstrap* half
  of the suggestion was correct and has been run. It also flags that the "38/40 in each run"
  parenthetical was itself arithmetic on a percentage rather than a reading of the data.
* **M11 — `⚠ SUPERSEDED — DO NOT APPLY`.** Split into (a) the budget-mechanism sentence, **false**
  — 1-call replicates at 47.7%, exactly the 2-call value, and the two 1-call runs differ by more
  (p = 0.286) than 1-call differs from 2-call — and (b) "it did not finish in the window",
  **obsolete**, with the neutral-prompt result and the 0/340 mechanism finding.
* **M12, M15, M6 — `✅ RESOLVED` notes.** Shorter, but they stop those items reading as open work.
  M15's note also corrects a factual error in its own suggested revision: "we have the item-level
  data (it is how T1, T2c and T9 were computed)" is wrong — those are different experiments, the
  36-cell matrix is parsed from report tables, and `outputs/post_neurips_ac3_phase{1,2}/` hold only
  `winners.json`. The per-sample data is recoverable from `snapshot.tar.gz`, which is how T27 ran
  it, but a reader following that line to `outputs/` would have concluded it was impossible. The
  M15 note also carries the McNemar guardrail.

## 5. Part 3 — the T6 tau2 withdrawal

Routed to T28 mid-task. T6 completed the **full published matrix** at N=3: 3 models x 5 arms x 3
replicate runs (seeds 42/43/44) x 19 tasks = **855 scored rollouts**, 15/15 cells.

| tau2 (reward %) | gpt-5.4 | DSV4F | Kimi-K2.6 |
|---|---|---|---|
| FC published (N=1) | 68.4 | **31.6** | **26.3** |
| **FC re-measured (N=3)** | **68.4 ± 13.9** | **70.2 ± 11.0** | **78.9 ± 0.0** |
| AO | 0.0 | 0.0 | 0.0 |
| AC3-Augment | 47.4 ± 5.3 | 50.9 ± 8.0 | 57.9 ± 9.1 |
| AC3-Gated-Reset | 57.9 ± 21.1 | 57.9 ± 10.5 | 71.9 ± 11.0 |
| AC3-Rewrite | 47.4 ± 5.3 | 57.9 ± 13.9 | 66.7 ± 8.0 |

**On all three models the re-measured baseline is at or above every AC3 arm.** Written as a flat
withdrawal, never as "mixed results", per the routing instruction. What is posted:

* **Withdrawn:** the tau2 magnitude comparison and the improvement claim, in `00` CW4 (table
  replaced), `01` W3, `02` W2 and Q2, `04` correction **6**, `05` correction **8**.
* **Framed as "our baselines were wrong", not "not comparable"** — and stated that this was
  *tested*: gpt-5.4 FC reproduces at 68.4 vs published 68.4, AO reproduces at 0.0 in 9/9 cells and
  171 rollouts, `gpt-5-mini` reachable, invocation strings byte-identical, no model substitution.
  Our own source report already called the Kimi cells floors (14/20 and 19/20 short-exits).
* **Kept:** AO = **0.0% on every model**, structurally (rollouts exhaust the 50-step budget;
  paired −68.4 / −69.6 / −78.9pp, p < 0.0001). It does not depend on the baseline's level, which
  is the sentence that lets it survive the correction — and it is what we most need tau2 for.
* **Kept, not upgraded:** the gpt-5.4 Gated-Reset regression iNYK named — 57.9 ± 21.1 vs 68.4,
  paired **−10.5pp, p = 0.238** over 57 pairs. Reported as a persistent, underpowered negative.
* **Disclosed as unexplained:** gpt-5.4's AC3 collapse (Augment 84.2 → 47.4) with its baseline
  reproducing exactly. Ruled out: substitution, non-firing, degenerate termination, rate limits.
  The one real fork defect found — 53% of analyzer calls falling back to splicing a raw completion
  into the briefing — is worth **+2.3pp** when patched, so it is reported as a real bug that is
  *not* the explanation.
* **Phrasing:** "N=3 replicate runs (seeds 42/43/44)"; `--seed` genuinely threads on this fork,
  best-effort at the provider — explicitly unlike LiC's inert `cfg.seed`.
* **Red-team H9 closed.** "Improves over full context across the entire spectrum" would have been
  false on the benchmark it was sharpened to survive. README Blocker 5's pre-drafted fallback is
  applied in `00` CW4, `01` W3, `04` and `05`: *"improves over full context on every self-contained
  and referential benchmark, and the only method that remains **viable** in the stateful agentic
  setting"*. The stronger wording appears nowhere in the reply set.
* **`00` CW1** additionally now states that tau2 no longer supports the operator-intensity
  ordering and that we have stopped citing it as if it did — the sentence the CW1 HOLD block was
  holding out is not restored, because T6's arms do not reproduce the ordering (Augment, the
  lightest, is worst on all three models; Gated-Reset beats Rewrite on Kimi).

## 6. HOLD-block verification — two phases

**Phase 1 — the T27 pass (constraint in force).** Per-block SHA-256 over every
`⚠ INTERNAL — HOLD` region, extracted by walking each marker line out to its full contiguous
blockquote. Computed from the pre-edit commit `d989c50` (`git show HEAD:…`) and again from the
working tree after every T27 edit had landed. Baseline at `hold_baseline.txt`.

| File | Region | SHA-256 (first 32) | Bytes |
|---|---|---|---|
| `00_general_response.md` | block 1 (CW1) | `cb6e8fe025ae09c79b6a0e0190da2fd3` | 655 |
| `00_general_response.md` | block 2 (CW4) | `cd0fc826fc4c11a7a3a813df0d9778c7` | 1995 |
| `01_reviewer_iNYK.md` | block 1 (W3) | `a6158d29e50b5027bc12abdbd31b46dc` | 264 |
| `04_response_to_AC.md` | block 1 | `02fd1863722efea236d6ec0f57f4872c` | 1448 |
| `05_final_remarks.md` | block 1 | `0375d99bed752330fbc4bee6282fae59` | 806 |
| `CHANGES.md` | 4 HOLD-referencing lines | `a32f…`, `3ab5…`, `f9d4…`, `a213…` | 344 / 179 / 444 / 93 |

**All nine regions matched to the digit after the T27 pass**; only line numbers shifted (`00`
block 2 moved 150→166, `04` block 1 moved 66→67). This is stronger than grep: it would catch a
whitespace or punctuation edit that a marker-line grep would miss.

**Phase 2 — the T6 landing (constraint superseded by instruction).** The orchestrator's routing
message explicitly directed the blocks to be unsealed: they were written for exactly this outcome
and their pre-drafted withdrawal wording was written to be applied. All five reply-file HOLD
blocks and both `⚠ INTERNAL — T19 renumbering` notes were therefore **resolved and removed**, and
their content converted into posted reply text (§5). This is a deliberate, instructed change of
state, not a violation of the Phase-1 constraint — which is why the two phases are recorded
separately and Phase 1's digests are kept.

**Final state:** `grep -rn "⚠ INTERNAL" replies/v5/*.md` returns **only** `00`'s orientation
preamble, whose T6 item is rewritten from "on HOLD" to "resolved, and it goes against us".
`README.md` Blocker 1 and the "Before posting" checklist are updated from "eight blocks" to "one".

## 7. Artifacts

| Path | What |
|---|---|
| `tasks/T28/worklog.md` | this file |
| `tasks/T28/hold_baseline.txt` | per-block SHA-256 of every HOLD region at commit `d989c50` |
| `replies/v5/CHANGES.md` §12 | the reviewer-facing integration record (T27 items, reconciliations, tau2 withdrawal, HOLD verification) |
| `tasks/T23/RED_TEAM.md` | annotated in place: banner + 2 `⚠ SUPERSEDED` + 3 `✅ RESOLVED` notes |

## 8. Left open, deliberately

* **Red-team M1** — the self-correction count reads 3 / 5 / 7 / 10 across four files, and my
  changes moved two of those four. Each count is defensible in its own scope; making them agree is
  a tone judgement about how prominently the general response should carry the total, and it
  belongs to the operator.
* **The paper.** The tau2 withdrawal implies paper edits (the tau2 table, the abstract's
  "spectrum" sentence, Figure 1's claim). `writing/overleaf_repo/` is out of bounds for
  autoresearch agents, so this joins PAPER-1..10 in the operator's queue. It is the highest-stakes
  item on that list — the reply now commits to it in front of the reviewers.
* **The tau2 fork's tag-parsing bug** is patched only behind `T6_FIX_TAG_PARSE=1` in T6's clone.
  It degrades every AC3 arm and cannot touch Baseline or AO, so it should be fixed upstream
  regardless of the rebuttal.
