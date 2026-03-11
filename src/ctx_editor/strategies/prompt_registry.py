"""Versioned prompt registry for context editing strategies.

Allows switching between prompt versions via config without code changes.
Each version is a named dict with 'editor_prompt' and optionally 'decision_prompt'.
"""

# ── V2: Structured user/assistant separation (clean, minimal) ──────────────

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


# ── V3: V2 + guardrails against observed failure modes ─────────────────────

EDITOR_PROMPT_V3 = """\
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

IMPORTANT:
- Do NOT include the assistant's interpretations, assumptions, or invented details here.
- If the user didn't specify something (e.g., function name, parameter types, return format), \
do NOT fill it in from the assistant's choices — leave it unspecified.
- If the assistant added parameters or constraints the user never mentioned, do NOT include them.
</user_intent>

<approach_evaluation>
Critically evaluate the assistant's current approach. Be BRIEF and SPECIFIC — focus on what's wrong.
- List any assumptions the assistant made that the user never confirmed (e.g., invented parameters, \
wrong function signatures, assumed return types).
- List any specific errors in the solution.
- State what the assistant should do differently in 1-2 sentences.

Do not flag ambiguity unless it's causing the assistant to do the wrong thing. If the user \
hasn't specified something and the assistant's default seems reasonable, that's fine — don't \
flag it. The goal is to fix actual errors, not to enumerate every unspecified detail.

If the assistant's approach is broadly correct but has minor issues, say so — don't make it \
sound worse than it is. If it has fundamental problems, say so clearly.
</approach_evaluation>"""

DECISION_PROMPT_V3 = """\
Analyze this conversation and decide: should the assistant get a fresh start?

<conversation>
{conversation}
</conversation>

A context reset clears the conversation and gives the assistant a clean summary of what the \
user actually asked for, helping it avoid repeating mistakes.

Answer these questions one by one:

1. WHAT DID THE USER ASK FOR? (Summarize the user's actual requirements in 1-2 sentences)

2. WHAT IS THE ASSISTANT DOING? (Summarize the assistant's current approach in 1-2 sentences)

3. IS THE ASSISTANT'S APPROACH CORRECT? Check for these specific problems:
   - Has the assistant introduced parameters, function names, or return types the user never mentioned?
   - Is the assistant building on an earlier wrong answer instead of reconsidering?
   - Has the user corrected the assistant, but the assistant ignored or misunderstood the correction?
   - Is the assistant producing similar wrong outputs repeatedly?

4. DECISION: Based on your analysis, should we reset? Answer "yes" if the assistant is on a \
fundamentally wrong path, or "no" if it is making reasonable progress.

You MUST answer all 4 questions. Format your response exactly like this:

<notes>
1. User wants: [your answer]
2. Assistant is: [your answer]
3. Problems found: [your answer, or "None — approach looks correct"]
</notes>

<edit_decision>yes or no</edit_decision>"""


# ── Registry ───────────────────────────────────────────────────────────────

EDITOR_PROMPTS = {
    "v2": EDITOR_PROMPT_V2,
    "v3": EDITOR_PROMPT_V3,
}

DECISION_PROMPTS = {
    "v2": DECISION_PROMPT_V2,
    "v3": DECISION_PROMPT_V3,
}

# Default version
DEFAULT_VERSION = "v3"


def get_editor_prompt(version: str = DEFAULT_VERSION) -> str:
    """Get editor prompt by version name."""
    if version not in EDITOR_PROMPTS:
        raise ValueError(f"Unknown editor prompt version '{version}'. Available: {sorted(EDITOR_PROMPTS)}")
    return EDITOR_PROMPTS[version]


def get_decision_prompt(version: str = DEFAULT_VERSION) -> str:
    """Get decision prompt by version name."""
    if version not in DECISION_PROMPTS:
        raise ValueError(f"Unknown decision prompt version '{version}'. Available: {sorted(DECISION_PROMPTS)}")
    return DECISION_PROMPTS[version]
