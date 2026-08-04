# Depth Read: Huang et al. (2026) — "Do LLMs Benefit From Their Own Words?"

**Bibkey:** huang2026llmsbenefit  
**arXiv:** 2602.24287  
**Access status:** Full text retrieved from PDF (35 pages). All quotes below are verbatim from the PDF; paraphrases are labeled.

**Authors:** Jenny Y. Huang, Leshem Choshen, Ramon Astudillo, Tamara Broderick, Jacob Andreas  
**Affiliation:** MIT / MIT-IBM Watson AI Lab / IBM Research

---

## 1. Exact Definition of "Context Pollution"

**Section 2.5 title:** "Context Pollution: When Seeing Past Responses Becomes Counterproductive"

**Verbatim definition (p. 6):**
> "We find cases where earlier assistant turns introduce errors, hallucinations, or stylistic artifacts that propagate into future turns. We call this phenomenon context pollution."

**Abstract formulation (p. 1):**
> "instances of context pollution, in which models over-condition on their previous responses, introducing errors, hallucinations, or stylistic artifacts that propagate across turns."

**Introduction formulation (p. 2):**
> "context pollution: a phenomenon in which earlier model-generated outputs introduce errors, hallucinations, or stylistic artifacts that propagate into subsequent turns"

---

## 2. The Assistant-Omit Method

**Section A.3:** "Context Configurations"

**Two configurations compared:**

- **Full Context (FC/INCLUDED):** "Assistant responses are stored verbatim in the conversation history. The model sees all previous user shards and its own complete prior responses."
- **Assistant-Omitted (AO/OMITTED):** All past assistant turns replaced with placeholder.

**Verbatim system message for AO (p. 13 / Appendix A.3):**
> "In this conversation, previous assistant responses are shown as '[Response provided]' to save memory. These are placeholders indicating the turn was already answered and has passed. Focus only on answering the user's most recent message."

**Mechanics (paraphrase, A.3):** After each turn the assistant's full response is replaced with the token `[Response provided]` to preserve the alternating user/assistant turn structure. The model conditions on all user turns and placeholders, but has no access to any prior response content.

**Variant:** A summarized-context condition (one-sentence summary per assistant turn) is tested in Section A.8 and improves over FC for both models and datasets tested, suggesting long reasoning chains are a primary driver of context pollution.

---

## 3. Failure Modes: "Follow-up without Feedback" and Entanglement

### Category definitions (Section 2.3 / p. 4–5)

Three prompt types, defined by degree of dependence on prior assistant responses:

1. **New Ask** — "non-initial user prompts that introduce a new, self-contained request within an ongoing conversation." (p. 4)
2. **Follow-up with Feedback** — prompts that "reference a prior conversation round ... with any concrete feedback" (paraphrase; feedback like "Make it shorter" or "X is not right, use Y").
3. **Follow-up without Feedback** — verbatim definition (p. 5):
   > "user prompts that reference a prior conversation round (may be a user turn or an assistant response) without any concrete feedback (e.g., 'Reflect on your response,' 'And does George like it too?')."

### Frequency (Section 2.3, p. 5) — VERIFIED

> "In our dataset, new-ask prompts account for **36.4%** of user turns, follow-up with feedback for **30.5%**, and follow-up without feedback for **33.1%**."

**Alternative phrasing from Introduction (p. 2):**
> "Only a subset of user prompts (**33.1%**) reference an earlier assistant response without giving actionable feedback on ways to improve or revise the response"

So the entanglement category ("Follow-up without Feedback") is **33.1%** of all turns. This is the category where blind omit hurts most, because the prompt references a specific prior assistant output without reproducing it.

### Qualification: even "Follow-up without Feedback" does not always need full history

From Section 2.4 / p. 6 (verbatim):
> "Note that the third case requires storing only the relevant assistant turn."

This is critical: even within the entanglement category, Huang's authors observe that blanket omit is over-aggressive — storing the one referenced turn would suffice. This is where selective/surgical methods (like ours) are motivated.

---

## 4. Scope Limits, "Coarse" Characterization, and Future Work Framing

### "Finer-grained" future work (Section 3 / p. 8) — VERBATIM

> "A natural extension of this work is to develop a finer-grained approach for context filtering that preserves only the specific past assistant responses relevant to a given prompt."

This is the single clearest statement scoping out their own method and pointing to what we do.

### Stateful / agentic tasks explicitly called out as harder (Section 4 / p. 8) — VERBATIM

> "Furthermore, for multi-turn agentic systems, conversation context extends beyond user prompts and assistant responses to include intermediate artifacts, such as tool outputs, execution traces, retrieved files, and planning scratchpads (Anthropic, 2025). These additional outputs make context garbage collection an even more critical design problem."

Huang et al. explicitly do **not** evaluate stateful or tool-use settings. Their benchmark is restricted to in-the-wild chat (coding + math questions, no persistent environment state). The statefulness axis our benchmark adds is explicitly flagged here as future/harder work.

### Binary per-turn decision

The adaptive classifier in Section 3 is a binary per-turn choice between FC and AO — it does not do partial omit or surgical rewriting. The paper does not implement the finer-grained selective approach it proposes.

---

## 5. Benchmark, Tasks, Models, and Headline Numbers

### Datasets (Section 2.1 / Appendix A.1)

- **WildChat** (allenai/WildChat-4.8M): real ChatGPT interaction logs; filtered to GPT-4 conversations, English, 5–10 turns, technical topics.
- **ShareLM** (shachardon/ShareLM): aggregated human–model chat.
- **Sample:** 150 conversations from each = **300 total** real-world conversations.
- **Technical filter:** math and coding keywords (algebra, python, debug, etc.). Non-technical or toxic conversations excluded.
- **Appendix A.8 also uses:** `microsoft/lost_in_conversation` (Laban et al., 2025) — the synthetic LiC benchmark (HumanEval, LiveCodeBench, Spider, Berkeley FCBL, GSM8K, ToTTo, Haystack Summary sharded into multi-turn). Results in appendix only, not main text.

### Models (Section 2.1 / A.2)

- Qwen3-4B (thinking mode enabled)
- DeepSeek-R1-Distill-Llama-8B
- GPT-OSS-20B
- GPT-5.2 (state-of-the-art frontier)

### Evaluation (Section A.4)

LLM-judge: GPT-5, pairwise win rate across "quality" and "on-topic" dimensions. Two judge variants: (a) judge sees full user+assistant context; (b) judge sees only user turns. Human–LM-judge alignment: **90.0% on quality, 91.7% on on-topic** (60 manually scored pairs).

### Headline numbers

**Context length reduction (p. 4 / A.7):**
> "full-context histories in our analysis grow linearly with conversation depth, reaching approximately 25,000–55,000 characters by round 8. In contrast, the user-turn-only context remains nearly constant with conversation depth, consuming only 5,000–10,000 characters at the same turn depth, a 5 to 10× reduction in context usage"

**Win rates (paraphrase, Fig. 2 / p. 4):**
- Under the full-context judge: FC outperforms AO for Qwen3-4B and GPT-5.2 (overall); AO maintains or matches for DeepSeek and GPT-OSS-20B.
- Under the user-only judge: AO tends to match or outperform FC across all four models.
- The gap is strongest on **Follow-up without Feedback** turns; New Ask turns are approximately equal under both configurations.

**Adaptive strategy (Section 3.2 / p. 7–8):**
> "Several adaptive configurations retain over 95% of FC-only performance while substantially reducing context usage (the adaptive performs similarly to FC-only at 70% of the context consumption)."

**LiC appendix results (A.8, paraphrase):** On Lost-in-Conversation, both DeepSeek and Qwen3 show improvements when omitting assistant responses. On WildChat, results are mixed (DeepSeek improves; Qwen3 regresses slightly).

---

## 6. Limitations Section (Section 4 / Discussion)

**LLM-judge reliability caveat (p. 8):**
> "We note that our evaluation relies on an LLM-as-judge framework, which means that these findings depend on the reliability of the automated evaluator."

**Benchmark curation gap (p. 8):**
> "we suggest the need for more carefully-curated real-world conversation benchmarks that reflect true multi-turn dependence, to allow for accurate future benchmarking of models' long-context reasoning capabilities."

**Agentic context gap (p. 8):**
> "for multi-turn agentic systems, conversation context extends beyond user prompts and assistant responses to include intermediate artifacts, such as tool outputs, execution traces, retrieved files, and planning scratchpads (Anthropic, 2025). These additional outputs make context garbage collection an even more critical design problem."

**Future work framing (p. 8):**
> "Future work may look into designing context management systems that predict, from user-side behaviors alone, whether retaining past assistant responses is likely to benefit a downstream conversation."

---

## Citable Hooks for Our Paper

The 4 strongest verbatim quotes to cite when arguing we measure gaps Huang flagged:

1. **The "finer-grained" gap (p. 8):**
   > "A natural extension of this work is to develop a finer-grained approach for context filtering that preserves only the specific past assistant responses relevant to a given prompt."
   — Use to argue our surgical rewriting is exactly the extension they proposed.

2. **Entanglement category exists and is quantified (p. 5):**
   > "follow-up without feedback for 33.1%"
   — Use to anchor our entanglement dial: 33% of real turns exhibit the entanglement property Huang's omit cannot handle gracefully.

3. **Even entangled turns need only one referenced turn, not all (p. 6):**
   > "Note that the third case requires storing only the relevant assistant turn."
   — Use to argue that the right intervention is selective preservation, not wholesale omit.

4. **Stateful/agentic context is out of scope and harder (p. 8):**
   > "for multi-turn agentic systems, conversation context extends beyond user prompts and assistant responses to include intermediate artifacts, such as tool outputs, execution traces, retrieved files, and planning scratchpads. These additional outputs make context garbage collection an even more critical design problem."
   — Use to justify our statefulness axis as addressing a gap Huang explicitly deferred.
