# AC3 arXiv prep — state of things & machine audit (2026-09-03)

Written to get Matthew back on top of the arXiv push after time away on the summer
internship. Two parts: **(1) is the paper done/ready?** and **(2) a guide to the tmux
sessions on this machine** with close/keep recommendations.

TL;DR:
- **The arXiv draft is written, honest, internally consistent, and revised through multiple
  passes (research-paper-writing skill + a formal adversarial debate + a later, even more
  conservative evidence fold-in).** It is *not yet posted*, and there are **3 real blockers**,
  only one of which is genuinely hard.
- **The machine is running 4 Claude sessions across 3 tmux sessions.** Only one (the `arxiv`
  window in tmux session `1`) did the paper work, and its output is fully committed to git — so
  the others can be closed safely. Recommendation: consolidate to a single driver session.

---

## Part 1 — Is the paper done? Is it ready?

### 1.1 Short answer

**Content-complete and rebuttal-hardened: yes. Postable today: no — one hard blocker (author
block) and one correctness blocker (Figure 1 art), plus a push/access step.** Everything else
is polish.

The draft you'd post lives at:

```
writing/overleaf_repo/arxiv/neurips_2026_conference.tex   (851 lines added over the neurips/ copy)
```

It is a **clean duplicate of `neurips/`** retargeted as the preprint, so the frozen NeurIPS
submission is untouched. This is the version-control approach used (git history + a folder copy),
which satisfies the "keep old versions recoverable" request — see §1.5.

### 1.2 What was incorporated (rebuttal-period + post-submission work)

All folded into `arxiv/…tex` (commit `5565100`, preceded by `b1a629a`, `ef40b01`):

| Area | What changed | Status |
|---|---|---|
| **tau2-bench claim** | *Improvement claim fully withdrawn.* Re-measured N=3 baselines (855 rollouts) showed two of the three originally-reported baselines were **rate-limit-clipped floors**. Reframed as a **viability test**: AO collapses to 0% structurally; Gated Reset holds parity; the unexplained gpt-5.4 cell is disclosed. | ✅ done |
| **Mechanism** | Retracted "preserve what's correct" → "detect, discard the assistant side, **rebuild the spec from the user side**," backed by new Tier-B span-ablation evidence (detection real, selectivity not — and the paper *says so*). | ✅ done |
| **Table 1 comparability** | ERGO on matched pools, per-task denominators, gap-closure updated **55–80% → 67–82%**; WildChat framed as a **72–92% consistency envelope**. | ✅ done |
| **5 new-evidence subsections** | matched-compute condenser + MT-OSC baselines; analyzer-as-detector (Tier A/B); analyzer robustness across 4 model families; item-level McNemar + scale; explicit a-priori operator-selection rule in Methods. | ✅ done |
| **Overclaim softening** | "only method robust across the spectrum" → "only method that improves over full context on every self-contained/referential benchmark, and remains viable in the stateful setting." "Every operator beats baseline" retired → **best operator per cell**. | ✅ done |
| **De-anonymization** | Switched to `\usepackage[preprint]{neurips_2026}`. | ✅ done (except author names — see blockers) |
| **House style** | Prose em-dashes removed (tex + checklist). | ✅ done |

The narrative got **progressively more conservative and more honest** over three rounds — the
final draft is *stronger* because it's rebuttal-proof, not weaker.

### 1.3 Was there multiple-pass / adversarial revision? (Yes)

The user specifically asked about this. Evidence on disk:

1. **research-paper-writing skill passes** — used for abstract readability, flow, terminology
   consistency (state doc §4 Priority 3).
2. **Formal adversarial debate** — `docs/arxiv_push/debate/`:
   - `01_reviewer_skeptic.md` — claim–evidence & desk-reject risks (reviewer A).
   - `02_writing_editor.md` — flow/clarity/terminology (reviewer B).
   - `03_synthesis.md` — an Opus orchestrator adjudicated the two against ground-truth numbers
     and issued a ruling. **The skeptic won the key tensions** ("every operator beats baseline"
     and the "+47.4pp / 60%→0%" headline were shown to be overclaims against the paper's own
     tables) and the draft was moved to the honest framing.
3. **A later evidence fold-in pass (2026-08-12)** went *even further* than the July debate —
   withdrawing the tau2 improvement claim entirely after the N=3 baseline re-measurement. This is
   the current state.

So: multiple independent passes, adversarial review, and version-controlled rollback points all
happened. This part of the request is satisfied.

### 1.4 Blockers before a public arXiv post

**Ranked. Only #1 and #2 are true blockers.**

1. **[HARD BLOCKER] Author block is a placeholder.** `arxiv/…tex` lines 62–65:
   `\author{ Anonymous Authors }` with a `% TODO(authors)`. Preprint mode is on, but the real
   author list, order, and affiliations are not filled in. **Only you/co-authors can supply this.**
2. **[CORRECTNESS BLOCKER] Figure 1 art contradicts its corrected caption.** The schematic
   (`assets/ctxe_story.drawio.png`) still draws AC3 ≥ vanilla at the tau2 (stateful) end. The
   corrected caption now says AC3 *remains viable but does not exceed full context* there. The
   `.drawio` source is missing from the repo. **Note:** there are new **untracked** files
   `assets/fig1_bars_gpt54.{pdf,png}` (+ `_h2h` variants) in the overleaf repo — these look like a
   started attempt at a replacement figure. Worth checking whether they're the intended redraw.
3. **[MECHANICAL] Not pushed to Overleaf.** The inner repo is **3 commits ahead of origin**, and
   Overleaf's `main` is still at the old `d211637` — meaning **none of the post-submission
   revision work has reached Overleaf/co-authors yet.** The previous session recorded the push as
   failing ("Repository not found"). **This is now resolved:** the `id_ed25519_deux` SSH key
   authenticates to the paper repo cleanly (verified `git ls-remote` today, GitHub identity
   `matt-seb-ho`). Pushing just needs the right key configured + your go-ahead (collaborator-visible).

**Softer items (do before or shortly after v1 — none block posting):**
- MT-OSC "6 of 107 conversations" counter (FLAG-1) unconfirmed against a single source artifact.
- LiC per-cell floor `n≈113` (FLAG-2) asserted in a handoff, not traced to a RESULTS count; draft
  currently prints the safe ceiling "up to 150/cell."
- "Gated Reset" vs "Gated-Reset" hyphenation sweep.
- Redundant `arxiv/assets/prompts/` copy (harmless drift risk).

Full detail: `docs/arxiv_push/nice_to_have_experiments.md` (§A hygiene, §B provenance, §C v2
experiments, §D explicitly-out-of-scope).

### 1.5 Version control / rollback (as requested)

Already in place — no `_v1/_v2` file sprawl needed:
- **Frozen submission:** `neurips/neurips_2026_conference.tex` (untouched).
- **arXiv version:** `arxiv/neurips_2026_conference.tex` (all edits here).
- **Pre-edit backup:** `docs/arxiv_push/backups/neurips_2026_conference.d211637.tex`.
- **Per-group commits** in the inner repo make selective rollback easy.
- ⚠ **Confusing stragglers to clean up:** `neurips/neurips_2026_conference_v2.tex` is **untracked
  and stale** (a May-9 table-mockup-era artifact, *not* a newer version despite the name). Recommend
  deleting or renaming it so it isn't mistaken for the current draft.

### 1.6 Honest caveat about *this* report

I (the Sep-3 session) **verified the blockers and framing directly** in the `.tex` and confirmed
the debate artifacts exist, but I did **not** re-run a fresh independent adversarial pass or
re-verify every number in this sitting. The multi-pass revision above was done by the prior
`arxiv` session. If you want, I can run one more clean-eyes review pass (skeptic + copyedit) as the
first task of the consolidated session before we push — recommended, since it's cheap insurance.

---

## Part 2 — tmux / Claude-session audit & cleanup guide

3 tmux sessions, 12 windows, **4 Claude sessions**. Nobody is "in charge" in a coordinated sense —
they're independent threads spun up over time. Here's the map.

### 2.1 The Claude sessions

| tmux | window | what it is | state | safe to close? |
|---|---|---|---|---|
| `1` | `1:1 arxiv` | **The paper session.** Did all the arXiv fold-in work. | Idle; waiting on a push decision. ~142k tokens. | **Yes — all output committed to git.** Its in-memory context is not needed; everything is on disk (commits + `docs/arxiv_push/`). |
| `1` | `1:4 entangle-bench` | Separate research thread: entanglement-knob benchmark + context-management literature survey (v2 experiment ideas, not the current paper). | Complete; its cron was retired; idle. Committed (`9a39a89`, `0b5ea5b`, entanglement commits). | **Yes.** Nothing uncommitted; nothing touching `writing/overleaf_repo/`. |
| `1` | `1:5` (titled `[tmux]`) | The Azure-blob **backup/restore guide** session. | Complete; committed (`c22b5ca`, `f2edf16`, `665e95d`); idle. | **Yes.** |
| `0` | `0:1 claude` | Fresh empty Claude at `~/ac3`. | Idle welcome screen, no work. | **Yes — nothing there.** |
| `4` | `4:0 claude` | **This session (Sep-3).** The one you're talking to. | Active. | Keep — proposed single driver. |

### 2.2 The non-Claude windows

| tmux | window | what it is | recommendation |
|---|---|---|---|
| `0` | `0:0 bun-` | `copilot-api` server (`bun`), **listening on port 4141**, running since Jul 28. A local API proxy. | **Don't kill blindly** — it's a live service something may route through. Verify it's unused before closing. Not part of the paper work. |
| `0` | `0:2 bash` | idle shell in `ctx_editor` | close at will |
| `1` | `1:0 main` | idle shell in `overleaf_repo` | close at will |
| `1` | `1:2 bash` | idle shell in `ctx_editor` | close at will |
| `1` | `1:3 bash` | idle shell in the `research-paper-writing` skill dir | close at will |
| `1` | `1:6 bash-` | idle shell in `~/ac3` | close at will |
| `4` | `4:1 bash-` | idle shell (this session's) | keep |

### 2.3 Recommended end-state & cleanup

Target: **one driver session (`4:0`) + subagents**, as requested.

Proposed actions (destroys only committed/idle state; **get consent first — killing a Claude
window loses its scrollback/context, though all its *work* is already on disk**):

```bash
# Close the finished/empty Claude sessions:
tmux kill-window -t 1:1     # arxiv  (work committed)
tmux kill-window -t 1:4     # entangle-bench (committed)
tmux kill-window -t 1:5     # blob-guide (committed)
tmux kill-window -t 0:1     # empty claude

# Close idle shells (optional tidy):
tmux kill-window -t 0:2 ; tmux kill-window -t 1:0 ; tmux kill-window -t 1:2
tmux kill-window -t 1:3 ; tmux kill-window -t 1:6

# Leave running until confirmed unused:
#   0:0  copilot-api server (port 4141)
# Keep:
#   4:0 (this driver) + 4:1 (its shell)
```

After this you'd have tmux session `4` as the single home for the arXiv push, plus the
`copilot-api` server if you still want it. No cron jobs are scheduled (checked).

---

## Part 3 — recommended next steps for the arXiv push

In order:
1. **Fill in the author block** (`arxiv/…tex` l.62–65) — the one thing only you can do.
2. **Decide the Figure 1 fix** — confirm whether `assets/fig1_bars_gpt54.*` is the intended
   replacement, or redraw the schematic so the tau2 bar shows parity/below.
3. **(Optional, recommended) one clean-eyes review pass** on `arxiv/…tex` before pushing.
4. **Push to Overleaf** with the `id_ed25519_deux` key (verified working) so co-authors see the
   revised draft — with your go-ahead, since it's collaborator-visible.
5. Clear the soft hygiene items (hyphenation sweep, FLAG-1/2 confirmations, stale `_v2.tex`).
6. Then it's postable. v2-strengthening experiments are ranked in `nice_to_have_experiments.md`
   §C but are explicitly *not* required for a v1 post.
