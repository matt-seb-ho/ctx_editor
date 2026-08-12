# Focused session: triage the MT-OSC "no-op" result

You are a fresh Claude Code session spun up specifically to interrogate ONE question for the
AC3 NeurIPS rebuttal (Sub. 27902). The main session is handling reviewer triage/response; you
own the MT-OSC baseline question only. Read the project CLAUDE.md conventions but stay scoped.

## The question

We reimplemented **MT-OSC** (arXiv:2604.08782) as a stronger context-management baseline
because reviewer **Vg97** explicitly asked for it. On LiC database it scores 60.7% at the
published setting (w=4), ~+4.7pp over baseline but **not significant** (p=0.383). The reason we
give is that MT-OSC is a **near "no-op"** on LiC-length conversations: at w=4 it performs only
**0.3 condensations/conversation** (30 across 107 convs), cannot modify context before turn 6,
and LiC conversations average **4.1 turns** — so only **6 of 30** condensations ever reached a
context. Scaling it down to w=2 fires 7.9× more often and scores *worse* (47.7%).

Answer three things, concisely and with evidence:

1. **What does "no-op" mean mechanically?** Walk the MT-OSC schedule (`T_j = (w-1)j + 2`, the
   one-turn application lag, γ/τ decider) against LiC's turn-length distribution and show
   exactly why it rarely fires and rarely reaches a generation.

2. **Is this a problem with OUR eval, or a real property of MT-OSC on short conversations?**
   i.e. did we handicap the baseline (misconfigure the window, wrong condenser model, an
   implementation infidelity) such that a reviewer could fairly say "you set it up to fail"?
   Or is short-conversation inertness intrinsic to a length-triggered compaction schedule?
   This is the crux — be adversarial against our own setup.

3. **How should we present/defend it in the Vg97 reply** so it reads as a fair, informative
   baseline and not as a strawman? What is the strongest reviewer objection and our answer?

## Read these first

- `neurips_review/RESULTS_SUMMARY_2026-08-03.md` — section **A2** (and A1 for the sibling
  summarisation baseline).
- `src/ctx_editor/strategies/mtosc.py` — the implementation **and** its written faithfulness
  audit (what was taken verbatim from the paper vs. generalised vs. underdetermined).
- `neurips_review/autoresearch/tasks/T32/worklog.md` — how the engagement rate (0.3 / 2.2) was
  derived from code + artifacts; resolves an earlier mis-count.
- `neurips_review/autoresearch/tasks/T1/` — the run (RESULTS.md, worklog.md, outputs).
- `neurips_review/replies/v5/02_reviewer_Vg97.md` — how MT-OSC is currently framed to Vg97.

## Deliverable

A short written triage (to stdout, and save to `neurips_review/MTOSC_TRIAGE.md`): the mechanism,
a clear verdict on eval-fairness (is it defensible?), and 3–5 sentences of recommended framing
for the reviewer reply. Do NOT rerun experiments unless a specific number is unverifiable from
artifacts. Flag anything that would embarrass us if a reviewer reran it.
