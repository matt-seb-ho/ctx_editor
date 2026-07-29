# Mentor's message

Thanks. I read through the rebuttal, and it's quite good. The new evidence/results answers the AC's "too large for the rebuttal process" directly, so hopefully we can sway them...
 
> the gate opens on at least 97% of text turns (LiC 97.3%, CollabLLM 98.3%), so its errors are dominated by false negatives (missed interventions) rather than spurious harmful edits. 
 
If the gate opens 97% of the time, doesn't that mean it's intervening almost always? so the errors would be false positives?
 
> AC: The reviewers have serious reservations related to [...] validity of **theoretical** assumptions 
 
I don't understand where the "theoretical" part is coming from. Maybe worth pointing out? We could write something like: "We would add that context pollution is a phenomenon characterized empirically rather than formally, with a contribution that is comparable to that of, e.g., Laban et al and Huang et al. Our contribution is in the same register: falsifiable predictions tested against controlled experiments." The AC says "feel free to rebut if the reservations have been made in error", so we could write a polite answer, perhaps with an indirect allusion that "too large for the rebuttal process" may not be an issue.

---

# My reply:

yeah I think the gate opening almost all the time is a bit of a weakness because the explicit purpose is cost saving. I agree that false positive is likely more correct here but this is hard to characterize until we have actual eval on the efficacy in removing pollution (separate from the downstream perf).
 
Yeah I like your response for the theoretical objections, let me iterate around that.
