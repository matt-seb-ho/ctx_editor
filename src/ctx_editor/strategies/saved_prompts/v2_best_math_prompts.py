"""Saved V2 prompts that produced best math results.

Results achieved:
- agentic_edit math V2a: 5/9 (55.6%), avg 5.9 turns (outputs/2026-03-10/19-44-03)
- agentic_edit_memory math V1: 5/9 (55.6%), avg 12.1 turns
- context_edit math V2b: 3/9 (33.3%), avg 17.7 turns

These are the prompts currently in context_edit.py and agentic_edit.py as of 2026-03-10.
Saving here for safekeeping in case future changes regress math performance.
"""

# From context_edit.py — the editor prompt
EDITOR_PROMPT_V2 = """\
You are a context editor for a multi-turn conversation. Your job is to produce a clean \
context that helps the assistant avoid repeating past mistakes.

CRITICAL PRINCIPLE: The user's messages are the source of truth. The assistant's prior \
responses may contain wrong assumptions, incorrect approaches, or errors that snowballed \
across turns. You must clearly separate what the USER said from what the ASSISTANT tried.

<conversation>
{conversation}
</conversation>

{memory_section}

Produce your output in these two clearly separated sections:

<user_intent>
Collate ONLY information from the user's messages (and system message if present). Include:
- The user's goal/question
- All requirements, constraints, and specifications the user has provided
- Any examples, test cases, or clarifications from the user
- Any corrections the user made to the assistant's understanding
Do NOT include the assistant's interpretations or assumptions here — only what the user actually said.
</user_intent>

<approach_evaluation>
Critically evaluate the assistant's current approach:
- Is the assistant's interpretation of the problem correct given ALL user messages?
- Has the assistant made assumptions that the user never confirmed or that contradict user messages?
- Are there specific errors in the assistant's solution that need to be corrected?
- What should the assistant do differently on the next attempt?
If the assistant's approach has fundamental problems (wrong function signature, wrong algorithm, \
wrong interpretation), say so clearly. Do not preserve wrong work just because it was produced \
with effort. The whole point of this edit is to let the assistant start fresh without the \
baggage of prior wrong reasoning.
</approach_evaluation>"""

# From agentic_edit.py — the decision prompt
DECISION_PROMPT_V2 = """\
Analyze the current conversation and decide whether a context reset would help the assistant.

<conversation>
{conversation}
</conversation>

A context reset clears the conversation and gives the assistant a fresh start with a clean \
summary of what the user wants. This is beneficial when the assistant has gone down the wrong \
path and accumulated errors are making things worse.

Look for these signs that a reset would help:
1. The assistant's approach is fundamentally wrong (wrong algorithm, wrong interpretation, wrong function signature)
2. The assistant is building on top of earlier mistakes instead of reconsidering
3. New user information contradicts assumptions the assistant made earlier
4. The assistant keeps producing similar wrong answers turn after turn

A reset is NOT helpful when:
- The assistant is making steady progress (even if slow)
- The conversation is still short and the assistant hasn't committed to a wrong path yet
- The main problem is missing information (which a reset can't fix)

Respond with your analysis and decision:

<notes>
Be specific and concrete:
- What exactly has the user asked for? (Cite their messages)
- What is the assistant's current approach? Is it correct?
- If the approach is wrong, what specifically is wrong? (e.g., "wrong return type: returns List[List[str]] but should return flat List[str]")
- What should the assistant do differently?
</notes>

<edit_decision>yes or no</edit_decision>"""
