# Follow-ups from the AC3 overnight batch

Tracked items the overnight run surfaced that should be addressed next.

## Engineering

- **`huang_eval/run_phase2.py` needs `load_balancer_config` plumbing.**
  Currently calls `get_model_client(cfg.respondent_model)` with no load
  balancer, so Foundry-routed models (DeepSeek-V4-Flash, Kimi-K2.6, gpt-5.5)
  silently 404 against the default Azure OpenAI endpoint pool. This is why
  Phase 3b's first attempt produced 0-evaluated-turn cells. Fix: pull a
  `load_balancer` field from the Hydra config (default null), instantiate
  the LB config when present, pass through. Small change but quietly broke
  one of the headline phases tonight.

- **`AnalysisCache._hash_trace` empty-string-role fix landed at `cf00efd`** —
  affected only Kimi math conv0 in Phase 2 (Augment + Reset cells, 9 of 48
  problems each errored). All subsequent cells are clean.

- **gpt-5.5 deferred** for cost/throughput reasons after Kimi finished at
  ~07:30. Add a Phase 2 follow-on with gpt-5.5 (and possibly other foundry
  models) when there's a longer overnight window.

- **Phase 2 aggregator regex** in `scripts/aggregate_ac3_phase.py` matches
  LiC-style cell names (`{exp}_{task}_v2_conv{c}_{ts}`). It silently dropped
  CollabLLM cells (`{exp}_{dataset}_rep{N}_{ts}`). Generalize the regex or
  add a CollabLLM-specific aggregator.

- **Huang eval's summary writer doesn't print Augment win rates**, only S3
  (which it labels "S3"). Phase 3b's Augment numbers were re-computed by
  hand from `turn_results.jsonl`. Add Augment / S2 / S15 sections to
  `huang_eval/aggregate.py:format_summary`.

## Experimental follow-ups

- **Multi-turn AC3 + gating** (deferred from rev.2 of the plan). Phase 3a's
  CollabLLM Augment regression (-10pp vs baseline; bigcodebench errors
  climbing across reps as conversations balloon) suggests AC3 needs the gate
  in multi-turn settings. The Phase 1 gating result (Gated-Reset ≈ Reset in
  last-turn replay) doesn't generalize — the question is empirical for
  multi-turn fresh sims. A targeted experiment (DeepSeek, math+database,
  always-on Reset vs Gated-Reset) is the next high-value step. Budget
  estimate from rev.2: ~10-12h overnight.

- **Phase 3a re-do with Reset on stronger models** (gpt-5.4, Kimi). Tonight's
  Phase 3a used DeepSeek-V4-Flash, where AC3 was already weaker on LiC. The
  Phase 2 pattern was "AC3 wins more on stronger models" — worth retesting
  CollabLLM with gpt-5.4 to see if the AC3 vs AO ranking flips here too.

- **Phase 3b with DeepSeek-V4-Flash** once the load-balancer fix lands. The
  current Phase 3b numbers are gpt-5-mini only; the cross-model AC3
  generalization story has a gap.

- **Bigcodebench**: every Baseline / AO / Augment trial on DeepSeek returned
  0/20. Either the dataset is too hard for this model class or there's a
  systematic eval-mismatch issue. Inspect a few sample outputs vs gold to
  rule out a grading bug.

- **Variance bound on AO Phase 3a math-hard**: AO came in at 40% ± 5pp (n=3
  reps × 20 problems). Worth a 1-model probe at n=5+ reps to tighten the
  envelope before any paper claim "AO beats AC3 on CollabLLM math by X pp".

## Paper-narrative items

- **Cross-benchmark story split**:
  - LiC (last-turn replay): AC3-Reset competitive with / better than AO,
    especially on database (+25pp).
  - WildChat: AC3 dominates (~90% win-rate vs AO at gpt-5-mini).
  - CollabLLM: AO ahead; AC3-Augment regresses. Multi-turn fresh-sim effect.
  Write this up clearly. It complicates the "AC3 is the answer everywhere"
  narrative but actually strengthens the science — we identify where the
  method works and where it needs refinement.

- **Per-task pattern on LiC**: AC3 dominates database (+25pp over AO),
  ties on math/code/actions. The database win is the cleanest story:
  database's system prompt carries the SQL schema (load-bearing); AO drops
  the assistant's reasoning context but keeps schema, while AC3 preserves
  both schema *and* a clean restatement of user intent. Worth a paragraph
  in the paper.

- **Conversation-length sensitivity**: WildChat (median 6-10 turns) ≠
  CollabLLM (median 14 turns) ≠ LiC last-turn replay (1 turn of
  intervention). Augment's pile-on is a real failure mode at longer
  conversation lengths. Gating is the obvious mitigation.

- **Foundry pricing**: the user populated `foundry_pricing.yaml` — once
  the aggregator runs with that priced in, fold dollar costs into the
  report tables.
