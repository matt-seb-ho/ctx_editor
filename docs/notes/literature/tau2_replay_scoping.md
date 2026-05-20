# tau2 Replay-Mode Scoping (R3 Task 15)

**Verdict**: tau2 telecom_small can NOT be easily last-turn-replayed
overnight. Cost-effective expansion of the tau2 cell of the mega
table requires either:

1. A morning of engineering to build replay infrastructure, OR
2. Fresh-sim runs which cost ~2h per (assistant model, strategy) cell.

For tonight, **defer tau2 fills**. Document the engineering ask in
the follow-ups.

## Why replay is hard for tau2

tau2's `telecom_small` is a **dual-control Dec-POMDP**:

- Agent has CRM-side tools (customer lookup, service ops).
- User-sim has phone-side tools (toggle airplane mode, reseat SIM).
- Both modify a shared environment state.
- Per turn each side chooses *either* a message or a tool call.

A "prefix" at turn k therefore captures:

- The conversation transcript through turn k.
- The agent's tool-call history through k.
- The user's tool-call history through k.
- The full **environment state snapshot** at turn k (CRM DB + phone
  state + flags).
- The user-sim's hidden persona / planning state.

To last-turn-replay, we would need to **persist all five** at every
turn during a baseline run, then on replay reload them, apply the
intervention strategy, and continue. The current runner
(`/home/v-homatthew/tau2_ctxe/ctx_edit/run_parallel.py`) doesn't
snapshot any of this — env state lives inside the tau2 Env object
and isn't serialized between turns.

Compare to LiC (cheap replay: just user-turn shards) and Huang
(cheap replay: real human conversation is already frozen on disk).
CollabLLM is single-control but still requires conversation + user-sim
state. tau2 is the worst case for replay-mode infrastructure.

## Estimated effort to add replay (rough)

| Step | Effort |
|---|---|
| Add env-state snapshot/restore on the tau2 fork | half-day |
| Persist user-sim persona / plan state | half-day |
| Adapt `run_parallel.py` to accept a `--replay-from <prefix-dir>` | quarter-day |
| Capture-baseline pass to materialize prefixes | quarter-day |
| Sanity-check replay reproducibility vs. fresh | half-day |
| **Total** | ~2 dev-days |

This is real eng work, not a small wrapper. Worth doing if we want
to scale tau2 across multiple models / variants / seeds, but cannot
be squeezed into an overnight slot.

## What we *could* do overnight if we wanted some tau2 movement

**Option A — fresh-sim cross-model**: run `S0 + AO + S2 + S3 × {gpt-5.4,
Kimi-K2.6}` on telecom_small (20 tasks each). Per cell ~1.5–2h.
Total 4 strategies × 2 models × 2h ÷ 8-parallel = ~1.5-2h wall.
**Feasible in an overnight slot**, but tonight is already booked.

**Option B — fresh-sim seeds for existing best variant**: take the
current best tau2 strategy (S2, v10.4) and re-run 3 seeds on
gpt-5-mini (the paper config) for tighter error bars. ~3h wall.

Neither option fills the mega table — it expands one column.

## Recommendation for the paper's mega table

Tonight: **leave tau2 row sparse** (with explicit "future work"
caveat).

Next overnight: pick **Option A** (cross-model fresh-sim) to fill in
2 more tau2 cells.

After that: prioritize the replay infra (~2 dev-days) before further
tau2 expansion.

## Related docs

- `docs/tau2.md` — benchmark overview.
- `docs/tau2_absorption_decision.md` — repo-layout decision (federation
  via ctx_edit fork; not absorbed into ctx_editor).
