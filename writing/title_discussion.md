# Paper Title Discussion

## Current title
**Agentic Context Curation for Multi-Turn LLM Conversations**

## Constraints from feedback

**Advisor (Lianhui):**
- Wants **"harness"** in the title, to emphasize that the intervention lives at the harness / context-engineering layer rather than at the model level.
- If "harness" is in the title, it must appear and be explained in the introduction.

**MSR mentor:**
- Make the title **lay-friendly**; do not include "executive function" (that's a framing device inside the paper, not a sell).
- The phrase **"multi-turn LLM conversations"** risks being parsed as "conversations between multiple LLMs" rather than "multi-turn conversations between a human and an LLM." Disambiguate.
- A memorable method name is desirable but does not have to live in the title (see `method_name_discussion.md`).

**Implicit constraints from the paper itself:**
- The core contribution is **selective removal** of pollution while preserving stateful assistant content, not compaction.
- It works across stateless tasks, real human–AI conversations (WildChat), and stateful agentic tool use (tau2-bench).
- We want reviewers to immediately connect to the Lost-in-Conversation (LiC, ICLR best paper) line of work.

## Tensions to resolve

1. **Advisor's "harness" vs MSR's "lay-friendly."** "Harness" is a term-of-art that most NLP readers know (since Claude Code / Anthropic popularized the "agent harness" vocabulary) but it is still jargon for a lay audience. We can keep "harness" if the rest of the title is unambiguous; alternatively we can imply it with "inference-time" or "outside the model."
2. **"Multi-turn" disambiguation.** "Human–AI" is the clearest, but clunky. "Dialogue" / "assistant" / "chat" carries the human-in-the-loop implication for free.
3. **Distinguish from compaction work.** Titles that foreground "curation," "editing," "decontamination," "selective removal" read very differently from "compression," "folding," "compaction."

## Candidate titles

### Group A — Harness-forward (satisfies advisor, may feel technical to lay readers)
- **A1.** *A Harness for Context Curation in Multi-Turn Human–AI Conversations*
- **A2.** *Harness-Level Context Curation for Multi-Turn Human–AI Conversations*
- **A3.** *An Agent Harness that Edits Context for Multi-Turn Human–AI Conversations*
- **A4.** *Harnessing Context: Selective Curation for Multi-Turn Human–AI Conversations*
  - plays on "harness" as both noun (agent harness) and verb
- **A5.** *Curating Context in the Agent Harness for Multi-Turn Human–AI Conversations*

### Group B — Lay-friendly, "harness" implied (satisfies MSR more than advisor)
- **B1.** *Curating Conversation Context to Close the Multi-Turn Gap*
- **B2.** *Selective Context Editing for Multi-Turn Human–AI Conversations*
- **B3.** *Curating, Not Compacting: Context Editing for Multi-Turn Human–AI Conversations*
  - directly frames the paper against compaction lines
- **B4.** *Lost in Conversation, Found in Curation: An Inference-Time Fix for Multi-Turn LLMs*
  - explicit piggyback on LiC; memorable; MSR mentor endorses piggybacking

### Group C — Problem-forward (attention-grabbing, pulls reader in by the pollution frame)
- **C1.** *Silencing Pollution: Context Curation for Multi-Turn Human–AI Conversations*
- **C2.** *Removing What Misleads: Harness-Level Context Curation in Multi-Turn Conversations*
- **C3.** *Decontaminating the Context Window: Selective Curation for Multi-Turn Conversations*

### Group D — Method-name-forward (if we commit to a backronym from `method_name_discussion.md`)
- **D1.** *\{MethodName\}: Harness-Level Context Curation for Multi-Turn Human–AI Conversations*
- **D2.** *\{MethodName\}: Curating Context Across Multi-Turn Conversations*

## Recommendation

If we want to satisfy both advisors cleanly, I would lead with either:

- **A2 — *Harness-Level Context Curation for Multi-Turn Human–AI Conversations***
  Why: "Harness-Level" is the most explicit realization of advisor's harness ask; "Human–AI" defuses MSR's multi-LLM ambiguity; "Curation" differentiates from compaction; no "executive function."

- **B3 — *Curating, Not Compacting: Context Editing for Multi-Turn Human–AI Conversations***
  Why: immediately tells a reader the paper's distinguishing claim; easier to remember; "harness" is implicit (only the harness can curate); advisor may push back because "harness" is not literally present.

- **B4 — *Lost in Conversation, Found in Curation: An Inference-Time Fix for Multi-Turn LLMs***
  Why: maximum piggyback value — any reviewer who has read LiC will recognize the gesture immediately. Good venue-match if LiC is current hot work. Riskier: the wordplay can read as cute rather than serious; "LLMs" reintroduces the multi-LLM ambiguity (we'd need to replace with "Assistants" or "Dialogue").

## Things to decide
1. **Is "harness" in the title a hard constraint?** If yes → A-group. If soft → B/C/D-group with "harness" front-and-center in paragraph 3 of the introduction.
2. **How much do we want to lean on the LiC piggyback in the title itself?** It's already a natural citation in the introduction; a title-level wink (B4) is a bigger commitment.
3. **Are we ready to commit to a method name?** If yes, D-group becomes viable. If no, A2 or B3.

## Notes on what I'd change regardless of choice
- **Replace "LLM Conversations" with "Human–AI Conversations"** in whichever title is picked, to address MSR's ambiguity concern.
- **Keep "multi-turn"** regardless — it is the paper's setting and its main distinction from the broader context-engineering literature.
