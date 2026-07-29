# T14 — Audit of `adjusted_accuracy` (false-negative adjustment) and corrected LiC matrix

Started 2026-07-29. Autonomous session. Operator asleep.

## Goal
1. Characterise the FN-judge bias mechanism with file:line evidence.
2. Quantify per-arm exclusion rates across the LiC matrix (tasks × strategies).
3. Re-derive corrected accuracies with T1's arm-symmetric re-judge.
4. State whether any qualitative conclusion flips.
5. Recommend what the paper should report.

## 0. Ground rules adopted
- Reuse `neurips_review/autoresearch/tasks/T1/fn_rejudge.py` verbatim where possible.
- Output dir scoped to T14 (`outputs/T14/`), never write into other agents' dirs.
- No `git checkout` in this tree.
- Judge model `gpt-5.4-mini_2026-03-17` under `load_balancer=trapi`; `execution.max_concurrent=5`.
- Positive controls mandatory before trusting any number.

---

## 1. Mechanism — confirmed, file:line

`src/ctx_editor/identify_false_negatives.py`

- **L190-193** `get_active_messages(trace)` — `return [m for m in messages if m.get("visible", True) and m.get("role") != "log"]`. Filters on the per-message `visible` flag.
- **L228** inside `analyze_sample`: `messages = get_active_messages(trace) if isinstance(trace, dict) else []`
- **L229-230** `user_messages_str = format_user_messages(messages)` / `system_message_str = format_system_message(messages)` — only the *visible* subset reaches the prompt.
- **L96-104** the prompt then asks the judge to evaluate "the UNION of all user messages", and **L106-110** instructs it to mark insufficient if "a critical detail ... is completely absent from ALL user messages".
- **L160-164** `exclusion_reason` → `"user_sim_induced"` when `not user_sim_sufficient`.
- **L419, L426** `compute_adjusted_accuracy` — `adjusted_denominator = total_valid - len(user_sim_induced)`; user-sim-induced samples are *always* dropped from the denominator (no config gate, unlike non-answer-attempts at L427).

So: an arm that hides user turns causes the judge to see a truncated union, conclude the user
never specified the problem, and get the sample deleted from its own denominator. Numerator
(`total_correct`) is untouched. Deleting failures from the denominator only ⇒ accuracy inflates
monotonically with how much user text an arm hides. This is post-treatment conditioning; the
exclusion rate is a function of the treatment.

Confirmed magnitude by T1 on LiC-database: baseline excludes 9% of its failures, AC3-Reset 62%,
summarisation 78%.

TODO next: confirm which strategies actually set `visible=False` on *user* messages (vs only
assistant messages) — that determines which paper cells are affected.

---

## Log
