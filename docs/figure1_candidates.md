# Figure 1 Overhaul — Candidate Examples

**Goal**: Two subfigures. (a) Context pollution — outdated assumption persists and misleads. (b) Statefulness — AO destroys essential accumulated state, leaving the assistant stranded. Ideally both use the same example.

**Key shift from prior version**: We now need agentic/SWE-bench/tau2-bench style examples (tool use, file edits, environment state) rather than pure code-generation or math examples. The example must motivate *selective* context curation — not just AO — by showing both the pollution problem AND the statefulness problem.

---

## Candidate 1: SWE-bench style — Debugging a test failure **(recommended)**

### Subfigure (a): Context Pollution

```
Turn 1 [User]:  CI is failing. test_process_order raises
                TypeError: unsupported operand '+' for Decimal and float

Turn 1 [Asst]:  [read tests/test_orders.py] → sees Decimal("9.99") + tax_rate
                The error is a type mismatch — tax_rate is a float but the
                prices are Decimal. Converting tax_rate to Decimal in
                compute_total():
                [edit orders.py:47] tax = price * Decimal(str(tax_rate))
                ✓ This should fix the type error.

Turn 2 [User]:  That fixed the TypeError, but now the same test fails with:
                AssertionError: expected Decimal("10.79") got Decimal("10.78").
                Actually — we changed the rounding policy to ROUND_CEILING
                last sprint for tax calculations.

Turn 3 [Asst]:  [read orders.py] → sees quantize(Decimal("0.01"))
                [edit orders.py:48] ...quantize(..., rounding=ROUND_CEILING)
                ✓ Fixed. Tax now rounds up per the new policy.
                                     ⋮
Turn N [User]:  test_apply_discount is also failing now.

Turn N [Asst]:  This is likely another Decimal/float mismatch in the discount
                path. Let me check if discount_rate also needs the Decimal
                conversion...
                [read orders.py:60-80] → discount_rate is already Decimal ✓
                Hmm, maybe the rounding mode is wrong here too...
```

**Pollution mechanism**: The Turn 1 "type mismatch" framing persists — the assistant keeps hunting for Decimal/float issues and rounding problems, when `test_apply_discount` actually fails because the discount is applied *after* tax instead of before (a logic ordering bug unrelated to types).

### Subfigure (b): Why AO is destructive (same conversation)

Under Assistant-Omitted, at Turn N the model sees:

```
Turn 1 [User]:  CI is failing. test_process_order raises TypeError...
Turn 1 [Asst]:  [omitted]
Turn 2 [User]:  That fixed the TypeError, but now... we changed the
                rounding policy to ROUND_CEILING last sprint.
Turn 2 [Asst]:  [omitted]
                                     ⋮
Turn N [User]:  test_apply_discount is also failing now.
```

The assistant doesn't know:
- It already edited `orders.py` **twice** (those changes are on disk)
- What the current state of the file looks like
- Which fixes were already applied and verified
- What diagnostic steps were already taken

It's **stranded** — forced to re-read files it already modified, potentially confused by its own uncommitted changes, and may try to re-apply fixes that already exist.

### Strengths
- Software engineering audience will immediately grok it
- Pollution is visceral — "type mismatch" is a specific frame, and you can see exactly how it biases Turn N
- Statefulness is concrete — file edits on disk, test results observed, diagnostic state accumulated
- Both subfigures use the same conversation

### Weaknesses
- Somewhat dense for a figure — the Decimal/float detail may take a moment to parse
- The "rounding" middle turn adds realism but also complexity

---

## Candidate 2: Tau2-bench style — Telecom troubleshooting

### Subfigure (a): Context Pollution

```
Turn 1 [User]:  My phone can't connect to mobile data.

Turn 1 [Asst]:  [tool: lookup_account(id=5827)]
                → plan: prepaid, balance: $0.00, data: enabled
                Your prepaid balance is $0 — data service is
                suspended. Please add funds to restore connectivity.

Turn 2 [User]:  I switched to a postpaid plan at the store
                yesterday. Can you check again?

Turn 3 [Asst]:  [tool: lookup_account(id=5827)]
                → plan: postpaid, balance: n/a, data: enabled
                You're right, the plan shows postpaid now. But the
                data service configuration may not have migrated
                cleanly.
                [tool: reprovision_data(id=5827)]  ✓ Reprovisioned.
                Try restarting your phone.
                                     ⋮
Turn N [User]:  Still not working. And I also can't send MMS.

Turn N [Asst]:  MMS also requires an active data balance. Since your
                account showed $0 earlier, MMS would be blocked as
                well. Let me check if the balance...
```

**Pollution mechanism**: The Turn 1 "$0 balance / prepaid" framing anchors the assistant. At Turn N it reverts to the balance explanation even though the account is now postpaid (where balance is irrelevant). The actual issue is likely airplane mode or a SIM reseat — things requiring user-side action.

### Subfigure (b): Why AO is destructive (same conversation)

Under AO, the assistant at Turn N doesn't know:
- It already ran `reprovision_data` — running it again could cause a **double-provision error**
- The account lookup results from Turn 3 (plan=postpaid, data=enabled)
- That the user already tried restarting (per Turn 3's suggestion)
- What diagnostic steps have been exhausted

### Strengths
- Directly mirrors tau2-bench's telecom domain (cited in the paper)
- Tool call results are the clearest example of irreplaceable state
- Accessible to non-SWE readers — everyone has called tech support
- The "double-provision" risk makes AO's danger very concrete

### Weaknesses
- Tool-call notation takes more figure space
- Telecom-specific details (prepaid/postpaid, MMS, SIM) may be less familiar to some ML readers

---

## Candidate 3: Config migration debugging (simpler, less dramatic)

### Subfigure (a): Context Pollution

```
Turn 1 [User]:  App crashes on startup after upgrading to v3.
                Error: KeyError: 'db_host'

Turn 1 [Asst]:  [read config.yaml] → sees db_host, db_port, db_name
                The config uses the old flat key format. V3 expects
                nested keys:
                [edit config.yaml] database: {host: ..., port: ..., name: ...}

Turn 2 [User]:  Still crashes — same KeyError. Oh wait, I have a
                config override in /etc/app/config.local.yaml too.
                                     ⋮
Turn N [User]:  Now I'm getting ConnectionRefused on port 5432.

Turn N [Asst]:  The database config migration likely left the port
                in the old flat format. Let me check if 'db_port'
                needs to be nested too...
```

**Pollution mechanism**: The "config format migration" frame from Turn 1 persists. At Turn N the assistant assumes ConnectionRefused is another config formatting issue, when the actual problem is the database server isn't running.

### Subfigure (b): Why AO is destructive

Under AO:
- The assistant doesn't know it already edited `config.yaml`
- The current file state on disk reflects edits it has no memory of
- It may try to re-apply the same migration or make conflicting edits

### Strengths
- Very concise — fewer turns needed
- Simple to follow

### Weaknesses
- Pollution is less dramatic — ConnectionRefused → config format is a plausible (if wrong) hypothesis, so it doesn't feel as clearly "anchored"
- Only one file edit, so statefulness argument is weaker

---

## Comparison

| Criterion                        | Candidate 1 (SWE-bench) | Candidate 2 (Telecom) | Candidate 3 (Config) |
|----------------------------------|------------------------|-----------------------|---------------------|
| Audience fit                     | SWE / ML researchers   | General               | SWE / ML researchers |
| Pollution clarity                | High — "type mismatch" frame persists into unrelated bug | High — "prepaid $0" persists after plan change | Medium — plausible misdiagnosis |
| Statefulness clarity             | High — file edits on disk, test results | High — tool calls, double-provision risk | Medium — just one file edit |
| Conciseness for figure           | ~5 turns + ellipsis    | ~4 turns + ellipsis   | ~3 turns + ellipsis |
| Same example for both subfigs    | ✓                      | ✓                     | ✓ |
| Benchmark alignment              | SWE-bench              | Tau2-bench            | Neither specifically |
| Risk of reading as capability failure | Low — type mismatch is a *frame*, not ignorance | Low — clear anchoring on stale data | Medium — could seem like model doesn't know DB basics |

**Recommendation**: Candidate 1 for SWE-focused venues, Candidate 2 for broader ML audience. Candidate 1 has the strongest pollution mechanism because "type mismatch" is a very specific diagnostic frame that clearly wouldn't arise in a single-turn setting given the full history.
