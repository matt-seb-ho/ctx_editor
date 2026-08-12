# Final note to the Area Chair (discussion period)

Thank you for arbitrating this submission. As the window closes, a compact summary of the contribution and where the evidence now stands.

**Problem and contribution.** Multi-turn degradation is large and well-documented, and the standard remedy, omitting assistant turns, collapses to **0% on stateful tool use (tau2)** because it deletes state the task needs. AC3 treats conversational context as heterogeneous rather than uniformly harmful: one analyzer feeding a small family of editing operators, with **at least one operator improving in every evaluated regime**. The transferable insight is that the assistant's own turns are the pollutant, and editing them selectively beats both keeping them and blanket-deleting them.

**Where the evidence now stands, against all three meta-review pillars:**

- **Robustness, scale, generalizability.** 5 analyzers across 4 model families, all positive (**+12.9 to +39.9pp**); item-level McNemar **+15.4pp [+11.5, +19.4]** over **1,668 items**; LiC scaled to n≈113–150/cell; memory contamination measured at zero.
- **Baselines (experimental evidence).** The stronger baselines requested in review: a faithful per-turn condenser at matched budget does not close the LiC gap (database 47.7–53.3% vs 56.1%; AC3-Reset 75.7%) and by instrumentation over-consumed AC3 (1.02–1.19× calls, 1.62–2.14× tokens); a neutral-prompt variant reproduces it (51.4%). MT-OSC (no code release) reimplemented at its published setting.
- **Pollution measured directly, no judge in the label path (theoretical validity).** Constructed injection with ground-truth labels: **97.6%** removal. Causal counterfactual span ablation over **3,357 turns**: AC3 removes **100%** of causally-harmful natural spans. The assumption is now grounded empirically, not asserted.

The central LiC claim held under every metric variant we could construct, the baselines you and the reviewers asked for were delivered, and where re-measurement moved our own numbers (detailed in the reviewer threads) we corrected them against ourselves. Thank you for the careful handling.
