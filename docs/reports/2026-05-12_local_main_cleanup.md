# 2026-05-12 — Local `main` cleanup before infra pull

Short writeup of how local `main` was untangled and re-based onto `origin/main`
after the upstream experiment-infrastructure refactor landed (AC3 rename,
analyzer prompt registry, Hydra-ified Huang eval, tau2 hybrid absorption,
docs index requirement). Captured here so the decision rationale isn't lost.

## Starting state

Local `main` was 3 commits ahead of `origin/main` and origin was 22 commits
ahead of local, plus a dirty working tree (4 modified files, 9 untracked).
Local work had been done directly on `main` (no feature branch), so a plain
`git pull --rebase` would have entangled keep-worthy work with throwaway
experiments.

**Local-only commits:**

| SHA | Message | Disposition |
|---|---|---|
| `7e45c6d` | feat: reasoning effort baseline + provenance doc | **keep** |
| `f89af6c` | fix: DeepSeek+gpt-5 judge with full responses | drop (message misleading; payload was just stale paper PNGs under `writing/latex_project/` plus a stray `.swp` file) |
| `be5b32a` | fix: remove 1000-char response truncation | drop as a commit, re-apply against new infra |

**Dirty + untracked tree** included CollabLLM experiment scaffolding the user
classified as not useful, an analyzer `v12` prompt attempt (designed to dodge
Azure's prompt-injection content filter), an associated Azure-filter writeup,
and a few ad-hoc probe scripts.

## Process

1. **Snapshot everything to a backup branch first.** Made a WIP commit on
   `main` capturing dirty + untracked files (`ed800ca`), then created
   `backup/pre-infra-pull` pointing at that commit. This branch preserves the
   full pre-cleanup state verbatim — every dropped commit and discarded file
   is recoverable from it.
2. **Reset local `main` to `origin/main`** (`git reset --hard origin/main`).
   No merge / no rebase — the upstream refactor was substantial enough that
   replaying our small local commits as cherry-picks was much cleaner than
   resolving conflicts against a heavily-rewritten Huang eval.
3. **Cherry-pick the one keeper commit** (`7e45c6d`) onto the reset main. It
   only added new files, so it applied with zero conflicts.
4. **Archive and document.** Moved the `v12` prompt attempt and its Azure
   writeup to `docs/archive/v12_attempt/` with a `notes.md` capturing what
   v12 tried, why it stalled, and how to port the survival bits into the new
   prompt registry if we want to revive it.
5. **Triage the dropped local fixes against the post-refactor code.** Of the
   three small fixes that didn't survive the reset:
   - **`[:1000]` response truncation** — still present in 11 spots across
     `huang_eval/run_phase1.py`, `huang_eval/run_phase2.py`, and
     `scripts/run_wildchat_memory.py`. Re-applied as a new commit.
   - **`run_phase2.py` result-dict newline mash-bug** — already fixed by the
     upstream rewrite (`result["sX_response"] = ...` and `result["sX_analysis"] = ...`
     are on separate lines now).
   - **`memory=None` kwarg position** — already correct in the new
     `process_failure_turn` signature; `memory=None` is the last parameter,
     no required positionals after it.
6. **Restore `scripts/test_non_oai.py`** (ad-hoc non-OpenAI deployment probe,
   useful for ongoing Azure-filter diagnostics) from the backup branch as a
   separate commit.

## What got dropped

Recoverable from `backup/pre-infra-pull` (`ed800ca`) at any time:

- CollabLLM yaml mods + report + scripts (`collabllm_*.yaml`,
  `docs/reports/collabllm_panel_b_v12.md`, `scripts/collabllm_error_bars.py`,
  `scripts/launch_collabllm_gr_aug.sh`).
- `f89af6c`'s stale paper PNGs under `writing/latex_project/` — paper assets
  now live under `writing/overleaf_repo/assets/` per `CLAUDE.md`.
- The stray `.huang_eval_30conv.md.swp` vim swap file.
- `scripts/test_claude.py` + `scripts/launch_wildchat_gr_replicates.sh`
  (one-off probes; can restore from backup if needed).
- The pre-reset `analyzer.py` `_analyze_v12` code path itself (the *prompts*
  are archived under `docs/archive/v12_attempt/`; the wiring will be
  re-derived against the new prompt registry if we revive it).

## Final state on `main` (4 commits ahead of `origin/main` after cleanup)

```
4a6c21b chore: restore scripts/test_non_oai.py probe
50f01b2 fix: remove [:1000] response truncation across huang_eval + wildchat
1f40476 docs: archive v12 analyzer attempt + flag fixes pending re-verification
f7afae1 feat: reasoning effort baseline experiment (medium vs high) + paper provenance doc
```

Working tree clean.

## Lessons / takeaways

- **Don't work directly on `main`.** This cleanup was only painless because
  the upstream changes happened not to touch `7e45c6d`'s paths; if they had,
  the cherry-pick would have conflicted and the backup-branch dance would
  have been a lot less mechanical.
- **A WIP-snapshot commit on a backup branch beats a stash** for situations
  like this. Stashes can be dropped accidentally; a named branch can't.
- **Commit messages should match payload.** `f89af6c` claimed to be a judge
  fix but was just paper assets — that mismatch is what made disposition
  unclear for ten minutes when sorting through the local commits.
