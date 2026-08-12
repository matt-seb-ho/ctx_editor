# Reply to Reviewer 5YHP (follow-up): the detector evaluation

In our initial reply we agreed with W5 and committed to evaluating the analyzer directly as a detector. We built it, with no judge in the label path so the evaluation cannot be circular. Two studies, reported in full including the parts that do not flatter us.

## 1. Constructed pollution, ground-truth labels (the ceiling)

Into 145 LiC database and code conversations we injected two assistant-side spans each, one known-false and one known-true, in an identical surface frame anchored on a rare token. Labels are correct by construction; no judge is involved. Four offline controls calibrate the metric: an identity editor scores 0.00 removal, a hand-removal oracle 1.00, and a delete-everything editor 1.00 removal / 0.00 preservation, which is what makes preservation, not removal, the metric that cannot be gamed.

AC3-Reset (n=126): removal **97.6%** (123/126); names the pollutant explicitly in its `issues` output **78.6%** (89.7% on the causally-harmful subset); gate sensitivity 98.4%.

The detection is real; the selectivity is not, and we say so. Preservation is 4% and edit precision sits at chance: Reset removes correct injected content at nearly the same rate as false content. That is a description, not a defect. Reset discards the assistant side and re-derives the task from the user side, so per-span precision is not a property it was built to have, and the delete-everything control is its reference class. The compacting operator, Rewrite, removes only 27% here, so the metric is not saturated by construction. One caveat we put first in our own writeup: injected spans may be more salient than natural pollution, so these are an upper bound. The second study closes that.

## 2. Natural spans, causal labels (no LLM anywhere in the label path)

For **111 spans** occurring naturally in **30 LiC conversations** (the assistant's own prose and code, nothing injected), we re-ran the final turn with each span present and with it removed, byte-identical otherwise (**3,357 assistant turns**, 0 errors). A span is causally harmful if removal raises accuracy, useful if removal lowers it. The label is a measured accuracy difference; no detector, no judge, no LLM. Three controls pass: a contentless span +0.033 (n.s.), the injected pollutant +0.368, the full-spec plus gold-SQL span −0.447. The harness resolves large effects in both directions and reports near zero when nothing is there.

Three results, one of them against us:

1. **Natural pollution is real and concentrated.** The spread of per-span effects beats a replicate-matched null (SD 0.155 vs 0.125, p=0.0085; 16 spans with |Δ|≥0.25 where the null predicts 9.3, p=0.017), while the mean span is inert (+0.020). Pollution is carried by a minority of spans, not a fog over the whole history. This is the first causal characterization of the phenomenon the paper is about.
2. **AC3 removes what is doing the damage:** removal on causally-harmful spans **100%** (7/7).
3. **Neither operator is span-selective.** Reset keeps 5 of 66 probe-admissible spans, Rewrite 0 of 66; preservation on causally-useful spans is 0%. A label-free test agrees: the mean effect of the spans Reset removed minus those it kept is −0.014 (permutation p=0.85), where a selective editor should score positive.

## 3. What this says about the mechanism

Read alongside the non-selectivity in Study 2, the picture is consistent: AC3 works by rebuilding rather than by surgical excision. It **detects, discards the assistant side, and reconstructs the specification from the user side** (Reset by dropping that side outright, Rewrite by recompacting it), and the accuracy gain comes from that reconstruction, not from a span-by-span preserve/remove decision. This is also the precise scope of your W1: structural exclusion is safe exactly where user turns independently specify the task, which is what these edits reconstruct.

Detection is unaffected, since it is measured before the editor acts; the causal factorial is unaffected; and the natural-span study adds evidence we did not previously have, that on conversations chosen without reference to what AC3 would do to them, it removes 100% of the spans a judge-free counterfactual proves harmful.
