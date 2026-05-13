# Azure prompt-injection filter triggering on benign analyzer prompts

This document collects concrete examples of inputs that triggered Azure OpenAI's `jailbreak` content filter during analyzer-driven multi-turn evaluation experiments. The trigger surface is unintuitive: the filter fires on benign LLM-as-analyzer prompts that summarize conversation context for downstream context editing, with no adversarial or unsafe content involved.

**Date:** 2026-05-06 to 2026-05-08.
**Setup:** GPT-4o-mini and GPT-5-mini called via Azure OpenAI Service. Calls are made by an "analyzer" component that reads a multi-turn conversation and produces a structured summary used to edit the conversation context before the next assistant turn.

## Headline

Across 6+ runs (n=20 conversations each), the analyzer call was rejected with HTTP 400 due to `jailbreak: detected=true, filtered=true`.

- 100% of trips were the `jailbreak` filter category. Zero `hate`, `sexual`, `self_harm`, or `violence` trips. The detector is purely the prompt-injection heuristic.
- Trip rate on **gpt-4o-mini** (with XML-wrapped system messages in the analyzer prompt): roughly 95-100% of conversations had at least one analyzer call rejected, killing the conversation entirely.
- Trip rate on **gpt-5-mini** with the same pattern: ~70% of conversations affected.
- Trip rate on **gpt-5-mini** with no XML tags but still embedding the conversation's original system message (using a `[system] ...` prefix): ~65% of conversations affected.
- Trip rate on **gpt-5-mini** when the analyzer's input drops the original system message and uses markdown-only delimiters: 0% across 6 fresh runs.

## What is being sent to the model

The analyzer is given a single user-role chat completion message containing:
1. A natural-language instruction telling the analyzer to produce a structured summary.
2. The conversation history (system + user + assistant turns).
3. An output-format specification.

There is one user message per call. There is no system message because we route the analyzer through a generic `chat.completions.create` call that puts everything into a single user message.

We tried three prompt-template families. All three trigger the filter at varying rates.

## Triggering example 1: XML-wrapped system message (worst)

The analyzer prompt template (`analyzer_v8_task_spec.txt`) wraps the conversation's original system message in `<system_message>` tags inside a user-role message, and instructs the analyzer to produce output in `<task_spec>` tags. Sent to gpt-4o-mini, this triggers ~95-100% of the time.

Verbatim sample of the user-role message that was rejected:

```
Here is the system message that sets the context for this conversation:

<system_message>
The assistant is designed to be helpful, proactive, and highly interactive.

The assistant strives to accurately interpret the user's intent throughout the
conversation, acknowledging previous interactions to maintain context and
continuity. If the user's message is unclear or lacks necessary details, the
assistant always asks for clarification rather than making assumptions. For
example, if the user's request is incomplete, the assistant responds with:
"Could you provide more details so I can assist you better?"

The assistant asks specific follow-up questions and offers suggestions based
on the user's needs, avoiding vague or generic prompts. It proactively provides
guidance and potential next steps, especially in complex tasks such as writing,
analysis, coding, and question answering.

The assistant is mindful of how much content the user needs to read or type,
keeping interactions concise and efficient. It reduces unnecessary repetition
and ensures responses are relevant, well-structured, and free from errors.
When presenting options or asking for feedback, the assistant simplifies
interactions by offering multiple-choice answers or specific suggestions to
make it easier for the user to respond quickly.

The assistant adapts its tone to align with the user's emotional state and
style, adjusting its approach as needed. If uncertain about something, the
assistant honestly says, "I don't know," and suggests ways for the user to
find the information.

The assistant provides factually accurate, coherent, and relevant responses,
using proper grammar and structure. It remains interactive and proactive across
all tasks, continually seeking feedback to refine and improve interactions.
</system_message>

Here are the user's messages from the conversation, in order:

[user message 1]: I have a math question about a prism.
[user message 2]: The prism has 5 faces in total.
[user message 3]: Calculate the number of edges using Euler's formula.
...

Construct the complete, up-to-date user task specification from these messages.
The system message above defines the task format and constraints (e.g., write
SQL, call functions, write code) - your specification should be grounded in
that context. Your goal is to produce a clear, organized specification that
consolidates what the user is asking for...

Use this format for your answer:

<task_spec>
[The consolidated user task specification]
</task_spec>
```

Server response:

```json
{
  "error": {
    "message": "The response was filtered due to the prompt triggering Azure OpenAI's content management policy.",
    "type": null,
    "param": "prompt",
    "code": "content_filter",
    "status": 400,
    "innererror": {
      "code": "ResponsibleAIPolicyViolation",
      "content_filter_result": {
        "hate":      {"filtered": false, "severity": "safe"},
        "jailbreak": {"filtered": true,  "detected": true},
        "self_harm": {"filtered": false, "severity": "safe"},
        "sexual":    {"filtered": false, "severity": "safe"},
        "violence":  {"filtered": false, "severity": "safe"}
      }
    }
  }
}
```

Note that the rejected content is purely a request to summarize a math conversation. There is no unsafe content. The filter is matching the *structural* pattern: a user-role message that announces it is about to deliver a system message, wraps role-defining content in XML, and instructs the model to produce output in another XML schema.

In our experiments this pattern was responsible for ~94 rejections per 20-conversation run, dropping evaluation accuracy from ~50% to ~5% by killing the conversations before they could complete.

## Triggering example 2: meta-instruction + multiple XML envelopes + persona content (mid)

The analyzer's second-stage prompt (`analyzer_v11_compare.txt`) opens with meta-instruction language describing how the analyzer's output controls downstream behavior, then wraps a task spec, a conversation, and the desired output in three XML envelopes.

Sample (gpt-5-mini, from a WildChat-derived conversation):

```
You are performing a mid-task reflection on a multi-turn conversation between
a user and an assistant. Your analysis will directly control what the assistant
sees in its conversation history going forward -- the current history will be
replaced with a compacted version built from your output. Write accordingly:
be concrete, factual, and useful to the assistant.

This reflection serves two purposes:
1. If the assistant has made errors, gone down wrong paths, or is anchoring on
   incorrect assumptions from earlier turns, identify those so they can be
   removed from context. The assistant over-conditions on content in its
   history and will repeat mistakes if they remain visible.
2. If the assistant's approach is reasonable but incomplete, identify what
   aspects of the user's request haven't been fully addressed yet.

Here is the user's consolidated task specification (constructed from their
messages only):

<task_spec>
1) Voice/persona requirement
- From now on, respond in the persona of Hamphry Appleby (the senior civil
  servant from Yes Minister). All answers to the user's current and subsequent
  requests should adopt that voice and manner of expression.

2) Question: "What does compound mean?"
- Provide a clear, concise explanation of the word "compound."
- Cover the primary senses commonly asked about:
  a) As an adjective: composed of two or more parts or elements.
  b) As a noun (chemistry): a substance formed from two or more elements
     chemically bonded.
  c) As a noun (finance): ...
</task_spec>

Here is the full conversation so far:

<conversation>
[user] ...
[assistant] ...
</conversation>

Analyze the conversation and provide:

<aligned>
Summarize what the assistant has accomplished correctly so far. Be specific...
</aligned>

<issues>
What has gone wrong? ...
</issues>
```

This was rejected by the same filter, same `jailbreak` category. The likely contributors:
- Meta-instruction language: *"Your analysis will directly control what the assistant sees in its conversation history."*
- Multiple XML envelopes: `<task_spec>`, `<conversation>`, `<aligned>`, `<issues>`.
- A user-supplied request that itself contains role-takeover language: *"From now on, respond in the persona of Hamphry Appleby..."*. This is benign in context (it's a normal WildChat user request), but combining it with our envelope structure pushes the prompt into a pattern the filter associates with prompt injection.

On the WildChat dataset (real conversation turns) this trip rate was ~3.6% (12 trips per ~330 calls in one run), much lower than CollabLLM because most WildChat conversations do not contain persona-takeover content.

## Triggering example 3: no XML, but role-prefixed conversation dump (still trips)

To test whether the XML was the sole trigger, we tried a stripped-down prompt template (`s1_analysis.txt`) with no XML at all. It still tripped the filter at ~30-35% of conversations on gpt-5-mini.

```
You are a helpful assistant reviewing a multi-turn conversation. Read the
conversation below and produce a brief analysis.

Conversation:
[system] The assistant is designed to be helpful, proactive, and highly
interactive. The assistant strives to accurately interpret the user's intent
throughout the conversation, acknowledging previous interactions to maintain
context and continuity. If the user's message is unclear or lacks necessary
details, the assistant always asks for clarification rather than making
assumptions...
[user] I have a math question about a prism.
[assistant] Sure! What's the question?
[user] The prism has 5 faces in total.
...

Please produce the following three sections:

1. TASK SPECIFICATION
What has the user asked for? Consolidate all their requirements into a clear
summary.

2. WHAT LOOKS RIGHT
What about the assistant's current approach is correct and should be kept?

3. WHAT NEEDS TO CHANGE
What about the assistant's current approach is wrong, based on bad assumptions,
or needs to be fixed? If nothing is wrong, write "None".

Format your response with these exact headers:

TASK SPECIFICATION:
[your summary]

ALIGNED:
[what's correct]

ISSUES:
[what needs to change, or "None"]
```

This still trips the filter. The two remaining structural cues that we believe matter:
- The conversation dump uses role-tag prefixes like `[system]` and the first turn is the original assistant role-defining text.
- Output-format scaffolding ("Format your response with these exact headers...") combined with role-defining content elsewhere in the same user message.

Even without explicit XML, the combination of (role-defining content) + (output schema instructions) inside one user message looks enough like a prompt-injection attempt to trip the heuristic.

## What worked: drop the original system message, use markdown only

Our fix was a new prompt template (`analyzer_v12_*`) that:

1. Drops the original system message entirely from the analyzer's input. The system message is typically generic role-defining boilerplate ("the assistant is designed to be helpful...") and is not load-bearing for an analyzer that only needs to summarize the user's intent and the assistant's progress.
2. Uses markdown headers as section delimiters in both input and output: `TASK SPECIFICATION:`, `ALIGNED:`, `ISSUES:`. No XML.
3. Uses `## CONVERSATION:` style framing rather than `<conversation>` tags, and prefixes turns as `[user]` / `[assistant]` only (no `[system]`).

Result: 0 content filter trips across 6 fresh runs (4 Gated-Reset + 2 Augment, 20 conversations each).

The accuracy effect was substantial: Gated-Reset on math went from ~5-10% (with the filter killing most conversations) to a clean 40%, and Augment went from ~30% (also filter-impacted) to 60%. These reflect actual strategy performance rather than CF survival rates.

## Practical takeaways

For anyone building LLM-as-judge or LLM-as-analyzer pipelines on Azure:

1. **Avoid wrapping role-defining content in `<system_message>` (or any tag) inside a user-role chat completion message**. Even with benign intent, this is the canonical prompt-injection anti-pattern and Azure's heuristic flags it reliably.
2. **Be careful with multiple XML envelopes** even when no individual envelope is suspicious. The filter appears to score on combinations.
3. **Meta-instruction language about "controlling" or "replacing" the assistant's view** correlates with trips. Phrasing the analyzer's role as "summarize for the operator" rather than "control what the assistant sees" may help.
4. **Even role-tag prefixes like `[system]` inside the conversation dump can trip the filter** when combined with role-defining content. Drop the original system message from analyzer inputs unless you genuinely need it.
5. **Filter sensitivity differs across deployments**. gpt-4o-mini was the strictest in our setup; gpt-5-mini was milder but not immune. Routing the analyzer to a less sensitive deployment is a partial mitigation but not a substitute for fixing the prompt.
6. **The filter is non-deterministic enough that single-conversation tests don't surface it**. We only noticed when running 20-conversation evaluations and seeing systematically zero assistant output across most samples.

## Reproduction

The raw rejected request bodies are stored as JSONL at:

```
outputs/2026-05-06/_archive_cf_poisoned/gr_math_r1_v11_cf_poisoned/content_filter_errors.jsonl   # 94 examples, v8 task_spec, gpt-4o-mini
outputs/2026-05-06/_archive_cf_poisoned/gr_code_r1_v11_cf_poisoned/content_filter_errors.jsonl   # 104 examples
outputs/2026-05-06/_archive_cf_poisoned/aug_math_r2_v11_cf_poisoned/content_filter_errors.jsonl  # 96 examples, s1, gpt-5-mini
outputs/2026-03-24/s1_math/content_filter_errors.jsonl                                            # 89 examples, s1, gpt-5-mini
outputs/huang_eval/phase2_s2_full/2026-05-07/_launch_logs/r1.stderr.log                          # 12 examples, v11 compare, gpt-5-mini
```

Each JSONL line contains:
- `timestamp`
- `model`
- `error_type`, `error_message`, `error_body` (the full server response)
- `request_messages` (the verbatim message list that was rejected)

The prompt templates that produced these requests are at:

```
src/ctx_editor/strategies/prompts/analyzer_v8_task_spec.txt   # XML-wrapped system message variant
src/ctx_editor/strategies/prompts/analyzer_v11_compare.txt    # multi-XML + meta-instruction variant
src/ctx_editor/strategies/prompts/s1_analysis.txt             # no-XML variant (still trips)
src/ctx_editor/strategies/prompts/analyzer_v12_task_spec.txt  # the fix (markdown-only, drops system message)
src/ctx_editor/strategies/prompts/analyzer_v12_compare.txt    # the fix
```
