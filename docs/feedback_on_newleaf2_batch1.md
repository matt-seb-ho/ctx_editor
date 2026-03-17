# My Feedback for the Dev Set Error Analysis 

## Branching Problem

You wrote:
- **The analyzer doesn't detect**:
	- Over-branching / multi-scenario presentation when a single interpretation is natural
	- Failure to commit to an answer within limited turns
	- Wasted turns on unnecessary clarification

So that's details a single problem of over-branching-- i.e. over-branching and its consequences (failing to commit, wasting time waiting on clarification).

I think the single interpretation should be able to be reconstructed or inferred from the analysis. In my head comparing the reconstructed task spec should clarify the interpretation. Or is the observed problem that assistant is reading the last analysis and still being uncertain about the interpretation?
- do you think this is solvable with just changes to analysis/cheatsheet prompts?
- maybe we can correct this in the same way we handle the error attribution?
	- like a post-hoc analysis of the user messages to see if it's really ambiguous and if so then we mark correct if either branch is correct?
	- this obviously complicates evaluation and would cost more so ideally it's solvable from the methods side compared to making the eval more friendly

## S2 Loses Accumulated State for Actions

You wrote:
- S2's context compaction destroys the accumulated state:
	- Old conversation → compacted to task spec + aligned work
	- Assistant sees compacted context + latest user message
	- Assistant responds only to the latest request, not the full accumulated set
	- Ground truth requires all calls in one response

So this problem is especially pronounced for actions because some of the task instances request multiple function calls which naturally gets separated across multiple shards.

Ok I discussed in a separate thread and we found the problem. Or at least, one problem that contributes to this. We hadn't properly considered what happens when S2 has already compacted the conversation and we are doing another analysis. The current code for the analysis just looks at the active user messages which is just the latest message, but it does not include the task spec summarized in the previous analysis/context compaction. Let's correct this. The analyzer, in S2, should read the task spec section of the previous analysis if it exists and the visible user messages to update the task spec. This is the correct and intended behaviour of task spec being produced from user messages.

Another problem maybe is that we can adjust the analyzer's prompt for producing task spec. Unifying/canonizing an organized single task spec is good, but in some cases, the user might really be requesting multiple artifacts (as in the case of the actions, and database tasks). Now this is partially a problem with the way the user simulator handles the sharding for these types of questions where I'm not confident the user simulator is making sufficient demarcations for where one artifact's description ends and another begins. We've been instructed to avoid expending effort in fixing LiC evaluation problems so maybe the prompt change can get sufficient signal. As always, when I suggest a prompt change, I'm suggesting high level ideas, I'll leave the ideal verbiage/construction to you.


## "Memory Injection Harms Actions"

You wrote:
>The cheatsheet learned for S0+mem actions contains analyzer-focused workflow instructions like "If any required information is missing or ambiguous, ask a targeted clarifying question" and "Do not assume sensible defaults for required values." These directly conflict with the actions system prompt which says "You should only return the function calls in your response."

> The cheatsheet is written for the analyzer (target=assistant uses render_for_assistant), but its prescriptive rules about clarification and defaults cause the assistant to ask questions instead of emitting function calls, burning turns.

This does look like a reasonable concern. At the same time I can imagine why the updater model might suggest this strategy in response to seeing perhaps failed trajectory with branched paths.

Ok I have multiple ideas for this problem
1. For the LiC setup we have considered adding explicit prompt guardrails to dissuade the assistant from asking clarifying questions because we've empirically observed that the LiC user simulator seems quite averse to ever responding to a clarifying question. From a research perspective is this defensible. Is this "cheating" in the sense that we're exploiting prior knowledge about the simulation in a way that's hardcoded and not "learned" or is this a reasonable action to take because clarifying question is a good behaviour to learn in more realistic settings but just happens to be maladaptive for LiC evaluation specifically
2. The next idea is to bake error attribution into the cheatsheet updating pipeline. We could treat error attribution as a preprocessing step for our customized version of dynamic cheatsheet. The idea here is that the assistant doesn't really have much to learn if the error in this conversation is the fault of the user simulator, so if the error is attributed to the user/system (not the assistant), then we should skip this trajectory from a cheatsheet update
3. The final point for this problem is that S0 is mostly a baseline. It's true that we want S0 + mem to beat S0 but if memory is maladaptive for only this niche baseline setting, I'm actually ok with that

## S2+mem regresses on math

- S2+mem amplifies the multi-branching tendency
- ok so again we can address the clarification question thing like in the previous point
- are there other behaviours we can adjust prompts around?

## S1 works through passive consolidation

- great that was on purpose, and good to see it's helpful, not entirely surprised by that.
- In general, I really expect the new analysis to be somewhat of a slam dunk because it approximates the concat setting.
- Let's take care to show the promise of S2, of actually rewriting the history

## Error Attribution was Disabled

- so this operation could  be expensive depending on the model we choose to use.
- but also it's only one query per conversation which actually might be relatively ok
- anyways the point of error attribution is to help us remove "user/system-induced errors" from the analysis
- it should help reduce noise so let's add that back

### RE: "fix memory target for S0"

- I think we already implement separate reflection prompts for different targets, no?

