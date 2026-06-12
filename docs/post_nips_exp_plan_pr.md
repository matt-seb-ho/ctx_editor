Onwards to the AC3 experiments.

Can you check which prompt version we currently have as default? Can you check which prompts were used for LiC paper experiments (there should be a documentation markdown file somewhere that explains the correspondence between reported paper results and experiment report markdown files/config info)?

There are 2 decision points I want to discuss with you before proceeding.

1. Do we make any adjustments to the paper prompts before proceeding?
	- The impetus is for this discussion is that in the paper we kinda explore subtly different interventions on the different benchmarks
	- It makes sense to have some differences/adjustments between the pure conversation benchmarks (LiC, CollabLLM, WildChat) vs. the more agentic one (tau 2), but we probably should have normalized across LiC, CollabLLM, WildChat
	- The reason this was done was because the non LiC benchmarks were extremely last minute, desperation moves to show our method can win (it was really hard to beat AO on LiC where AO is basically the upper bound by basically recovering the single turn setting). As a result, I made any adjustment I thought would bolster the chances of getting good scores. The downside to this is that there is less consistency across benchmarks which means it's harder to draw particular conclusions
	- I think it's totally fine from a scientific contribution standpoint to present "here are the adjustments you may want to make to adapt to your particular setting", but we want a systematic study/experiments/results to support any suggestions we make.
	- So the potential adjustments would be about trying to test a more consistent intervention across each of the benchmarks (i.e. can we just use the LiC prompts for the other conversation benchmarks or are there adjustments to be made to have a nice general approach that works across all of them)
	- Alternatively, we just test the exact prompt versions from the LiC paper experiments across the 3 conversation benchmarks, which is also ok with me.
2. Do we need to test every treatment across every model?
	- Or do we pick the cheapest/fastest model to test all the variations and then we can scale the most effective setup to the other models?
	- If do the single model exploration -> pick the best setup to scale up, which single model do we choose?
		- Can you briefly remind me how we are estimating costs? And talk me through latency concerns as well
		- Are you using some pricing table I gave you (and calculating with token data) or do the endpoints also send back cost information?
	- My intuition is the DeepSeek-v4-flash is the cheapest, fastest model out of the ones we are considering based on public benchmarks and the official DeepSeek API but in our case we are using some self deployment, so I'm not sure if that real serving cost is identical to what each of these companies charge for their official APIs.

A quick reminder on the different setups:
- augment: this is actually a bit of an ablation: we are verifying the hypothesis that some context pollution is better dealt with by removing the context vs. just appending new context that informs the model to ignore this previous stuff.
- reset vs. rewrite:
	- this is our main methods of curating context
	- we think that rewrite is the more flexible and expressive operation; but the extra LLM call (1) adds extra cost (2) could add extra noise
	- I think in the last round of experiments we determined that reset (which just reorganizes the analysis output into a template-- definitionally less flexible-- is actually sufficient). It's not clear if this scales/holds true for the stronger models we're looking at now
- gating
	- the idea here is whether or not to rework context every turn
	- gating is the mechanism that decides from the analysis whether or not we should even edit context or not
	- in our "replay last turn" experiments we only get one chance to introduce something different from the baseline, so we always do the context edit 
	- but how are we deploying this in the real world?
		- the simplest way we're considering is that every turn we do this analysis (one could imagine this being baked into the model's internal reasoning) and then depending on the analysis deciding to edit context or not
	- there are real costs associated with resetting context every turn:
		- we may not need to-- we may introduce more problems by intervening instead of just letting the LM converse
		- we lose the KV cache of previous conversation and have to start over
	- I think it's fine to only test this on what works best among rewrite/reset

Please deliberate over what we should do for each of the decision points. Weigh the pros and cons to a markdown file and then come to a final decision and design a set of experiments. We can start with LiC, but crucially we want to have experiments across the benchmarks so we're not making unsubstantiated assertions about what works best in different settings.

Please also record the plan to the markdown document. I'll check it over and give approval to start.

There is one more item of concern:
- sometimes we've hit issues with the Azure Content Filter falsely flagging our API requests (LLM queries) as against their policy. This is always incorrect because our content is purely for benchmarking on harmless tasks (math, code, database, actions), but we've run into incidents where analyzing/proposing edits over a previous conversation is incorrectly interpreted by their content filter as a jailbreak attempt.
- Previously I only observed this with the OpenAI models through Azure. I'm not sure if the non-OAI models (e.g. deepseek) are impacted.
- In any case, this may or may not be an issue.
- If it does present itself, we should pivot and try to redesign some prompts to get around this. Again, our content is genuinely safe and harmless so it should  be able to get through. We are merely trying to improve LLMs ability to be helpful in multi-turn conversation.
- I only alert you of this ahead of time so we can plan around the possibility of this being a problem.
