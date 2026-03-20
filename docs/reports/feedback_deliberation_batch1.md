# Deliberation on Batch 1 Feedback — 2026-03-14

Response to `docs/feedback_on_newleaf2_batch1.md`. For each feedback point, I deliberate
on the options and state what action was taken.

---

## 1. Branching Problem

**Feedback**: The analyzer's task spec should resolve ambiguity. Is the problem that the
assistant reads the analysis and still branches? Is this solvable with prompt changes?

**Deliberation**: The branching problem has two layers:
1. The task spec query sometimes preserves ambiguity rather than committing to the natural
   reading. This is partially because the user messages genuinely are ambiguous (by design —
   LiC shards are rewritten fragments).
2. Even when the task spec is clear, gpt-5-mini's tendency is to present multiple scenarios.

For (1), the fix to include compacted conversation content in the task spec query (see below)
should help — the accumulated task spec from prior turns provides a clearer foundation.

For (2), this is more of a model behavior issue. We could strengthen the S1 system addendum
to say "treat the task spec in the analysis as definitive." But I'm being conservative here —
let's see how the replay results look with the S2 fix first before adding more prompt pressure.

The post-hoc evaluation fix (marking correct if either branch is right) is interesting but
adds evaluation complexity. I agree it's better to solve from the methods side.

**Action**: No additional changes beyond the S2 fix. Revisit after replay results.

---

## 2. S2 Loses Accumulated State (Critical Bug Fix)

**Feedback**: After S2 compacts, the analyzer only sees the latest user message, not the
task spec from the previous compaction. Fix: include the compacted conversation content.

**Deliberation**: This is clearly a bug. After a reset, `get_user_messages_string()` returns
only `role="user"` messages. The compacted conversation (which contains the previous task spec
+ aligned work) has `role="compacted conversation"` and is excluded. So the analyzer's task
spec query only sees the latest user message — losing all accumulated information.

**Action**: Two changes implemented:
1. Added `include_compacted` parameter to `ConversationTrace.get_user_messages_string()`
   that also includes `role="compacted conversation"` messages, labeled as
   `[Previous Task Summary]` to distinguish them from user messages.
2. Updated `ConversationAnalyzer._analyze_v6()` to pass `include_compacted=True` when
   building the task spec query.

This means after a reset, the task spec query sees:
```
[Previous Task Summary]
# Task Spec
{accumulated task spec from prior analysis}
# What Looks Right So Far
{aligned work}

[Message 1]
{latest user message}
```

This lets the analyzer update/extend the previous task spec rather than building from scratch.

**Note on multi-artifact tasks**: The feedback also suggests adjusting the analyzer prompt
for tasks requesting multiple artifacts. The current task spec prompt ("Include every
requirement, constraint, example, and correction") should handle this naturally once it
has the full accumulated context. I'm not adding a separate prompt change now — let's see
if the compacted content fix is sufficient.

---

## 3. Memory Injection Harms Actions

**Feedback**: Three options — (1) prompt guardrails against clarifying questions,
(2) error attribution as cheatsheet update preprocessing, (3) accept S0+mem as baseline.

**Deliberation**:
- **Option 1 (guardrails)**: Not cheating — it's a known property of the LiC user simulator
  (averse to answering clarifying questions). Adding a guardrail like "do not ask clarifying
  questions — work with the information provided" is defensible because it matches realistic
  settings where the user may not be available for follow-up. However, this is a general
  system prompt change that affects all strategies, not just memory. I'll hold off for now.
- **Option 2 (error attribution in cheatsheet pipeline)**: This is the most principled fix.
  If the error is the user simulator's fault (e.g., not answering a reasonable question),
  the cheatsheet shouldn't learn from that trajectory. This requires error attribution to be
  running (now re-enabled) and integration into the cheatsheet update pipeline. This is a
  larger change for a follow-up.
- **Option 3 (accept it)**: S0 is mostly a baseline. If S1+mem and S2+mem work well, S0+mem
  being slightly worse is acceptable.

**Action**: Re-enabled error attribution (see below). The cheatsheet pipeline integration
is deferred to a follow-up. Accepted that S0+mem may underperform on actions for now.

---

## 4. S2+mem Regresses on Math

**Feedback**: Address clarification question issue, other prompt adjustments?

**Deliberation**: The S2+mem regression (39% → 30%) is caused by two factors:
1. The cheatsheet amplifies multi-branching (same as the branching problem above)
2. The analyzer's low edit rate means the cheatsheet rarely gets to help

With the S2 accumulated state fix, the analyzer should produce better task specs after
resets, which should improve both the edit rate and the quality of edits. The cheatsheet
should then learn from better-quality trajectories.

**Action**: No additional changes beyond the S2 fix. The replay experiments will test
whether the fix helps.

---

## 5. S1 Works Through Passive Consolidation

**Feedback**: Good, expected. Show the promise of S2.

**Deliberation**: The replay mode is ideal for showing S2's promise. With identical
conversation prefixes, S2 can demonstrate that context rewriting helps on the final turn
without the compounding effects of full simulation. The S2 accumulated state fix should
also improve replay results.

**Action**: Replay experiments will test this.

---

## 6. Error Attribution Was Disabled

**Feedback**: Re-enable it, one query per conversation is fine.

**Action**: Changed `config.yaml` defaults:
- `error_attribution.enabled: true`
- `error_attribution.model: gpt-5-mini` (was gpt-4o-mini)

---

## 7. RE: "Fix Memory Target for S0"

**Feedback**: We already have separate reflection prompts for different targets.

**Deliberation**: Correct. The `target` parameter in `CheatsheetUpdater` selects both the
renderer (how the trajectory is shown) and the reflection prompt (what to reflect on). With
`target=assistant`, it uses `render_for_assistant` and `assistant_reflection.txt`. With
`target=analyzer`, it uses `render_for_analyzer` and `analyzer_reflection.txt`. These are
already separate and appropriate for their targets.

The runner script already sets `memory.target=assistant` for S0 and `memory.target=analyzer`
for S1/S2, which is correct.

**Action**: No changes needed. This was already handled correctly.

---

## Summary of Changes Made

| Change | File(s) | Description |
|--------|---------|-------------|
| S2 accumulated state fix | `core/trace.py`, `strategies/analyzer.py` | Task spec query now includes compacted conversation content after resets |
| Error attribution enabled | `config/config.yaml` | Default `enabled: true`, model changed to `gpt-5-mini` |
| Replay runner script | `scripts/run_replay_experiments.sh` | Runs S1/S2 ± memory on S0 baseline prefixes |
