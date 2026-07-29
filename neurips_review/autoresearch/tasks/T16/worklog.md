# T16 — Re-deriving the gate-open statistics from trace artifacts

**Status:** complete (2026-07-29 overnight session). Zero API calls.
**Question:** do the gate-open rates **97.3% (LiC, n=554)** and **98.3% (CollabLLM, n=119)**
— quoted in `replies/v5/03_reviewer_5YHP.md:112`, flagged unverifiable as **U1** in
`replies/v5/CHANGES.md` §7 — hold up against the traces?

## Verdict (short)

**The numbers are real and reproduce to the digit. The *wording* around them is wrong in two
places, and one honest caveat is missing.**

1. **U1 should be retired, not "re-derived-and-changed".** The artifact the audit could not
   find does exist: `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_lic.md`
   and `..._collabllm.md` (2026-06, in-repo). Both state the figure verbatim
   (`539/554 (97.3%)`, `117/119 (98.3%)`). I reproduced both from raw traces independently.
2. **Both figures are per-CONVERSATION, not per-turn.** The reply calls them "97.3% of LiC
   turns" and "98.3% of CollabLLM turns". For LiC that is harmless (last-turn replay ⇒ exactly
   one analyzer call per conversation, verified). **For CollabLLM it is materially wrong**: that
   run is genuinely multi-turn, 659 analyzer calls over 120 conversations. The turn-level
   CollabLLM rate is **95.3%**, not 98.3%.
3. **Both denominators silently count conversations the analyzer never ran on as gate-CLOSED.**
   This is exactly the trap the task brief named. Correcting it *raises* both rates.
4. **New caveat worth stating:** on the arm the claim comes from, 28.8% (LiC) / 73.4%
   (CollabLLM) of gate-OPEN records have the analyzer explicitly writing `"None"` under
   `issues`. `needs_edit` is a firing rate, not a detection rate. This is consistent with — and
   arguably strengthens — the reply's own "the gate is close to always-on" framing, but a
   reviewer who is handed the script will find it, so we should say it first.

## Recomputed numbers

Regenerate everything with:

```bash
.venv/bin/python neurips_review/autoresearch/tasks/T16/gate_stats.py \
    --control --json neurips_review/autoresearch/tasks/T16/gate_stats.json \
    > neurips_review/autoresearch/tasks/T16/report.md
```

| population | metric | value |
|---|---|---|
| **LiC** | legacy (reproduces the claim) | **539/554 = 97.3%** ✅ exact match |
| | corrected, turn = conversation level | **539/547 = 98.5%** |
| **CollabLLM** | legacy (reproduces the claim) | **118/120 = 98.3%** ✅ exact match (see note) |
| | corrected, conversation level | **118/118 = 100.0%** |
| | **turn level** (what the reply claims to report) | **628/659 = 95.3%** |

**CollabLLM n=119 vs n=120.** The 2026-06 reconstruction paired against the Baseline arm and
lost one `bigcodebench` rep3 sample (its table shows `bigcodebench` conv3 n=19). Its two
gate-closed conversations are `math-hard`, and they are exactly the two conversations on which
the analyzer never ran. Per-task the reconstruction and my recount agree cell-for-cell
(bigcodebench 100% open; math-hard 58/60 = 96.7%). The population is fully reconstructable; I
report the complete n=120 rather than the pairing-truncated n=119.

## Exact populations

| | LiC | CollabLLM |
|---|---|---|
| run root | `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/` | `~/ac3/t14_snapshot/ctx_editor/outputs/post_neurips_ac3_phase3_collabllm/` |
| arm | `context_edit_v2_no_gate*` (always-on Reset; the analyzer runs and logs `needs_edit` every turn, the flag is simply ignored) | `collabllm_ac3_reset_v8_*` |
| model | DeepSeek-V4-Flash | DeepSeek-V4-Flash |
| cells | 4 tasks × 3 conv prefixes = 12 | 2 tasks × 3 reps = 6 |
| conversations | 554 | 120 |
| analyzer invocations | 547 | 659 |
| design | last-turn replay ⇒ 1 analyzer call / conversation | end-to-end multi-turn ⇒ 1–11 calls / conversation |

Neither tree is inside the repo (both are recovered snapshot extractions); the script points at
them by absolute path and warns if a root is missing.

## Per-task breakdown — LiC, `context_edit_v2_no_gate`

| task | conversations | analyzer never ran | invocations | gate-open | **open rate (turn)** | legacy rate |
|---|---|---|---|---|---|---|
| actions | 150 | 0 | 150 | 149 | **99.3%** | 99.3% |
| code | 113 | 7 | 106 | 103 | **97.2%** | 91.2% |
| database | 147 | 0 | 147 | 144 | **98.0%** | 98.0% |
| math | 144 | 0 | 144 | 143 | **99.3%** | 99.3% |
| **all** | **554** | **7** | **547** | **539** | **98.5%** | **97.3%** |

**Not bimodal.** Every task sits in 97–99%; the pooled figure is honest. The whole 97.3 → 98.5
gap is `code`, whose 7 excluded conversations ended before `min_turns` so the analyzer was never
invoked. T2c independently found the same 7 (`T2c/worklog.md` §6d caveat 6).

Per conv-prefix (12 cells), the turn-level rate ranges **94.3%–100%**; the minimum is
`code conv1` (33/35).

## Per-task breakdown — CollabLLM, `ac3_reset_v8`

| task | conversations | analyzer never ran | invocations | gate-open | **open rate (turn)** | conv-level (any turn) |
|---|---|---|---|---|---|---|
| bigcodebench | 60 | 0 | 374 | 352 | **94.1%** | 60/60 = 100% |
| math-hard | 60 | 2 | 285 | 276 | **96.8%** | 58/58 = 100% |
| **all** | **120** | **2** | **659** | **628** | **95.3%** | **118/118 = 100%** |

Per-rep turn-level range **93.1%–97.8%**. Again not bimodal.

## Per-strategy breakdown

Every arm that invokes the analyzer, same trees:

| benchmark | strategy | conversations | never ran | invocations | gate-open | **open rate (turn)** |
|---|---|---|---|---|---|---|
| LiC | `context_edit_v2_no_gate` (Reset) | 554 | 7 | 547 | 539 | **98.5%** |
| LiC | `append_analysis` (Augment/S1) | 554 | 7 | 547 | 539 | **98.5%** |
| LiC | `context_edit_v2_gated` (Gated-Reset) | 554 | 22 | 532 | 524 | **98.5%** |
| LiC | `ac3_rewrite_lic` (v8 Rewrite) | 554 | 554 | 0 | 0 | n/a |
| CollabLLM | `ac3_reset_v8` | 120 | 2 | 659 | 628 | **95.3%** |
| CollabLLM | `ac3_augment_v8` | 120 | 26 | 894 | 857 | **95.9%** |

Two things to note:

- **The three LiC analyzer arms agree to the invocation** (539/547 each, and identically
  149/103/144/143 per task). Expected under replay — all three branch from the same recorded
  prefix and call the same analyzer on the same input — and it is a useful cross-arm
  replication rather than a suspicious coincidence. `context_edit_v2_gated` differs only in
  having 22 rather than 7 never-ran conversations.
- **`ac3_rewrite_lic` emits no `conversation_analysis` records at all.** The v8 Rewrite operator
  uses a different log schema (`<new_context>` emission, no gate). It is therefore out of scope
  for a gate statistic, not a zero. The script reports `n/a`, not 0%, which matters: a naive
  tally that globbed all arms would have reported a pooled rate of ~74% purely from this.

## Diagnostic — is `needs_edit` coupled to the analyzer finding issues?

| `issues` content | LiC gate-open | LiC gate-closed | CollabLLM gate-open | CollabLLM gate-closed |
|---|---|---|---|---|
| states concrete issues | 384 | 0 | 167 | 0 |
| explicitly `"None"` | **155** | 1 | **461** | 2 |
| empty | 0 | 7 | 0 | 29 |

**155/539 = 28.8% (LiC) and 461/628 = 73.4% (CollabLLM) of gate-open records have the analyzer
writing "None" under `issues` and still setting `needs_edit=true`.** The gate is close to
vacuously open, especially on CollabLLM. This should be read as a firing rate. It is not a
contradiction of the reply — the reply already says the gate is deliberately high-recall and
close to always-on — but claiming the gate "detects" pollution 98% of the time would be
unsupportable, and the reply is careful not to (`"We would not over-read firing rates into a
precision/recall claim"`). That sentence is now backed by data.

## Positive controls

All four mandated checks pass.

- **C1 — independent parser.** A raw-text regex scan for `"needs_edit"\s*:\s*(true|false)`,
  bypassing the JSON walk entirely, over all 2456 trace files: **3087 true / 92 false = 3179**
  fields. The JSON walk reports **3087 open / 3179 invocations**. **MATCH.**
- **C2 — never-ran vs gate-closed.** Calls-per-sample histograms per arm confirm the
  distinction is handled correctly (0 calls ⇒ excluded from the invocation denominator, *not*
  counted as closed):
  - `LiC/context_edit_v2_no_gate`: `{0: 7, 1: 547}` — confirms last-turn replay, 1 call/sample.
  - `LiC/context_edit_v2_gated`: `{0: 22, 1: 532}`
  - `LiC/ac3_rewrite_lic`: `{0: 554}` — different schema, correctly excluded.
  - `CollabLLM/ac3_reset_v8`: `{0: 2, 1: 8, 2: 14, 3: 7, 4: 4, 5: 4, 6: 5, 7: 72, 8: 4}` —
    genuinely multi-turn, which is what makes the "turns" wording wrong.
- **C3 — cross-check against a different log record.** `edit_decision.should_edit` is written by
  a separate code path. Restricted to the 1197 conversations that emit any `edit_decision`
  (`append_analysis` and `ac3_reset_v8` never gate, so they emit none): **0 disagreements**.
- **C4 — hand inspection.** 12 records dumped evenly across arms
  (`gate_stats.py --dump-samples 12`) and read by hand; parser count matched manual count on
  all 12.

**One false alarm, caught by C4 and worth recording.** My first pass at the `issues` diagnostic
classified 339/659 CollabLLM records as "prompt-template echoes" (the field literally begins
`"What in the assistant's responses contradicts..."`), which would have been a serious data
quality finding. Reading one in full showed the analyzer prefixes the prompt's own section
header and *then* gives the real numbered analysis. The header is a formatting artifact, not a
failed generation. `classify_issues()` now strips it before classifying. No headline number was
affected — the gate tallies never touched the `issues` field — but the finding would have been
wrong.

## What to change in `replies/v5/`

**Required (factual):** `03_reviewer_5YHP.md:112` says *"98.3% of CollabLLM turns (n=119)"*.
That is a conversation-level figure. Either relabel it, or quote the turn-level number:

> the gate opens on **98.5% of LiC turns (n=547 analyzer invocations)** and **95.3% of CollabLLM
> turns (n=659)**; at the conversation level it opens at least once on **539/554** LiC and
> **118/118** CollabLLM conversations.

**Recommended (pre-emptive):** add one clause noting that `needs_edit=true` co-occurs with an
explicit `issues: "None"` on 29% of LiC and 73% of CollabLLM open turns, so the figure is a
firing rate. The reply's existing "we would not over-read firing rates into a precision/recall
claim" sentence then lands with evidence behind it.

**Also:** `CHANGES.md` §7 U1 should be updated — the claim is no longer unverifiable. Cite
`neurips_review/autoresearch/tasks/T16/gate_stats.py` plus the 2026-06 artifacts at
`scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, which the
audit missed.

## Files

| file | what |
|---|---|
| `gate_stats.py` | reusable, zero-API regenerator; `--control` runs C1–C3, `--dump-samples N` prints raw records |
| `report.md` | full generated output (all tables, controls) |
| `gate_stats.json` | machine-readable tallies |

## Ambiguity resolved without asking

- **Which arm is "the" gate-open rate?** The 2026-06 reconstruction used the always-on Reset arm
  (analyzer runs every turn, flag logged but ignored), so that is the headline. All other
  analyzer-bearing arms are reported alongside; they agree.
- **CollabLLM n=119 vs 120.** Reported the complete 120 and explained the missing one, rather
  than reverse-engineering the 2026-06 pairing drop.
- **Which sample-level rule did the 2026-06 script use?** Not recorded. Both `any-turn-open` and
  `last-turn-open` are computed; `any` reproduces the CollabLLM figure exactly, so that was the
  rule. On LiC the two are identical.
