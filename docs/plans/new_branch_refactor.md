# New Branch Refactor TODO
More work has been done and documented in `docs/plans/resume_state.md`

In particular with some prompt adjustments and swapping the user model to gpt-4o, we got some really excellent trending results on code.

We're currently working on checking if those results hold for the agentic memory and then for other tasks.

That's on another machine. I'd like for you to help me with a refactor that MUST BE ON A DIFFERENT BRANCH.

I have a bunch of assorted ideas including
- changing the conversational format
- centralizing conversational analysis as the main operation
- baking error attribution into the experiments
- delaying the first convo analysis operation until later across the board to just save time and tokens on earlier turns (for eval, only the very last turn matters, but for realism we need the turn before that to also potentially be analyzed and rewritten)

As always please maintain the documentation and also periodically git commit for each major feature set of this refactor. Remember the format is one-line subject line ONLY we don't want huge multiline bodies clogging our git log so please follow the format of "feat/fix/chore: one-liner description" and do NOT waste tokens/space putting the full body or signing that you co-authored the commit. That will be evident from our paper and the readme at the end.

**Git Branches**
- create and switch to new git branch `newleaf`
- please make sure you're not messing with main

**Conversational Format**
- refactor to use revamped conversation format sent to assistant model
	- please read the formatting aside below
- We use chat completions API where we send a chat history and the API responds with the assistant's message.
- To simulate multi-turn conversation, we have 2 options:
	1. send the conversation history as the `list[messages]`: use the API as intended
	2. render the conversation history as a string inside a single user message + along with a prompt for the assistant to respond

- Option (1) is likely how the model was trained
- Option (2) gives us full control of rendering for novel components and is API agnostic
	- can easily justify either way, we previously used Option (1), but want to swap to Option (2)

- Under Option 2 the chat history object sent to the API to request the assistant message would be like this:
```json
[
	{
		"role": "system",
		"content": "SYSTEM MESSAGE HERE, SAME AS BEFORE"
	},
	{
		"role": "user"
		"content": "Here is the current conversation:\n\n[CONTENT]\n\nPlease respond to the user and do not include the [assistant] tag."
	}
]
```

- where `[CONTENT]` would look like this
```
[user]
I want request X

[assistant]
initial response Y1

[user]
also make sure we have constraint C

[assistant]
next response Y2
```

- I think the user simulator currently looks at something similar, so we just need to update so the assistant model sees the same format.

- The main motivation for this change is to easily add arbitrary messages into context that need not fit OpenAI's API requirement for `list[message]` 

- Example 1: appending the analysis
```
...
{
	"role": "user"
	"content": "Here is the current conversation:\n\n[CONTENT]\n\nHere is an independent model's analysis:\n\n[ANALYSIS]\n\nPlease respond to the user and do not include the [assistant] tag."
}
```

- Example 2: kicking off a new conversation thread with edited context
```json
...
{
	"role": "user",
	"content": "Here is a concise version of the conversation as summarized by an independent checker:\n\n[EDITED_CONTEXT]\n\nPlease respond as the assistant."
}
```

- By the way this also requires a minor change to how we present the conversation to the user simulator. In particular the context rephrase new conversation kick-off is no longer expressed as a normal user-assistant exchange. I'll let you decide how to handle this but I feel that maybe rendering the initial message as a system message could be useful? Here's one possible set up. Just pick something that's clean and makes sense.

```
Here's the conversation so far:
[system restart]
Here is the conversational state as summarized by an independent analyst:

[EDITED CONTEXT]

Please resume the conversation as the assistant.
```

**Error Attribution**
- right now we have error attribution as an independent script that has to be run separately from the main experiment, let's allow 2 optional ways to run it alongside the main simulation:
	- option 1. perform the error attribution immediately after simulating a conversation
	- option 2. wait until all conversation simulations are complete to run error attribution in batches before reporting the scoring results/summary 
	- the reason we have option 1 is to enable online, on-policy memory learning where immediately after a conversation is simulated we check if the error is from some external factor (user sim, extraction error) and therefore not worth reflecting on this instance to update memory.
		- let me know if this makes sense or if we should just always try to squeeze out any learning signal independently of the validity of the eval code labeled the conversation's final response as correct or not

**Conversational Analysis as the Central Mechanism**
- all settings require conversational analysis and other pieces like actually editing context is relatively easy once the analysis is done. Being discerning about the user's intent, and whether or not the assistant approach still makes sense to keep is the main job, everything else is downstream of this analysis.
- **implement the conversation analysis as a first-class component**
	- analysis is about (1) understanding what the user is asking for (2) summarizing the assistant's approach (2.1) decide whether a pivot is called for
		- underlying question is "given the latest user message, do we need to backtrack on what the assistant previously tried?"
			- what's distracting?
			- what's misleading?
			- what assumptions are correct/incorrect?
			- what's still reasonable under the latest info?
		- on the prompt side of things
			- it might be useful to frame it not as self-reflection but more like independent review: e.g. this is a conversation between a user and an AI model, please critically analyze this conversation etc.
				- the idea here is to avoid biasing model one way or another by suggesting either the user wrote those responses or that the analyst model itself wrote those responses it's analyzing now. There is a prompting trick some people use for debating LMs where they say "some contractor wrote this code, please analyze it critically" or "some stranger debating me had this argument, please weigh in" (because the model tends to be overly obsequious towards the user's self purported views) so we're borrowing that principle to make our analyst more unbiased
			- I also want to explain/mention the failure modes:
				- "often times in early stages of a conversation an AI agent might make some assumptions to start tackling an underspecified question/task but then it later over-commits to its initial ideas even though looking at just the user messages might suggest going another direction. In other words models might get distracted by their prior outputs and are unlikely to backtrack on an incorrect partial solution. Your analysis is about precisely looking for this behaviour and discerning if the user messages suggest that a backtrack/removal of certain items from the assistant's output could be useful."
				- something to this effect, I'll leave the details to you
		- design question: do we generate (1) separately by only looking at user messages?
			- for simplicity let's default to single query for the whole analysis 
	- instead of being a vaguely similar operation used in reflection-only, context-edit and agentic-edit, let's actually formalize this operation so it can be cleanly reused elsewhere
	- notation: for turn i, in response to latest user message U_i we're interested in generating an analysis A_i of the current conversation and then the assistant's response R_i
		- we first generate analysis `A_i  = model.generate([(U_1, R_1), (U_2, R_2), ..., (U_{i-1}, R_{i-1}), U_i])`
		- then we generate assistant response `A_i  = model.generate([(U_1, R_1), (U_2, R_2), ..., (U_{i-1}, R_{i-1}), U_i, A_i])`
		- notice that when generating A_i, the input context does not contain the previous A_j where j < i.

**Simplify Settings to Test**
- Simplify the 4 settings down to 3.
	- S0 baseline is the same as before
	- S1 append analysis is the old "reflection-only"
	- S2 context edit is what we previously called "agentic-edit"
- motivation: with the first-class analysis component bearing all the weight (which makes sense because once that analysis is complete, actually putting the context together according to that analysis should be simple), we can focus on targeting this component with the memory learning module
	
S0 BASELINE
- establish baseline 3x runs per task on full set

S1 APPEND ONLY
- test conversation analysis append
- before each turn we perform convo analysis and the assistant sees full convo + analysis and we prompt it to give the next turn

- ideal outcome: performance up compared to baseline

S2 CONTEXT EDIT
- still do the same analysis
- analysis concludes that pivot is needed?
	- no: proceed normally with the current conversation like S0
	- yes: instead of appending this analysis to the conversation history, use the analysis to produce a compacted conversation state:
		- user request (collated)
		- useful intermediates
		- discarded intermediates(?)
			- this is a design choice
- ideal outcome: performance up compared to S1

**Establish New Minimum Turns before first analysis is triggered**
- running an analysis for every conversational turn essentially doubles latency of the simulation
- it doesn't really matter how many times the analysis is run on a given conversation, ultimately we need to get it right on the last shard so let's do a per-task threshold where we first programmatically check all the tasks we're simulating on and then find the minimum number of shards. If the minimum number of shards is 5 for example, let's set the skip turns to 3, so that at least 2 analyses are done for each conversation (i.e. do analysis after shard 4 is revealed and after shard 5 is revealed.)
- The point here being that in the S2 Context Edit setting we need to account for analyzing and rewriting for a conversation that maybe already has gone through this previously

**Make sure the memory stuff works like it did previously.**

---

## Implementation Progress (newleaf branch)

All items below are implemented. See `docs/newleaf_refactor.md` for detailed documentation.

- [x] Create `newleaf` branch
- [x] Conversation format: Option 2 (render as tagged string in single user message)
- [x] ConversationAnalyzer: first-class component in `strategies/analyzer.py`
- [x] S1 AppendAnalysisStrategy: `strategies/append_analysis.py`
- [x] S2 ContextEditV2Strategy: `strategies/context_edit_v2.py`
- [x] Error attribution integration (immediate + batch modes)
- [x] Auto min_turns computation from task shard counts
- [x] Memory compatibility verified (analyzer, assistant targets)
- [x] New experiment configs (append_analysis, context_edit_v2, + memory variants)
- [x] Old strategies preserved for backward compatibility
- [x] Documentation in `docs/newleaf_refactor.md`

### Regarding error attribution for online memory learning
The immediate mode fires error attribution right after each conversation. This could be used to filter out false negatives before updating memory. For now it collects results in parallel — the integration with the memory updater (skip reflection for non-assistant errors) can be wired up as a follow-on if the approach proves useful. Alternatively, always learning from all trajectories may be simpler and still extract useful signal even from noisy labels.
