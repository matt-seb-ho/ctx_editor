
Here are your new overnight project instructions.

## Task 1: Explore Rewrite Further

Ok so you tried to improve over AC3-Rewrite with a v2 of it that didn't pan out at all.

The reason we care is that we think that AC3-Rewrite should be more expressive compared to the templated setup of AC3-Reset. The idea being that decomposing the task of preparing a new cleaned up context is probably easier if you spend one LLM query only focusing on analyzing the conversation to understand what has been done and if this is problematic and then doing an explicit second LLM query to convert that analysis (and the conversation) into a new cleaned up context.

We expected that this decomposition might be better than 
1. asking the LLM to do both analysis and rewrite in a single query 
	- because of separation of concerns
2. using the outputs of the analysis to fill in a template that forms the new cleaned up context (AC3-Reset) 
	- because of improved flexibility (can move things around, rephrase to make things smooth, etc.)

We expected this to be good both for (1) removing pollution and (2) organizing context in a way more conducive to task completion (i.e. this last rewrite query effectively serves as on the fly LLM-driven prompt engineering for the assistant to finish out the task).

We are very surprised that currently reset is not only beating rewrite but rewrite is hanging at the same performance level as the baseline (i.e. equivalent to not intervening at all). First and foremost we should probably note this down in the paper that a naive rewrite operation counterintuitively isn't going to help. The current hypothesis is that the extra query adds extra noise which distracts the LLM.

### Task 1.1: Analysis: Why is this the case?

I want you to do analysis to determine what's going on between rewrite (v1) and reset.

For each of the problems where the reset version is outperforming, please check the actual edited context that is sent to the assistant LLM for each treatment. This should be available by lookinggg at the traces of the previous runs. Basically each of reset and rewrite prepare the context for which the assistant LLM reads and produces the final answer for that attempt. Please compare (1) what each prepared context contains (2) the answer the assistant makes (3) attributing any failures in the answer to prepared context or some other factor (4) attributing the prepared context to our prompt/conversation it was looking at.

The question to answer are:
1. how do the prepared contexts differ
2. how do the assistant's final answers differ
3. how does the rewrite bad answer relate to/flow from its prepared context as compared to the reset context
4. why did the rewrite context end up this way (is it due to the inputs of the rewrite operation (i.e. analysis outputs? rewrite prompt? conversation itself?)

Please do not go through all of these yourself. Please go through a few examples, and then write scripts that call deepseek-v4-flash to do this analysis. Basically I want you to act as the leader/manager for this analysis. You first check out a few cases yourself to understand the shape, and then you write analysis scripts to dole out the actual work to a cheaper worker model (dsv4f). You can also make a hierarchical analysis where you write scripts to read/aggregate the outputs of another set of dsv4f scripts. Basically I want you to mostly delegate work out to other models and only do a small amount of analysis yourself, and mostly focus on reading the reports and then aggregating that into a coherent explanation of **"why is rewrite currently underperforming reset?"**

### Task 1.2: Problem Solving: Try some interventions and see if we can change this fact

We think there are 3 ways to go about additional exploration of this problem (i.e. trying to resolve this and find a configuration where rewrite is indeed better to match our expectations that more expressive power = better).

These ideas are currently purely driven by intuition without analysis. I think after you complete task 1.1, you will have a much stronger understanding of why is happening and what we can do to address it.

I think you should try to leverage your 1.1 analysis to propose the most effective intervention to try to get rewrite to outperform at least the baseline.

That said, here are my underinformed ideas that you can consider as inspiration:

#### Task 1.2a: Middle Ground

So we know for a fact that we can do better than the current rewrite because there exists a function that maps analysis outputs to a new context that results in better task outcomes-- the rewrite template filling.

So we can prompt the LLM to make the rewrite operation basically an LLM executed template filling. This is obviously somewhat wasteful because why do something with an LLM that can be done programmatically/deterministically.

So proposal 1 is to try to find some middle ground between the current rewrite prompt and this template filling idea. In other words, try to make our LLM rewrite operation closer to the template filling operation but obviously trying to take advantage of the unique strengths of relying on an LLM

#### Task 1.2b: Toggling Access to the Original Conversation (and Variant)

In the paper we wrote about how if the first part of our pipeline (consolidate task spec) sees the full conversation and not just the user messages, then we observe downstream performance degradation worse than the baseline. The conclusion there was that context pollution could be contagious and needs to be managed even for the subagents that are working on identifying/cleaning up pollution for the main agent.

I was looking at the Rewrite operation and I noticed that the Rewrite operation's LLM query feeds the whole conversation so far in addition to the task spec and analysis outputs. I suspect that it's possible that having the full conversation at the bottom (most recent) in the context window is distracting the rewriter model. In other words, is it possible that even the rewriter is impacted by the contagious context pollution?

It might be useful to do small, quick ablations to see if either of the following helps:
1. having the analysis below the conversation in the input context to the LLM rewrite operation (i.e. more recent) helps mitigate the pollution contagion
2. what if we remove the conversation entirely, and the LLM query is only about reading the user spec, and the analysis and repackaging that as a nice context for the next turns.

#### Task 1.2c: Automatic Optimization

Ok again this is similar to Task 1.2a, but instead of me specifying that you should try to update the prompt to be more similar to the reset operation, maybe we take the "bitter lesson" approach of just doing search and optimizing this operation's prompt directly.

Please download and read ([[2507.19457] GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457)), and also its follow up work ([[2604.04247] Combee: Scaling Prompt Learning for Self-Improving Language Model Agents](https://arxiv.org/abs/2604.04247)), and also their blog: [optimize_anything: A Universal API for Optimizing any Text Parameter - GEPA](https://gepa-ai.github.io/gepa/blog/2026/02/18/introducing-optimize-anything/).
- here is a GEPA precursor btw, also about prompt optimization: [[2406.07496] TextGrad: Automatic "Differentiation" via Text](https://arxiv.org/abs/2406.07496)
- the optimize anything blog also emphasizes how although GEPA was initially for prompt optimization, it can optimize any text, which includes code, which includes the harness for an agent
	- the relation to our case is that we might be able to use GEPA to both optimize the prompt for the rewrite operation but also control flow (what inputs do we want to GEPA, following 1.2b, maybe we remove the full conversation input to the rewrite operation)

Please read each of these things and take notes.

There exist pretty excellent work on prompt optimization. The basic idea is that we already have all the inputs to the rewrite operation, so it's just a matter of optimizing its prompt and what inputs we need against some metric (LiC benchmark scores).

I cloned the gepa and textgrad repositories to ~/code_ref if you need to reference them. I would recommend preferring gepa and reading its docs at [Quick Start - GEPA](https://gepa-ai.github.io/gepa/guides/quickstart/)

For Task 1.2, you don't actually need to follow all of these. In fact you can make your own choices about what strategy actually makes the most sense for getting rewrite to be good from your analysis in 1.1. Don't feel the need to try everything I mentioned. Can stop whenever you find a configuration that (1) gets good performance (beating baseline at least, competitive or winning against reset) (2) makes sense for non LiC tasks well/can be easily adapted.

## Task 2:  Fill out the remaining table cells

We initially proposed a 3-D mega table for this post-neurips set of runs so we can bulk up our main table.

The main table would be (benchmarks: LiC, CollabLLM, WildChat, tau2) x (models: GPT-5.4, DeepSeek-v4-Flash, Kimi K2.6) x (methods: baseline, AO, AC3 variants).

I think we only have the LiC subtable filled out with all models and methods.

I think we need to start filling out the remaining CollabLLM, WildChat, tau2 cells with different models and maybe different methods.

In terms of engineering work I think tau2 is the trickiest because it's unclear if we can/should implement last turn replay to speed this up or if we truly just need to run a new simulation every time.

For the other 2 benchmarks we should definitely have different models and different methods (multiple AC3 variants: augment vs. reset vs. rewrite) where rewrite is revamped from your effort in Task 1

# Guidelines

This is yet another overnight task for you. This means that you're in charge of making reasonable decisions instead of getting blocked and waiting for my input (I'll be sleeping). Please record your progress, your decisions, and experiments in a markdown file. For experiments, as always, I want you to record run commands, output file/directory locations, scores, and takeaways.

Best of luck. Be smart. Make good choices.

