# Lianhui Feedback Round 2 — Changelog

## Summary of Changes

This document maps each piece of advisor feedback to the specific changes made in the paper.

---

### 1. First sentence: concrete example (OpenClaw) + "interaction" over "conversation"

**Feedback**: Refactor first sentence to include a concrete example; prefer "interaction" over "conversation".

**Change**: Rewrote the intro's opening sentence from a generic claim ("Multi-turn conversation is the dominant mode of interaction...") to a concrete, example-driven lead: "Multi-turn interaction is the dominant mode of use for large language models---from coding assistants that debug across dozens of exchanges to autonomous agents like OpenClaw that orchestrate email, calendars, and APIs through extended dialogues." Also changed the abstract's first sentence from "conversations" to "interactions".

**Why this resolves it**: The reader immediately sees two concrete, recognizable examples (coding assistants, OpenClaw) instead of an abstract assertion. "Interaction" is now the default term.

---

### 2. Terminology clarity: user/assistant roles

**Feedback**: "Assistant" could be misconstrued as a subagent that assists the main agent; need to be extremely clear that these are LLM API message roles.

**Change**: Added a footnote in the intro's first paragraph: "Throughout this paper, 'user' and 'assistant' refer to the standard message roles in LLM APIs---the human-written input and the model-generated response, respectively---not to human users and helper sub-agents. Huang et al. use the same convention; their main intervention is called 'assistant omission' (AO)."

**Why this resolves it**: Early, explicit definition prevents any confusion. Anchoring to Huang's established convention gives it authority.

---

### 3. Figure 1 overhaul (statefulness)

**Feedback**: Figure 1 doesn't communicate the problem clearly; plan to overhaul it to demonstrate the statefulness problem.

**Change**: No changes to the figure itself (pending overhaul). The surrounding text now better frames what the figure should demonstrate, with the stateful/stateless vocabulary established before the figure appears.

---

### 4. Statefulness explanation in the intro

**Feedback**: If we only explain pollution is a problem, we're just motivating AO. We need to explain statefulness and why that makes AO nonviable.

**Change**: Restructured paragraph 3 to explicitly introduce the stateful/stateless distinction:
- "effectively reducing the interaction to a stateless single-turn query"
- "This works for *stateless* tasks where the answer can be re-derived from user messages alone."
- "But many real interactions are *stateful*: the assistant's earlier outputs contain essential information that cannot be reconstructed from user messages alone."
- Closing line now explicitly says "while preserving the stateful information the model needs"

**Why this resolves it**: The reader now understands two things: (1) pollution is a problem (motivating intervention), AND (2) statefulness means you can't just throw away the polluted content (motivating curation over omission). AO is positioned as a stateless-only solution, and our contribution is the stateful-capable alternative.

---

### 5. Consistent stateful/stateless terminology

**Feedback**: Be consistent — use "stateful" vs "stateless" instead of varying phrasings like "self-contained", "from scratch", etc.

**Changes across the paper**:
- Abstract: "self-contained" → "stateless"; "self-contained tasks" → "stateless tasks"
- Intro para 1: "handful of turns" → "several (~8) turns"
- Intro para 2: "presented from scratch" → "given a single-turn query without the prior conversation history"
- Intro para 3: "restarting from scratch" → "reducing the interaction to a stateless single-turn query"
- Intro results para: "self-contained LiC tasks" → "stateless LiC tasks"
- Experiments: "self-contained" → "stateless" in LiC description
- Strategies: "self-contained LiC tasks" → "stateless LiC tasks"
- Related work: "effective only when..." → "effective only for stateless tasks where..."
- Discussion: "on LiC" → "on stateless LiC tasks"

**Why this resolves it**: One vocabulary, used consistently. "Stateless" and "stateful" are immediately understandable and form a natural contrast.

---

### 6. "Structural information control" too vague/abstract

**Feedback**: Too abstract for reviewer comprehension; needs concrete explanation.

**Changes**:
- Abstract: Replaced "so structural information control---not just prompting---is necessary" with "so the analysis pipeline must physically exclude the assistant's prior messages during task reconstruction---prompting alone does not suffice"
- Intro para 4: Replaced the abstract phrase with a concrete example: "different analysis steps must see different slices of the conversation history: for example, the task reconstruction step receives only user messages, ensuring that the assistant's (potentially incorrect) framing cannot bias what the system treats as ground truth."

**Why this resolves it**: Instead of naming an abstract concept, we describe the concrete action (physically excluding messages) and give a specific example of what that means in practice.

---

### 7. "Handful" quantified

**Feedback**: "Handful" is vague; quantify as ~8.

**Change**: "only a handful of turns" → "only several (~8) turns"

---

### 8. "From scratch" contrast unclear

**Feedback**: Advisor doesn't understand that "from scratch" contrasts with having previous context.

**Change**: "when presented from scratch" → "when given a single-turn query without the prior conversation history"

**Why this resolves it**: The contrast is now explicit: "single-turn query" vs the multi-turn conversation that caused the problem.

---

### 9. Smoother transition from cog sci → prior work

**Feedback**: Need to make it clear that managing conversation context implements selective attention at the harness level.

**Change**: Added bridge sentence at end of para 2: "Because the model cannot implement this self-regulation internally, it must be provided externally---by the system that constructs the prompt and manages the conversation history." Para 3 then opens with "Prior work on such external management of conversation context splits along two axes."

**Why this resolves it**: The reader follows a logical chain: (1) models lack executive function → (2) it must be provided externally → (3) here's what prior external approaches look like → (4) they're too coarse → (5) here's our fine-grained approach.

---

### 10. Executive function = harness, not analyzer

**Feedback**: Advisor was confused about whether the analyzer is the executive function; it's the entire harness/scaffolding that implements executive function.

**Changes**:
- Intro para 4: "a training-free, inference-time method that externalizes the self-regulation LLMs lack" → "a training-free, inference-time method in which the system harness---not the model itself---implements the selective attention and error monitoring that LLMs lack"
- Intro para 4: Added "This implements, at the harness level, the selective attention that the model cannot perform over its own context."
- Related work (exec function para): Added "because LLMs appear deficient in these capacities, the system harness surrounding the model must implement them externally"
- Figure 2 caption already frames this correctly ("A separate analyzer agent externalizes the executive functions that LLMs lack")

**Why this resolves it**: The paper now consistently says "the harness implements executive function" rather than leaving it ambiguous whether the analyzer alone is the executive function.

---

### 11. Sentences feel isolated/disconnected

**Feedback**: Advisor doesn't understand the relationship between executive function and our method.

**Changes**: This was addressed through the combination of:
- Bridge sentence at end of para 2 (connecting executive function deficit → external solution)
- Para 3 opening that connects to "such external management"
- Para 4 opening that explicitly names "the system harness---not the model itself" as implementing executive function
- The concrete example of what selective attention means in practice

**Why this resolves it**: Each paragraph now explicitly connects to the previous one, creating a narrative chain rather than isolated observations.

---

### 12. Methods section: motivational blurb before problem statement

**Feedback**: Advisor wants high-level motivation and intuition before the formal problem statement.

**Change**: Added an opening paragraph to the Methods section: "The core challenge is that an LLM cannot distinguish its own correct work from its own mistakes---both are encoded in the same assistant messages and both influence future generation equally. Our method addresses this by externalizing the judgment: a separate analysis pipeline reconstructs what the user actually asked for (from user messages alone, so the reconstruction cannot be biased by the assistant's framing), compares the assistant's work against that clean specification, and then rewrites the conversation to keep what is correct and remove what is harmful. We now formalize the problem this pipeline solves and describe its components."

**Why this resolves it**: The reader now has the full intuition before encountering any formalism. They know *what* the method does and *why* before seeing *how* it's formalized.
