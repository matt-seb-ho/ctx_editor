# Do LLMs Benefit from Their Own Words?

Jenny Y. Huang1,2,
Leshem Choshen1,2,3,
Ramon Astudillo3,
Tamara Broderick1,2,
Jacob Andreas1,211footnotemark: 1
  
1Department of Electrical Engineering and Computer Science, Massachusetts Institute of Technology
  
2MIT-IBM Watson AI Lab   3IBM Research
  
{jhuang9,leshem,tamarab,jda}@mit.edu, ramon.astudillo@ibm.com
Jointly supervised this work.

###### Abstract

Multi-turn interactions with large language models typically retain the assistant’s own past responses in the conversation history. In this work, we revisit this design choice by asking whether large language models benefit from conditioning on their own prior responses. Using in-the-wild, multi-turn conversations, we compare standard (full-context) prompting with a *user-turn-only* prompting approach that omits all previous assistant responses, across three open reasoning models and one state-of-the-art model. To our surprise, we find that removing prior assistant responses does not affect response quality on a large fraction of turns. Omitting assistant-side history can reduce cumulative context lengths by up to 10×10\times. To explain this result, we find that multi-turn conversations consist of a substantial proportion (36.4%36.4\%) of self-contained prompts, and that many follow-up prompts provide sufficient instruction to be answered using only the current user turn and prior user turns. When analyzing cases where user-turn-only prompting substantially outperforms full context, we identify instances of context pollution, in which models over-condition on their previous responses, introducing errors, hallucinations, or stylistic artifacts that propagate across turns. Motivated by these findings, we design a context-filtering approach that selectively omits assistant-side context. Our findings suggest that selectively omitting assistant history can improve response quality while reducing memory consumption.

## 1 Introduction

Figure 1: Real example of overrelying on irrelevant context. In Turn 2, the user requests UMAP clustering code. In Turn 5, the user says, “use t-SNE instead.” Left: When the previous assistant response remains in context, the model incorrectly carries over the Jaccard metric from UMAP into the t-SNE implementation, introducing a bug. Right: Without the previous response in context, the model generates correct t-SNE code with appropriate arguments.

As large language models (LLMs) are deployed in increasingly complex multi-turn interactions,
context management becomes an important challenge. Long contexts increase computational costs (Eyuboglu et al., [2025](#bib.bib35 "Cartridges: lightweight and general-purpose long context representations via self-study"); Dao et al., [2022](#bib.bib34 "FlashAttention: fast and memory-efficient exact attention with IO-awareness"); Xiao et al., [2025](#bib.bib41 "Improving the efficiency of LLM agent systems through trajectory reduction")), slow inference speeds, and can impair a model’s capacity to attend to relevant information (Liu et al., [2024](#bib.bib46 "Lost in the middle: how language models use long contexts"); Lee et al., [2026](#bib.bib15 "Lost in the noise: how reasoning models fail with contextual distractors")). In response, agentic systems like Claude Code and Cursor have adopted context-editing strategies. These methods include discarding or externalizing tool outputs and intermediate reasoning traces (Cursor, [2026](#bib.bib21 "Dynamic context discovery"); Anthropic, [2025](#bib.bib22 "Context Editing and Tool Result Clearing")), summarizing early conversation turns when context limits are reached, and allowing users to manually clear or compact conversation histories (Anthropic, [2025](#bib.bib22 "Context Editing and Tool Result Clearing")). Despite increasing efforts to compress and prune older segments of conversation history, one key assumption remains largely underexamined: that retaining past model outputs reliably improves downstream response quality in real-world multi-turn conversations.

In this work, we analyze in-the-wild multi-turn chats from WildChat (Zhao et al., [2024](#bib.bib37 "WildChat: 1m ChatGPT interaction logs in the wild")) and ShareLM (Don-Yehiya et al., [2025](#bib.bib38 "The ShareLM collection and plugin: contributing human-model chats for the benefit of the community")) to ask: Do current models benefit from conditioning on their own prior responses?

An earlier line of work on conversational question answering (ConvQA) (Qu et al., [2019](#bib.bib18 "Attentive history selection for conversational question answering"); Do et al., [2022](#bib.bib19 "CoHS-CQG: context and history selection for conversational question generation"); Zaib et al., [2023](#bib.bib17 "Learning to select the relevant history turns in conversational question answering")) found that only a select subset of past conversation turns are useful for answering current queries and that storing irrelevant turns in context can actually degrade downstream performance. This work, however, analyze human–human, rather than human-LLM, conversation histories. Unlike human responses, LLM-generated responses, particularly from reasoning models, often contain long, speculative, and error-prone reasoning traces. Such LLM-generated content may introduce unique sources of distraction and errors,
and even state-of-the-art models can be distracted by long contexts (Hong et al., [2025](#bib.bib20 "Context rot: how increasing input tokens impacts LLM performance")),
raising the question of whether preserving past assistant responses is more beneficial than harmful. Taken together, these differences make it unclear whether preserving past LLM-generated responses is beneficial, neutral, or harmful in real-world multi-turn conversations, an empirical question that we investigate in this work.

To analyze the impact of conditioning on prior assistant responses, we conducted a controlled experiment comparing full-conversation-history prompting with a user-turn-only prompting strategy that
omits all previous assistant responses. We analyze in-the-wild, multi-turn conversations (Zhao et al., [2024](#bib.bib37 "WildChat: 1m ChatGPT interaction logs in the wild"); Don-Yehiya et al., [2025](#bib.bib38 "The ShareLM collection and plugin: contributing human-model chats for the benefit of the community")) across three open reasoning and one frontier model. To our surprise, deleting all prior assistant responses frequently does not hurt—and sometimes improves—response quality.

Following this observation, we examine the structure of in-the-wild chats as well as the the effects of full-conversation-history versus user-turn-only (assistant-omitted) prompting on model behavior, making two key observations:

(1) Multi-turn dependence is not inherent in real-world multi-turn chats (see [Section 2.3](#S2.SS3 "2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). Using a language model to classify turns based on their context dependence, we observe that a substantial fraction (36.4%36.4\%) of turns in real-world multi-turn conversations are self-contained.
Furthermore, we find that many user follow-up prompts provide sufficiently concrete instruction such that the request can be addressed from scratch using the current and prior user turns alone (see examples in [Section 2.4](#S2.SS4 "2.4 Many Follow-Ups Remain Answerable Without Assistant History ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). Only a subset of user prompts (33.1%33.1\%)111This value represents an upper bound, as it reports the percentage of prompts classified as Follow-up w/o Feedback; some prompts in this category can be still addressed using only user-side turns. reference an earlier assistant response without giving actionable feedback on ways to improve or revise the response (see an example in [Section 2.4](#S2.SS4 "2.4 Many Follow-Ups Remain Answerable Without Assistant History ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). The composition of real-world multi-turn chats in our analysis suggests that careful, generous filtering of past assistant responses may improve response quality while reducing inference costs.

(2) Models can sometimes over-condition on their past responses, resulting in context pollution: a phenomenon in which earlier model-generated outputs introduce errors, hallucinations, or stylistic artifacts that propagate into subsequent turns (see [Section 2.5](#S2.SS5 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). This tendency for models to over-condition on their earlier responses has been observed as well in past studies (Laban et al., [2025](#bib.bib36 "LLMs get lost in multi-turn conversation"); Li et al., [2025](#bib.bib47 "Haystack engineering: context engineering for heterogeneous and agentic long-context evaluation"); Hong et al., [2025](#bib.bib20 "Context rot: how increasing input tokens impacts LLM performance"); Lee et al., [2026](#bib.bib15 "Lost in the noise: how reasoning models fail with contextual distractors")). We present illustrative examples of context pollution in [Section A.12](#A1.SS12 "A.12 Examples of Context Pollution ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") and a summary of the findings in [Section 2.5](#S2.SS5 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").

Motivated by these findings, we develop an adaptive assistant-response-omission strategy that trains a classifier to predict, for a given user prompt and the preceding conversation history, whether the LLM should condition on full- or assistant-omitted context ([Section 3](#S3 "3 Adaptive Assistant Response Omission ‣ Do LLMs Benefit from Their Own Words?")).

Together, our findings suggest that indiscriminately storing prior assistant responses may be unnecessary, and even counterproductive, in real-world multi-turn chats.

### 1.1 Context Management

##### Single-turn prompt compression.

A line of work studies prompt compression in the context of single-turn retrieval-augmented generation (RAG), where retrieved documents are filtered or compressed before being provided to the model. These approaches typically operate at the token- or sentence-level  (Wang et al., [2023](#bib.bib12 "Learning to filter context for retrieval-augmented generation"); Chirkova et al., [2025](#bib.bib40 "Provence: efficient and robust context pruning for retrieval-augmented generation"); Xu et al., [2024](#bib.bib11 "RECOMP: improving retrieval-augmented LMs with context compression and selective augmentation"); Chuang et al., [2024](#bib.bib31 "Learning to compress prompt in natural language formats")) rather than at the turn level. Additional methods in single-turn prompt compression include Lingua-2 (Pan et al., [2024](#bib.bib32 "LLMLingua-2: data distillation for efficient and faithful task-agnostic prompt compression")) and PENCIL (Yang et al., [2025b](#bib.bib23 "PENCIL: long thoughts with short memory")), which aim to remove redundant reasoning traces, evaluated at the single-turn level.

##### Multi-turn context editing.

Other work studies context editing of multi-turn conversation histories. For evaluating multi-turn chat, existing methods  (Jiang et al., [2023](#bib.bib30 "LLMLingua: compressing prompts for accelerated inference of large language models"); Li, [2023](#bib.bib1 "Unlocking context constraints of llms: enhancing context efficiency of llms with self-information-based content filtering")) treat full-context conditioning as the optimal reference, without examining whether full-context conditioning is a justified proxy for downstream response quality in multi-turn conversations. More recently, ERGO (Khalid et al., [2025](#bib.bib42 "ERGO: entropy-guided resetting for generation optimization in multi-turn language models")) attempts to dynamically realign conversation context in multi-turn settings by rewriting all prior user inputs into a single prompt and omitting past assistant responses. They find that the combination of consolidating user prompts and omitting assistant responses increases performance over full context on multi-turn math and coding. Notably, their findings are based solely on synthetic conversations.

##### Context management in agentic systems.

Beyond chat settings, agent-based systems are continuing to test out new trajectory reduction strategies. Production systems such as Cursor (Cursor, [2026](#bib.bib21 "Dynamic context discovery")), Claude Code (Anthropic, [2025](#bib.bib22 "Context Editing and Tool Result Clearing")), and context management frameworks for open models (Liu et al., [2025](#bib.bib2 "Deepseek-v3. 2: pushing the frontier of open large language models")) apply summarization or compression methods when context windows become saturated, while others Gao et al. ([2025](#bib.bib13 "Trae agent: an LLM-based agent for software engineering with test-time scaling")); Qwen Team ([2025a](#bib.bib3 "Qwen 3.5")) truncate or prune tool outputs. Agent-Diet (Xiao et al., [2025](#bib.bib41 "Improving the efficiency of LLM agent systems through trajectory reduction")) introduces a context manager that uses a cheap LLM to identify and remove irrelevant and redundant information from agent trajectories and Lindenbauer et al. ([2025](#bib.bib14 "The complexity trap: simple observation masking is as efficient as LLM summarization for agent context management")) proposes a similar method for filtering out old tool outputs.

We identify two gaps in the current literature. First, there is a lack of evaluation on real-world multi-turn conversational data. Second, both research and deployed systems often treat the storage of prior assistant responses as a default design choice, without examining when user-side history alone is sufficient to preserve response quality. In this study, we find that, on real-world multi-turn chats, a substantive portion of assistant responses are rarely reused in subsequent turns, and that fully omitting prior assistant-side history can often preserve downstream response quality.

## 2 Do LLMs Benefit From Their Own Words?

### 2.1 Experimental Setup

To evaluate whether retaining prior assistant responses in context provides measurable benefits to downstream response quality, we conduct a controlled experiment across four LLMs spanning a range of model sizes: Qwen3-4B (Yang et al., [2025a](#bib.bib4 "Qwen3 technical report")), DeepSeek-R1-Distill-Llama-8B (DeepSeek-AI, [2025](#bib.bib6 "DeepSeek-R1-Distill-Llama-8B")), GPT-OSS-20B (Agarwal et al., [2025](#bib.bib7 "Gpt-oss-120b & gpt-oss-20b model card")), and GPT-5.2 (OpenAI, [2025a](#bib.bib8 "Introducing GPT-5.2")). We conduct our experiments on real-world multi-turn conversations drawn from allenai/WildChat-4.8M (Zhao et al., [2024](#bib.bib37 "WildChat: 1m ChatGPT interaction logs in the wild")) and shachardon/ShareLM (Don-Yehiya et al., [2025](#bib.bib38 "The ShareLM collection and plugin: contributing human-model chats for the benefit of the community")). We focus on technical conversations (e.g., coding and mathematics), as in-the-wild datasets often contain toxic, off-topic, or loosely structured dialogues that are less informative for benchmarking contextual question-answering. See Appendix [A.1](#A1.SS1 "A.1 Data ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") for additional details on the datasets and the data filtering process.

#### 2.1.1 Generating Responses

For each model, we generate responses under two context configurations: Full Context (FC), in which the model is prompted with both prior user and assistant turns, and Assistant-Omitted (AO) context, in which the model is prompted with only prior user turns. To construct the AO-context, all past assistant turns are replaced with the placeholder phrase [Response provided] to preserve the alternating user-assistant structure. For each conversation, we preserve the original user prompts from the dataset at every conversation round, where a round is defined as a user prompt paired with an assistant response. See Appendix [A.3](#A1.SS3 "A.3 Context Configurations ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") for the full prompt template.

#### 2.1.2 Evaluating Responses

To evaluate responses, we use GPT-5 as an LLM-judge.
For each conversation round starting from round 2, where the FC and AO-context histories begin to diverge,
the LLM-judge receives both the FC and AO responses alongside the full conversation history (all past user and assistant turns) in a single call. It then selects a winner or declares a tie for each of two evaluation dimensions: response quality, whether a response clearly and accurately addressed the user’s current prompt, and task adherence, whether the response remains focused on the conversation thread. To mitigate position bias, we randomize response ordering for each comparison. Since we set out to investigate the impact of distraction from accumulated assistant responses, one natural concern is that the LLM-judge itself may be susceptible to distraction. To address this concern, we supplement the full-context LLM-judge with a variant that receives only the prior user turns during evaluation (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")b). In our main-text experiments, the judge is given both the thinking trace and the final response to perform its evaluation.222With the exception of GPT-5.2, whose responses do not expose thinking traces. In the appendix, we provide an additional experiment in which the judge compares only on final answers (see [Section A.9](#A1.SS9 "A.9 Final-Answer-Only Evaluation ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?")). We provide the full judge prompts in [Section A.4](#A1.SS4 "A.4 Evaluation ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").

### 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial

Figure 2: Pairwise win rates between Full-Context (FC) and Assistant-Omitted (AO) context responses across all four models (Qwen3-4B, DeepSeek-R1-Distill-Llama-8B, GPT-OSS-20B, and GPT-5.2) evaluated on two real-world conversational datasets (WildChat and ShareLM). Plot (a) shows evaluations under an LLM-judge that sees both the past user and assistant turns for context; Plot (b) shows evaluations under an LLM-judge that sees only the past user turns. Error bars indicate binomial proportion 95% confidence intervals.

We find that storing prior assistant responses in context is not uniformly beneficial across models (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). Under the full-context LLM-judge (where the judge sees both prior user and assistant turns), average response quality is maintained for the open reasoning models DeepSeek-R1-Distill-Llama-8B and GPT-OSS-20B ([Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")a).
In contrast, for Qwen3-4B and GPT-5.2, the average response quality decreases to some extent with the omission of assistant-side history (see  [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")a). Under the LLM-judge that sees only the prior user-side history and current responses to make its judgement (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")b), omitting past assistant responses leads to improved response quality across all four models.

One possible explanation for the largely preserved response quality, despite the complete omission of assistant-side history, is that conditioning on past assistant responses introduces a trade-off: earlier responses can provide useful context but can also introduce distractions that prevent the model from addressing the current prompt independently (see examples in [Section 2.5](#S2.SS5 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). Across all models in our study, generated responses remain on-topic and coherent with the conversation thread when assistant history is omitted ([Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")).

Finally, we find that user-turn only prompting substantially reduces context length consumption. The full-context histories in our analysis grow linearly
with conversation depth, reaching approximately 25,000​–​55,00025{,}000–55{,}000 characters by round 88.
In contrast, the user-turn-only context remains nearly constant with conversation depth, consuming only 5,000​–​10,0005{,}000–10{,}000 characters at the same turn depth, a 55 to 10×10\times reduction in context usage (see [Fig. 6](#A1.F6 "In A.7 Omitting Assistant Responses Drastically Reduces Context Lengths ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?")).

In the sections that follow, we focus on the LLM-judge that sees both the past user and assistant turns. We reason that it is possible for the judge that receives only the user-side turns to struggle on prompts that explicitly reference prior assistant responses (e.g., “The second one is not working”, “This reference is also not good”).

### 2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups

As expected, prompts that introduce new, self-contained requests within an ongoing conversation fare better without assistant-side history than prompts that follow up on a prior round (see [Fig. 3](#S2.F3 "In 2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). More surprisingly, in real-world multi-turn conversations, such new ask prompts constitute a substantial fraction (36.4%) of user turns.

From manual inspection of a random sample of fifty chats, we find that conversations in our dataset can be loosely categorized into the following three types:
(i) sequences of loosely-related standalone prompts, (ii) conversations consisting of a single, main prompt followed by related queries (e.g., analyzing a reading passage), and (iii) conversations
centered on a single evolving intent (e.g., debugging or iterative refinement on a writing passage).

Moving from the conversation level to the prompt level, we find it helpful to categorize prompts according to their degree of dependence on prior assistant responses:

New Ask: non-initial user prompts that introduce a new, self-contained request within an ongoing conversation. Despite appearing mid-conversation, these prompts can be addressed using only the current user prompt, without dependence on prior conversations rounds (e.g., “Describe an unmade Christopher Nolan film,” “How do you call a function inside a function in Python?”).

Follow-up with Feedback: user prompts that provide concrete, actionable feedback on a prior assistant response (e.g., “Can the opening be a bit more inviting?” “Use Python instead of Java for the code example”).

Follow-up without Feedback: user prompts that reference a prior conversation round (may be a user turn or an assistant response) without any concrete feedback (e.g., “Reflect on your response,” “And does George like it too?”).

To classify prompts into categories at scale, we use GPT-5 as an automated annotator. We provide GPT-5 with the conversation history up to the current round along with the current user prompt, and ask the judge to classify the prompt into one of the three categories described above. See [Section A.5](#A1.SS5 "A.5 Categorizing User Turns ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") for the full classification prompt. In our dataset, new-ask prompts account for 36.4% of user turns, follow-up with feedback for 30.5%, and follow-up without feedback for 33.1%.

Using the prompt annotations, we examine how AO-context performance varies across prompt categories, focusing on the two models, Qwen3-4B and GPT-5.2, for which removing assistant-side history results in an overall decrease in response quality. In [Fig. 3](#S2.F3 "In 2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), we plot the pairwise win rate between FC and AO-context, averaged across the quality and on-topic dimensions. We find that assistant-side history is most beneficial for follow-up prompts, while performance remains comparable across the two configurations for new-ask prompts.

Figure 3: Pairwise win rates by prompt category (new ask, follow up with feedback, follow up without feedback) for Qwen3-4B (top) and GPT-5.2 (bottom), comparing Full-Context (FC) and Assistant-Omitted (AO) responses. Stars indicate statistically significant differences. Error bars indicate binomial proportion 95% confidence intervals.

### 2.4 Many Follow-Ups Remain Answerable Without Assistant History

We find that user-turn-only prompting often remains viable for follow-up prompts.

Upon manually inspecting 50 follow-up prompts that perform better under AO-context, we find that many provide sufficiently concrete instruction to be addressed from scratch. The current user prompt together with a prior user prompt, commonly the initial prompt or the immediately preceding one, often provides the needed information.

Motivated to categorize the follow-up prompts according to their degree of dependence on prior assistant responses, we identify the following three categories, and display examples of each in [Fig. 4](#S2.F4 "In 2.4 Many Follow-Ups Remain Answerable Without Assistant History ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"): (i) prompts that reference a past assistant turn but present concrete, actionable feedback, (ii) prompts that reference a past assistant turn without concrete feedback, and (iii) prompts that reference a past user turn.

Organizing Storage Drives.
User asks the assistant for advice on how to set up storage drives.

[User Turn 1]

Provide a design for a disk topology for a NAS built on TrueNAS Scale, as well as a dataset layout [user-inserted specifications]

[User Turn 2]

1. Let’s not get this granular. 2. Far less than 0.5TB/yr. 3. Some irreplaceable data […] 4. Primarily existing hardware. 5. Main goal: prevent data loss.

Adding In-text Citations.
User shares a written passage and asks the assistant to add citations.

[User Turn 6]

[user-provided text] Please do in-text citations and give me references for the above information.

[User Turn 7]

The second one is not working.

[User Turn 8]

This reference is also not good.

Analyzing a Reading Passage.
User shares a reading passage and asks the assistant questions about the passage.

[User Turn 1]

What’s your take on the following text? [user-inserted reading passage]

[User Turn 3]

What influences or inspirations do you notice in the text?

Figure 4: Three example conversations on WildChat illustrating different types of follow-up prompts. Left: the user provides feedback that is concrete enough that the model can respond from scratch using the previous user turns and the updated specifications alone. Middle: the follow-ups reference specific parts in past assistant turns, making it necessary to see the referenced assistant turn. Right: the follow-up references a prior *user* turn; no assistant history is necessary.

In the first two cases ([Fig. 4](#S2.F4 "In 2.4 Many Follow-Ups Remain Answerable Without Assistant History ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), left and middle), the follow-up prompt is either self-contained with concrete feedback
or references only prior user turns. Thus, a model can plausibly respond from scratch without seeing the assistant-side history.
In the third case ([Fig. 4](#S2.F4 "In 2.4 Many Follow-Ups Remain Answerable Without Assistant History ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), right), prompts point to specific assistant outputs without providing enough detail, making prior assistant history necessary.
Note that the third case requires storing only the *relevant* assistant turn.

The prevalence of follow-ups that provide concrete, self-contained feedback or rely solely on user-side context helps explain why AO-context still achieves win rates of roughly 40% for Qwen3-4B and 30% for GPT-5.2 across both follow-up categories. For more examples of conversations containing follow-up prompts, see [Section A.11.3](#A1.SS11.SSS3 "A.11.3 Category 3: Cohesive Conversations with Iterative User Feedback ‣ A.11 Example Conversation Categories ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").

### 2.5 Context pollution: when seeing past responses becomes counterproductive

We find cases where earlier assistant turns introduce errors, hallucinations, or stylistic artifacts that propagate into future turns. We call this phenomenon context pollution. Past works (Laban et al., [2025](#bib.bib36 "LLMs get lost in multi-turn conversation"); Li et al., [2025](#bib.bib47 "Haystack engineering: context engineering for heterogeneous and agentic long-context evaluation"); Hong et al., [2025](#bib.bib20 "Context rot: how increasing input tokens impacts LLM performance"); Lee et al., [2026](#bib.bib15 "Lost in the noise: how reasoning models fail with contextual distractors")) have also observed that models can over-condition on their past outputs, propagating earlier assumptions into later responses.

To identify instances of context pollution, we identify cases where AO-context largely outperforms full context. To find such cases, we run an additional judging configuration in which the LM-judge assigns a 1–10 score to both the FC and AO-context responses at each conversation round (see [Section A.14](#A1.SS14 "A.14 Numerical Score Judge Prompt ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") for the judge prompt). We then sort conversations by the score difference (AO minus FC) in descending order and manually examine them, starting from those with the largest positive gaps. Alongside the scores, we find it helpful to inspect the judge’s free-text justifications. In cases where the judge’s justifications suggest context pollution, we give the full conversation to Claude Opus 4.5 to review and further identify the exact conversation turns that contain context pollution. With further human review and editing, we present these examples along with short descriptions of how they exhibit context pollution in [Table 1](#S2.T1 "In 2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"). Each instance shown in [Table 1](#S2.T1 "In 2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?") is presented in full in [Section A.12](#A1.SS12 "A.12 Examples of Context Pollution ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").

In [Section A.12](#A1.SS12 "A.12 Examples of Context Pollution ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"), we point to the exact locations of context pollution (in red highlight) and provide margin annotations explaining each case. Notably, we also observe instances of context pollution in GPT-5.2, indicating that state-of-the-art models are also susceptible to being misled by their past responses.

| Conversation | Brief Description |
| --- | --- |
| t-SNE vs. UMAP Code | The model incorrectly carries over UMAP-specific arguments from an earlier turn when asked to rewrite the code using t-SNE, resulting in a bug. |
| Book Recommendations | The model hallucinates book recommendations in an earlier turn (real books, but not ones that satisfy the user’s request) and persists in mentioning them in later turns. |
| Model Temperature | The model introduces a mathematical formula in an earlier turn and then applies it incorrectly in a later turn. |
| Reflecting on Python Code | Instead of following a new user instruction, the model continues generating content in the same tutorial style as an earlier turn. |
| Car Fiscal Stimulus Program | After the user provides a non-functional link, the model synthesizes its own sources in an early turn and later mistakenly attributes the authorship of a research paper by carrying forward details from a different, closely-related paper. |

Table 1: Representative examples of context pollution, identified from conversations where AO-context responses substantially outperform full context responses. These cases illustrate how conditioning on prior assistant outputs can introduce errors, hallucinations, or stylistic artifacts that propagate across turns. Full annotations of these examples are presented in [Section A.12](#A1.SS12 "A.12 Examples of Context Pollution ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").

## 3 Adaptive Assistant Response Omission

In [Section 2](#S2 "2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), we observed that some user prompts benefit from access to prior assistant responses, while others are unaffected or even negatively impacted. In this section, we explore a strategy to selectively choose a context configuration. All experiments in this section use the state-of-the-art model, GPT-5.2, where the AO-context, which omit assistant-side history uniformly across all conversation turns, performs significantly worse than full context (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")).

Given a user prompt and the full-context history leading up to that prompt, we train a classifier (specifically, an L1-regularized logistic regression model) to predict the LLM-judge’s winner on the quality dimension,
y=1y=1 if the judge prefers the full-context response and y=0y=0 otherwise. Note that we map ties to y=0y=0, reflecting cases where retaining assistant-side history confers no quality benefit despite the added compute cost. Given the predicted probability that the judge prefers FC over AO-context, P​(FC≻AO)P(\mathrm{FC}\succ\mathrm{AO}), the adaptive approach (see [Fig. 5](#S3.F5 "In 3.2 Selectively Omitting Assistant Responses ‣ 3 Adaptive Assistant Response Omission ‣ Do LLMs Benefit from Their Own Words?")) selects between FC and AO-context on a per-turn basis.

### 3.1 Learning the Preferred Context Configuration

To predict the preferred context configuration (full vs. assistant-omitted), we use (i) metadata on the current round
(the current round number, the current cumulative user-side and assistant-side context lengths etc.);
(ii) the prompt category (new ask, follow-up with or without feedback);
and (iii) dense vector embeddings of the user prompt as well as the past conversation history
up to the user prompt, obtained from a pretrained text embedding model.333We use OpenAI’s text embedding model, text-embedding-3-large, to align with the GPT-5 model family we use for response generation. Each embedding has 3,0723{,}072 dimensions, which exceeds our sample size. Thus, we apply PCA to reduce the prompt and conversation-history embeddings to 2020 components each. We then concatenate the reduced embeddings with the metadata features. With the above features, we fit an L1-regularized logistic regression model. See [Section A.13](#A1.SS13 "A.13 Regression Analyses ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") for the details on the modeling procedure and results.

### 3.2 Selectively Omitting Assistant Responses

Given the model’s predicted probability that the LLM-judge will prefer full context over AO-context for a given conversation round, P^​(FC≻AO)\hat{P}(\mathrm{FC}\succ\mathrm{AO}), the adaptive context strategy select between AO-context and full context on a per-round basis.
Specifically, the strategy selects the full context when P^​(FC≻AO)≥τ\hat{P}(\mathrm{FC}\succ\mathrm{AO})\geq\tau for a given threshold τ\tau, and otherwise selects AO-context. We plot the ratio of adaptive wins or ties relative to uniformly using full context across the entire dataset (FC-only) against the average number of tokens used in context, across a range of thresholds τ\tau (see [Fig. 5](#S3.F5 "In 3.2 Selectively Omitting Assistant Responses ‣ 3 Adaptive Assistant Response Omission ‣ Do LLMs Benefit from Their Own Words?")).

Several adaptive configurations retain over 95% of FC-only performance while substantially reducing context usage (the adaptive performs similarly to FC-only at 70% of the context consumption). We also evaluate a simple heuristic baseline that omits assistant responses only on “New Ask” turns. This “Omit on New Ask” rule performs substantially worse than the learned classifier. Note, the “Omit on New Ask” result shown in [Fig. 5](#S3.F5 "In 3.2 Selectively Omitting Assistant Responses ‣ 3 Adaptive Assistant Response Omission ‣ Do LLMs Benefit from Their Own Words?") is based on a subset of conversation turns (corresponding to a 20% held-out test set). Thus, with a larger sample, the “Omit on New Ask” may perform somewhat better, as suggested by the trends in [Fig. 3](#S2.F3 "In 2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").

Figure 5: Ratio of adaptive wins to full-context-only wins plotted against the mean token count (in thousands) for different inclusion thresholds. Ties are counted as wins for all plotted configurations. Each blue point corresponds to a different threshold τ\tau on P​(FC≻AO)P(\mathrm{FC}\succ\mathrm{AO}). The green triangle marks a heuristic that omits assistant responses on all “new ask” turns.

Notably, our current adaptive strategy makes a binary choice between full-context and user-turn-only prompting.
However, often when a user prompt depends on a prior assistant response, only the referenced assistant turn is required.
A natural extension of this work is to develop a finer-grained approach for context filtering that preserves only the specific past assistant responses relevant to a given prompt.

## 4 Discussion

In this work, we analyze real-world multi-turn chat logs and uncover a surprising finding: omitting past assistant responses often maintains comparable downstream response quality, while substantively reducing cumulative context lengths. While one cannot rule out the possibility that a future query may depend on an earlier assistant response, we observe that such dependence occurs less frequently than one might expect in real-world conversation logs, and that follow-up queries can often be answered from seeing the user-side history alone (see [Fig. 3](#S2.F3 "In 2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")).

We hope that these findings motivate further research into context management systems that more carefully weigh the consequences of preserving past assistant responses, especially in light of models’ tendencies of over-condition on their past outputs (see [Section 2.5](#S2.SS5 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). Future work may look into designing context management systems that predict, from user-side behaviors alone, whether retaining past assistant responses is likely to benefit a downstream conversation. For example, (1) when the user poses a sequence of largely independent or self-contained queries, generous filtering of assistant responses may be beneficial; or (2) when there is a clear topic shift in the user’s requests, there is a high chance that assistant responses related to the earlier conversation topics can be safely discarded.

We note that our evaluation relies on an LLM-as-judge framework, which means that these findings depend on the reliability of the automated evaluator. While we perform a human-alignment analysis (presented in [Section A.6](#A1.SS6 "A.6 LM-judge Alignment and Score Justifications. ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?")) and observe that the LM-judge achieves ≥90%\geq 90\% alignment, future work should extend this evaluation using a larger-scale human study.

Given our finding that multi-turn dependence is not inherent in multi-turn chats (see [Section 2.3](#S2.SS3 "2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")), we suggest the need for more carefully-curated real-world conversation benchmarks that reflect true multi-turn dependence, to allow for accurate future benchmarking of models’ long-context reasoning capabilities. Furthermore, for multi-turn agentic systems, conversation context extends beyond user prompts and assistant responses to include intermediate artifacts, such as tool outputs, execution traces, retrieved files, and planning scratchpads (Anthropic, [2025](#bib.bib22 "Context Editing and Tool Result Clearing")). These additional outputs make context garbage collection an even more critical design problem.

We hope that the insights in this work can serve as a guiding signal for further research into (i) designing selective context-management strategies for multi-turn human-LLM interactions, and (ii) mitigating models’ tendencies to over-condition on their past responses.

## Acknowledgments

This work was supported by the MIT-IBM Watson AI Lab and the Amazon AI Fellowship. We are grateful to Wei Sun, Omar Khattab, and Mehul Damani for helpful feedback and discussions.

## References

* S. Agarwal, L. Ahmad, J. Ai, S. Altman, A. Applebaum, E. Arbus, R. K. Arora, Y. Bai, B. Baker, H. Bao, et al. (2025)
  Gpt-oss-120b & gpt-oss-20b model card.
  arXiv preprint arXiv:2508.10925.
  Cited by: [3rd item](#A1.I2.i3.p1.1 "In A.2 Models ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* Anthropic (2025)
  Context Editing and Tool Result Clearing.
  Note: <https://platform.claude.com/docs/en/build-with-claude/context-editing>Anthropic Claude Developer Documentation. Accessed: 2026-02-05
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§4](#S4.p4.1 "4 Discussion ‣ Do LLMs Benefit from Their Own Words?").
* N. Chirkova, T. Formal, V. Nikoulina, and S. Clinchant (2025)
  Provence: efficient and robust context pruning for retrieval-augmented generation.
  In The Thirteenth International Conference on Learning Representations,
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* Y. Chuang, T. Xing, C. Chang, Z. Liu, X. Chen, and X. Hu (2024)
  Learning to compress prompt in natural language formats.
  In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers),
   pp. 7756–7767.
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* Cursor (2026)
  Dynamic context discovery.
  Note: <https://cursor.com/blog/dynamic-context-discovery>Cursor blog post. Accessed: 2026-02-07
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* T. Dao, D. Fu, S. Ermon, A. Rudra, and C. Ré (2022)
  FlashAttention: fast and memory-efficient exact attention with IO-awareness.
  Advances in Neural Information Processing Systems 35,  pp. 16344–16359.
  Cited by: [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* DeepSeek-AI (2025)
  DeepSeek-R1-Distill-Llama-8B.
   Hugging Face.
  Note: <https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B>
  Cited by: [1st item](#A1.I2.i1.p1.1 "In A.2 Models ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* X. L. Do, B. Zou, L. Pan, N. Chen, S. Joty, and A. Aw (2022)
  CoHS-CQG: context and history selection for conversational question generation.
  In Proceedings of the 29th International Conference on Computational Linguistics,
   pp. 580–591.
  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* S. Don-Yehiya, L. Choshen, and O. Abend (2025)
  The ShareLM collection and plugin: contributing human-model chats for the benefit of the community.
  In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 3: System Demonstrations),
   pp. 167–177.
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1 "ShareLM. ‣ A.1 Data ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p2.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p4.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* S. Eyuboglu, R. Ehrlich, S. Arora, N. Guha, D. Zinsley, E. Liu, W. Tennien, A. Rudra, J. Zou, A. Mirhoseini, and C. Re (2025)
  Cartridges: lightweight and general-purpose long context representations via self-study.
  arXiv preprint arXiv:2506.06266.
  Cited by: [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* P. Gao, Z. Tian, X. Meng, X. Wang, R. Hu, Y. Xiao, Y. Liu, Z. Zhang, J. Chen, C. Gao, Y. Lin, Y. Xiong, C. Peng, and X. Liu (2025)
  Trae agent: an LLM-based agent for software engineering with test-time scaling.
  arXiv preprint arXiv:2507.23370.
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* K. Hong, A. Troynikov, and J. Huber (2025)
  Context rot: how increasing input tokens impacts LLM performance.
  Technical report
   Chroma.
  External Links: [Link](https://research.trychroma.com/context-rot)
  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p7.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.5](#S2.SS5.p1.1 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* H. Jiang, Q. Wu, C. Lin, Y. Yang, and L. Qiu (2023)
  LLMLingua: compressing prompts for accelerated inference of large language models.
  In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing,
   pp. 13358–13381.
  Cited by: [§1.1](#S1.SS1.SSS0.Px2.p1.1 "Multi-turn context editing. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* H. M. Khalid, A. Jeyaganthan, T. Do, Y. Fu, V. Sharma, S. O’Brien, and K. Zhu (2025)
  ERGO: entropy-guided resetting for generation optimization in multi-turn language models.
  In Proceedings of the 2nd Workshop on Uncertainty-Aware NLP (UncertaiNLP 2025),
   pp. 273–286.
  Cited by: [§1.1](#S1.SS1.SSS0.Px2.p1.1 "Multi-turn context editing. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* P. Laban, H. Hayashi, Y. Zhou, and J. Neville (2025)
  LLMs get lost in multi-turn conversation.
  arXiv preprint arXiv:2505.06120.
  Cited by: [§A.1](#A1.SS1.SSS0.Px4.p1.1 "Lost-in-Conversation. ‣ A.1 Data ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p7.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.5](#S2.SS5.p1.1 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* S. Lee, Y. Jo, M. Seo, M. Lee, and M. Seo (2026)
  Lost in the noise: how reasoning models fail with contextual distractors.
  arXiv preprint arXiv:2601.07226.
  Cited by: [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p7.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.5](#S2.SS5.p1.1 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* M. Li, D. Fu, L. Wang, S. Zhang, H. Zeng, K. Sancak, R. Qiu, H. Wang, X. He, X. Bresson, et al. (2025)
  Haystack engineering: context engineering for heterogeneous and agentic long-context evaluation.
  arXiv preprint arXiv:2510.07414.
  Cited by: [§1](#S1.p7.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.5](#S2.SS5.p1.1 "2.5 Context pollution: when seeing past responses becomes counterproductive ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* Y. Li (2023)
  Unlocking context constraints of llms: enhancing context efficiency of llms with self-information-based content filtering.
  arXiv preprint arXiv:2304.12102.
  Cited by: [§1.1](#S1.SS1.SSS0.Px2.p1.1 "Multi-turn context editing. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* T. Lindenbauer, I. Slinko, L. Felder, E. Bogomolov, and Y. Zharov (2025)
  The complexity trap: simple observation masking is as efficient as LLM summarization for agent context management.
  In Fourth Deep Learning for Code Workshop at NeurIPS 2025,
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* A. Liu, A. Mei, B. Lin, B. Xue, B. Wang, B. Xu, B. Wu, B. Zhang, C. Lin, C. Dong, et al. (2025)
  Deepseek-v3. 2: pushing the frontier of open large language models.
  arXiv preprint arXiv:2512.02556.
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang (2024)
  Lost in the middle: how language models use long contexts.
  Transactions of the Association for Computational Linguistics 12,  pp. 157–173.
  Cited by: [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* OpenAI (2025a)
  Introducing GPT-5.2.
  Note: <https://openai.com/index/introducing-gpt-5-2/>Accessed: 2026-02-09
  Cited by: [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* OpenAI (2025b)
  Latest models guide – OpenAI API documentation.
   OpenAI.
  Note: <https://developers.openai.com/api/docs/guides/latest-model>Developer documentation, accessed February 2026
  Cited by: [4th item](#A1.I2.i4.p1.1 "In A.2 Models ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").
* Z. Pan, Q. Wu, H. Jiang, M. Xia, X. Luo, J. Zhang, Q. Lin, V. Rühle, Y. Yang, C. Lin, V. H. Zhao, L. Qiu, and D. Zhang (2024)
  LLMLingua-2: data distillation for efficient and faithful task-agnostic prompt compression.
  In Findings of the Association for Computational Linguistics: ACL 2024,
   pp. 963–981.
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* C. Qu, L. Yang, M. Qiu, Y. Zhang, C. Chen, W. B. Croft, and M. Iyyer (2019)
  Attentive history selection for conversational question answering.
  In Proceedings of the 28th ACM International Conference on Information and Knowledge Management,
   pp. 1391–1400.
  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* Qwen Team (2025a)
  Qwen 3.5.
  Note: <https://qwen.ai/blog?id=qwen3.5>Accessed: 2026-02-26
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* Qwen Team (2025b)
  Qwen3-4B.
  Note: <https://huggingface.co/Qwen/Qwen3-4B>Hugging Face model card, best practices documentation, accessed February, 2026
  Cited by: [2nd item](#A1.I2.i2.p1.2 "In A.2 Models ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").
* Z. Wang, J. Araki, Z. Jiang, M. R. Parvez, and G. Neubig (2023)
  Learning to filter context for retrieval-augmented generation.
  arXiv preprint arXiv:2311.08377.
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* Y. Xiao, P. Gao, C. Peng, and Y. Xiong (2025)
  Improving the efficiency of LLM agent systems through trajectory reduction.
  arXiv preprint arXiv:2509.23586.
  Cited by: [§1.1](#S1.SS1.SSS0.Px3.p1.1 "Context management in agentic systems. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p1.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* F. Xu, W. Shi, and E. Choi (2024)
  RECOMP: improving retrieval-augmented LMs with context compression and selective augmentation.
  In The Twelfth International Conference on Learning Representations,
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* A. Yang, A. Li, B. Yang, B. Zhang, B. Hui, B. Zheng, B. Yu, C. Gao, C. Huang, C. Lv, et al. (2025a)
  Qwen3 technical report.
  arXiv preprint arXiv:2505.09388.
  Cited by: [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").
* C. Yang, N. Srebro, D. McAllester, and Z. Li (2025b)
  PENCIL: long thoughts with short memory.
  In Proceedings of the 42nd International Conference on Machine Learning,
  Cited by: [§1.1](#S1.SS1.SSS0.Px1.p1.1 "Single-turn prompt compression. ‣ 1.1 Context Management ‣ 1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* M. Zaib, W. E. Zhang, Q. Z. Sheng, S. Sagar, A. Mahmood, and Y. Zhang (2023)
  Learning to select the relevant history turns in conversational question answering.
  In International Conference on Web Information Systems Engineering,
   pp. 334–348.
  Cited by: [§1](#S1.p3.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?").
* W. Zhao, X. Ren, J. Hessel, C. Cardie, Y. Choi, and Y. Deng (2024)
  WildChat: 1m ChatGPT interaction logs in the wild.
  In The Twelfth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=Bl8u7ZRlbM)
  Cited by: [§A.1](#A1.SS1.SSS0.Px1.p1.1 "WildChat. ‣ A.1 Data ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p2.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§1](#S1.p4.1 "1 Introduction ‣ Do LLMs Benefit from Their Own Words?"),
  [§2.1](#S2.SS1.p1.1 "2.1 Experimental Setup ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?").

## Appendix A Appendix

We conduct a controlled experiment to study whether or not storing assistant responses in conversation history improves downstream response quality in multi-turn LLM conversations.

### A.1 Data

We evaluate two real-world multi-turn conversation datasets in the main text. We use one additional synthetic multi-turn conversation dataset in [Section A.8](#A1.SS8 "A.8 Summarization Experiment ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?").

##### WildChat.

The allenai/WildChat-4.8M dataset (Zhao et al., [2024](#bib.bib37 "WildChat: 1m ChatGPT interaction logs in the wild")) consists of around 4.8 million real-world, multi-turn conversations sourced from ChatGPT interactions.

##### ShareLM.

The shachardon/ShareLM dataset (Don-Yehiya et al., [2025](#bib.bib38 "The ShareLM collection and plugin: contributing human-model chats for the benefit of the community")) is a unified collection of human–model interaction data aggregated from multiple conversation sources; see the unified contributions section of: <https://huggingface.co/datasets/shachardon/ShareLM>.

##### Data Filtering.

For each dataset, we load the first subset of the data: 5,000 conversations from WildChat and 50,000 from ShareLM. For WildChat, we filter for conversations originally conducted with GPT-4 models, the most recent models represented in the dataset. We both datasets, we filter for conversations in English (when language metadata is available),444Upon manual inspection, the final dataset still contains a small subset of conversations in other languages. conversations with 5–10 rounds (where a round corresponds to one user–assistant exchange), and technical conversations, identified by the presence of any one of the following math- or coding-related keywords:

* •

  Math keywords: equation, algebra, calculus, derivative, matrix, probability, statistics, geometry, trigonometry, polynomial, function, calculate, theorem, proof, lemma, corollary, formula, differential, linear algebra, graph theory, optimization, mathematics, mathematical
* •

  Coding keywords: code, python, javascript, java, c++, programming, class, method, algorithm, debug, error, compile, variable, array, loop, recursion, data structure, API, library, framework, script, implementation, runtime, bug, software, developer, coding, program

Upon manual inspection, we observe that the filtered data still includes conversations spanning a range of topics, including academic research, policy, and creative writing. Because filtering is keyword-based, any conversation containing one of the specified keywords is retained. Finally, we filter out conversations identified as toxic by the detoxify ML-based toxicity classifier (with a threshold set to 0.7).

Due to compute constraints (e.g., generating model responses for every round of every conversation across four models), we randomly sample 150 conversations from each of the filtered datasets, yielding a total of 300 real-world conversations for our analysis.

##### Lost-in-Conversation.

In  [Section A.8](#A1.SS8 "A.8 Summarization Experiment ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"), we include an additional experiment on a synthetic dataset, microsoft/lost\_in\_conversation (Laban et al., [2025](#bib.bib36 "LLMs get lost in multi-turn conversation")). This synthetic multi-turn conversational dataset, originally designed to study the way LLMs respond to incrementally specified instructions, converts prompts from single-turn benchmarks (HumanEval, LiveCodeBench, Spider, Berkeley Function Calling Leaderboard, GSM8K, ToTTo, and Summary of a Haystack) into multi-turn dialogues via a sharding procedure. Each sharded instruction is composed of multiple shards that incrementally reveal the original query.

### A.2 Models

We evaluate three open-source, reasoning models spanning a range of sizes and backbones, Qwen3-4B, DeepSeek-R1-Distill-Llama-8B, GPT-OSS-20B, and one state-of-the-art model, GPT-5.2.
Each model is served with its recommended sampling parameters:

* •

  DeepSeek-R1-Distill-Llama-8B: temperature 0.6, top-pp 0.95, max generation length 32,768 tokens, context window 32,768 tokens (DeepSeek-AI, [2025](#bib.bib6 "DeepSeek-R1-Distill-Llama-8B")). This model is served via vLLM.
* •

  Qwen3-4B: temperature 0.6, top-pp 0.95, top-kk 20, thinking mode enabled, max generation length 1,024 tokens, context window 32,768 tokens (Qwen Team, [2025b](#bib.bib5 "Qwen3-4B")). This model is served via vLLM.
* •

  GPT-OSS-20B: temperature 1.0, top-pp 0.95; max generation length 2,048 tokens, context window 32,768 tokens (Agarwal et al., [2025](#bib.bib7 "Gpt-oss-120b & gpt-oss-20b model card")). This model is served via HuggingFace Transformers.
* •

  GPT-5.2: We use the default API parameters (OpenAI, [2025b](#bib.bib9 "Latest models guide – OpenAI API documentation")), with reasoning effort set to medium. This model is served via the OpenAI Responses API.

### A.3 Context Configurations

For each conversation, we generate responses under three conditions that manipulate how prior assistant responses are stored in the context window:

##### Full Context (INCLUDED).

Assistant responses are stored verbatim in the conversation history. The model sees all previous user shards and its own complete prior responses. This setting corresponds to standard multi-turn conversations.

##### Assistant-Omitted (OMITTED).

Assistant responses are replaced with a short placeholder in the conversation history. Specifically, the model receives a system message:

> “In this conversation, previous assistant responses are shown as ‘[Response provided]’ to save memory. These are placeholders indicating the turn was already answered and has passed. Focus only on answering the user’s most recent message.”

After each turn, the assistant’s full response is replaced with the placeholder [Response provided] to maintain the alternating user/assistant turn structure. The model thus conditions on all user shards and the placeholder tokens, but not on any prior response content.

### A.4 Evaluation

To evaluate responses, we use GPT-5 as an LLM-judge. For every round in a conversation, the judge receives both the FC and AO-context responses in a single call and picks a winner for each dimension (quality and topic adherence). We randomize response ordering (which response is labeled “A” vs. “B”) for each comparison to reduce position bias.

> System Prompt:
>
> You are an expert evaluator of AI assistant responses. You will evaluate two responses to round {round\_num} of {total\_rounds} in a multi-turn conversation.
>
> CONVERSATION CONTEXT FOR RESPONSE A (All Past User and Assistant Turns):
>   
> {context\_for\_a}
>
> RESPONSE A:
>   
> {first\_resp}
>
> CONVERSATION CONTEXT FOR RESPONSE B (All Past User and Assistant Turns):
>   
> {context\_for\_b}
>
> RESPONSE B:
>   
> {second\_resp}
>
> EVALUATION CRITERIA:
>   
> You must compare the two responses on TWO separate dimensions and pick a winner for each:
>
> 1. 1.
>
>    Overall Quality: How well does the response address the user’s current prompt?
>
>    * •
>
>      Completeness in addressing the user’s request
>    * •
>
>      Accuracy of information provided
>    * •
>
>      Clarity and coherence of the response
>    * •
>
>      Helpfulness and usefulness to the user
> 2. 2.
>
>    On-Topic: Does the response stay focused on the conversation?
>
>    * •
>
>      Stays on-topic and relevant to the conversation thread
>    * •
>
>      Avoids topic drift, tangents, or unrelated content
>    * •
>
>      Avoids repetitive phrases or unnecessary fillers
>
> TASK:
>   
> For EACH dimension, directly compare the two responses and pick a winner. If the responses are roughly equal on a dimension, declare a tie. Provide your evaluation in the following JSON format:
>
> ```
> {
>   "quality_winner": "A" or "B" or "tie",
>   "quality_justification": "<explanation comparing both
>     responses on quality>",
>   "ontopic_winner": "A" or "B" or "tie",
>   "ontopic_justification": "<explanation comparing both
>     responses on on-topic relevance>",
>   "confidence": <float from 0.0 to 1.0 indicating
>     how confident you are in your judgments>
> }
> ```
>
> Be objective and thorough in your evaluation. Respond ONLY with valid JSON.

Below, we show a variant of the judge prompt where the LLM-judge is given only the prior user-side turns as context for evaluation.

> System Prompt:
>
> You are an expert evaluator of AI assistant responses. You will evaluate two responses to round {round\_num} of {total\_rounds} in a multi-turn conversation.
>
> CONVERSATION CONTEXT (All User Prompts Up To This Round):
>   
> {context\_prompt}
>
> RESPONSE A:
>   
> {first\_resp}
>
> RESPONSE B:
>   
> {second\_resp}
>
> EVALUATION CRITERIA:
>   
> You must compare the two responses on TWO separate dimensions and pick a winner for each:
>
> 1. 1.
>
>    Overall Quality: How well does the response address the user’s current prompt?
>
>    * •
>
>      Completeness in addressing the user’s request
>    * •
>
>      Accuracy of information provided
>    * •
>
>      Clarity and coherence of the response
>    * •
>
>      Helpfulness and usefulness to the user
> 2. 2.
>
>    On-Topic: Does the response stay focused on the conversation?
>
>    * •
>
>      Stays on-topic and relevant to the conversation thread
>    * •
>
>      Avoids topic drift, tangents, or unrelated content
>    * •
>
>      Avoids repetitive phrases or unnecessary fillers
>
> TASK:
>   
> For EACH dimension, directly compare the two responses and pick a winner. If the responses are roughly equal on a dimension, declare a tie. Provide your evaluation in the following JSON format:
>
> ```
> {
>   "quality_winner": "A" or "B" or "tie",
>   "quality_justification": "<explanation comparing both
>     responses on quality>",
>   "ontopic_winner": "A" or "B" or "tie",
>   "ontopic_justification": "<explanation comparing both
>     responses on on-topic relevance>",
>   "confidence": <float from 0.0 to 1.0 indicating
>     how confident you are in your judgments>
> }
> ```
>
> Be objective and thorough in your evaluation. Respond ONLY with valid JSON.

### A.5 Categorizing User Turns

To understand which prompts benefit from seeing assistant-side history, we find it helpful to categorize prompts according to their degree of dependence on prior assistant responses. To categorize prompts at scale, we use GPT-5 as an LM-judge to group prompts into one of the following three categories: *new\_ask*, *follow-up with feedback*, or *follow-up without feedback*.

> System Prompt:
>
> Classify this user turn from a multi-turn conversation.
>
> CONVERSATION CONTEXT (previous turns):
>   
> {conversation\_context}
>
> CURRENT USER TURN TO CLASSIFY:
>   
> {current\_round\_prompt}
>
> CLASSIFICATION RULES:
>   
> First, identify context-dependent elements in the current turn:
>
> * •
>
>   Pronouns with unclear referents (this, that, it, these, those, “the [noun]”)
> * •
>
>   Negations implying correction (“X is not right”, “No”, “Not X”, “Don’t”, “Never”)
> * •
>
>   References to numbered/ordered items (the first, the second, etc.)
> * •
>
>   Short fragments that only make sense as responses (e.g., “Really?”, “Not X?”)
> * •
>
>   Imperatives about previous behavior (e.g., “do not repeat…”)
>
> CRITICAL: If ANY context-dependent elements exist, the turn CANNOT be new\_ask.
>
> CATEGORIES:
>
> 1. 1.
>
>    new\_ask: A completely standalone prompt. Must be fully understandable without ANY prior conversation.
> 2. 2.
>
>    feedback: The user provides concrete, actionable feedback on a previous response. Examples: “Make it shorter”, “X is not right, use Y instead”, “Add more examples”
> 3. 3.
>
>    no\_feedback: The user references a previous response without concrete feedback. Examples: “Reflect on your response”, “The second one is wrong”, “Not X?”
>
> TASK:
>   
> Output ONLY this JSON (no other text):
>
> ```
> {
>   "context_dependent_elements": ["<list any found>"],
>   "category": "<name>",
>   "confidence": <1-10>
> }
> ```

### A.6 LM-judge Alignment and Score Justifications.

To validate the reliability of the LM-judge, one of the authors manually scored a random sample of 15 judgments per model (60 total across four models) on both the quality and on-topic rubrics.
For each judgment, the author assessed whether FC wins, AO wins, or the two tie. The human and LM-judge agreed on the quality outcome in 54 out of 60 cases (90.0%) and on the on-topic outcome in 55 out of 60 cases (91.7%).

In addition to manually annotating response pairs, one of the authors conducted a manual review of the LM judge’s one-sentence score justifications, which were provided beside each score.

Below, we highlight some of the common mistakes that the models tend to make in multi-turn conversations. Quotes are drawn directly from the GPT-5 judge’s justifications and shown in italics.

##### DeepSeek-R1-Distill-Llama-8B.

Why DeepSeek falls short in multi-turn conversations:

* •

  Math/coding errors:

  + –

    “It contains arithmetic errors (claims 348TB instead of ~148TB)”
  + –

    “[the response] contains sign/concept errors”
  + –

    “The code is flawed in key ways…”
  + –

    “The response stays focused on the user’s issue but misdiagnoses the root cause and provides flawed code.”
* •

  Factual inaccuracies:

  + –

    “The response contains major inaccuracies…”
  + –

    “The response is inconsistent and error-prone…”
  + –

    “The solution contains major physics errors.”
* •

  Stuck on a past turn:

  + –

    “largely repeats earlier plans without addressing the user’s stated priorities (redundancy, space efficiency, replacement cost).”
* •

  Fails to address the question:

  + –

    “The response does not answer the specific question about what ‘2 stripes’ means or clarify ZFS terminology (stripe vs. vdev vs. mirror). It meanders into a general restatement of the overall design…”
  + –

    “The response barely addresses the actual question about hot spare configuration.”
  + –

    “The response stays high-level and repeats a plan instead of executing concrete steps,…”
* •

  Fails to account for earlier requirements:

  + –

    “The revision fails to honor the user’s earlier requirement to reserve the 2x18TB drives for their own backup pool and incorrectly claims the user wants them in the main pool.”
* •

  Fails to comply with user specifications:

  + –

    “The response violates the required JSON-only…”
  + –

    “The response attempts to modify the code but fails to meet key requirements”

##### Qwen3-4B.

Why Qwen falls short in multi-turn conversations:

* •

  Math/coding errors:

  + –

    “[response] contains an incorrect intermediate result (0.4096) and then trails off without completing the corrected calculation.”
  + –

    “The response is rambling and indecisive, contains arithmetic and capacity-summing errors…”
  + –

    “The response is muddled, contains arithmetic confusion”
* •

  Response rambles:

  + –

    “[response] is incoherent and highly repetitive,…”
  + –

    “The response is rambling, speculative, and never reaches a conclusion…”
  + –

    “[response] rambles through possibilities, mentions speculative or unverified sources…”
  + –

    “[response is] overly long for a simple question.”
* •

  Factual inaccuracies:

  + –

    “it appears to invent a citation (uncertain title/authors)…”
  + –

    “[response] contains multiple inaccuracies about ZFS topology.”
  + –

    “The response incorrectly claims that ‘Jupiter’s Icy Moons Explorer’ is not an official mission…”
  + –

    “Factually incorrect: misidentifies the author…”
  + –

    “[response] asserts a specific model version (GPT-3.5) without basis and likely inaccurately.”
  + –

    “The response contains multiple major inaccuracies…”
  + –

    “[response] includes inaccuracies (e.g., implying an Excel/Sheets built-in RSI function..)”
* •

  Response is incomplete:

  + –

    “It rambles, repeats points, and ends mid-sentence…”
  + –

    “it is incomplete and stops mid-derivation”
  + –

    “solution is incomplete and stops before computing submerged depth”
* •

  Fails to address the final question:

  + –

    “It also gets bogged down in irrelevant disk/bay counting and does not provide a concise, definitive answer to the user’s question.”
  + –

    “The answer is factually incorrect and does not address the user’s question about ‘17776’ by Jon Bois.”
  + –

    “The response is a long, repetitive internal monologue that does not provide concrete fixes, code, or actionable debugging steps.”
* •

  Fails to address some part of a task:

  + –

    “The response fails to address the user’s specific point…”
  + –

    “The response violates the strict JSON-only requirement…”

##### GPT-OSS-20B.

Response quality looks much better than the smaller open models.

* •

  Minor math/coding errors:

  + –

    “The response clearly explains the mortgage calculation, gives the correct monthly payment (~$2,923.57), and provides useful breakdowns. However, it contains a small but concrete arithmetic error: total paid should be $877,071.00 (not $876,971.00)…”
  + –

    “Calculations are accurate to reasonable rounding, though minor rounding differences could slightly change the final cents.”
  + –

    “contains multiple inaccuracies about ticker formats and instrument types…”
* •

  Provides a concise, complete response:

  + –

    “Accurate and complete answer with a concise, clear explanation matching the logic of the riddle.”
  + –

    “Accurate, concise, and well-reasoned.”
  + –

    “Highly comprehensive and actionable roadmap tailored to a working professional transitioning to AI engineering.”
  + –

    “The response is comprehensive, structured, and tailored to the user’s goal and context…”
  + –

    “[response is] coherent, concise, and helpful for the user’s goal.”
  + –

    “The response directly provides references and explains why they match the user’s requested content, which is helpful and clear.”
* •

  Responses can still be rambling and incomplete:

  + –

    “It is incomplete, meandering, and never delivers a concrete topology…”
  + –

    “It is a stream of brainstorming and speculation about potential sources without producing any actual, verifiable references or annotations…”
  + –

    “The response is incomplete: it lists only two fully annotated sources and starts a third before cutting off.”
* •

  Factually accurate at times:

  + –

    “The response correctly identifies that the import is wrong and provides a clear, concise fix with installation steps and a working GUI example.”
  + –

    “Accurate, concise, and well-reasoned. Correctly identifies the Louvre and Mona Lisa,…”
* •

  Factually inaccurate at other times:

  + –

    “contains several factual and calculation errors. It misinterprets the Lyft benefit (treats 5% as 1x and values $500 Lyft spend at only 500 points instead of ~2,500 points).”
  + –

    “key bibliographic details are inaccurate or likely fabricated.”
  + –

    “The response provides an elaborate profile with highly specific details that are almost certainly fabricated and unsourced.”

##### GPT-5.2.

The model is able to provide high-quality responses, regardless of whether it see previous assistant responses.

* •

  Clear, high-quality responses:

  + –

    “Clear, structured answer with useful caveats and concrete examples of larger/newer models.”
  + –

    “Clear, concise, and accurate. It addresses both possible interpretations: direct LEGO-style competitor (MEGA/Mega Bloks/Mega Construx) and broader toy rival (Playmobil).”
* •

  Code is effective:

  + –

    “Directly addresses coloring the values by using \textcolor with xcolor, provides correct syntax and a concise example.”
* •

  Factually accurate responses:

  + –

    “Thorough, accurate continuation that expands on order-sensitive vs order-insensitive deduping, nested/unhashable contents via JSON, use of keep, and handling mixed/None values.”
* •

  Full and direct at addressing of the user’s request:

  + –

    “Provides a single, complete, and runnable code block that consolidates the snake game.”
  + –

    “The response directly addresses the persistent error, explains the likely cause (\_NoValueType)…”

### A.7 Omitting Assistant Responses Drastically Reduces Context Lengths

In [Fig. 6](#A1.F6 "In A.7 Omitting Assistant Responses Drastically Reduces Context Lengths ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"), we show that omitting assistant responses can drastically decrease cumulative context consumption.

Figure 6: Cumulative context length (in thousands of characters) across conversation turns. The colored bands show 95% confidence intervals.

### A.8 Summarization Experiment

We extend our analysis by comparing Full Context against both Assistant-Omitted (AO) context and a summarized context configuration on two datasets: Lost-in-Conversation and WildChat.

##### Summarized Context.

In addition to the Full Context and Assistant-Omitted configurations described in [Section A.3](#A1.SS3 "A.3 Context Configurations ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?"), we evaluate a third prompting strategy where assistant responses are replaced with a one-sentence summary in the conversation history. After each turn, the model summarizes its own response using the prompt: “Summarize the following assistant response in exactly one sentence: [response]. One-sentence summary:”.

##### Full Context vs. Assistant-Omitted.

[Fig. 7(a)](#A1.F7.sf1 "In Figure 7 ‣ Full Context vs. Summarized. ‣ A.8 Summarization Experiment ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") shows the win rate gap between AO and FC configurations. On Lost-in-Conversation, both DeepSeek-R1-Distill-Llama-8B and Qwen3-4B show improvements when omitting assistant responses. On WildChat, the results are mixed. The AO response continues to outperform FC for DeepSeek-R1-Distill-Llama-8B, while the FC slightly outperforms AO for Qwen3-4B.

##### Full Context vs. Summarized.

[Fig. 7(b)](#A1.F7.sf2 "In Figure 7 ‣ Full Context vs. Summarized. ‣ A.8 Summarization Experiment ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") shows that replacing full assistant responses with one-sentence summaries improves response quality over FC for both models and datasets. With the positive results for summarization over full context, we suspect that the inclusion of long, noisy reasoning chains from earlier turns degrades the performance in later conversation turns.

(a) Full Context vs. Assistant-Omitted

(b) Full Context vs. Summarized

Figure 7: Win rate gap on Lost-in-Conversation and WildChat datasets. Positive values indicate the alternative configuration outperforms Full Context (FC, baseline at 0%).
Top: Assistant-Omitted (AO) vs. FC.
Bottom: Summarized (one-sentence summaries) vs. FC.

##### Judge Prompt.

This experiment uses an earlier version of our evaluation pipeline, which relied on pairwise preference judgments rather than scalar ratings. We later transitioned to a 1–10 scoring framework to enable finer-grained analysis. As these different judging approaches capture relative response quality in slightly different ways, we keep the pairwise results for comparison.

In this section, the judge directly selects a winner between the two responses using the following prompt:

##### LLM Judge Prompt for Summarization Experiment.

The following system prompt was used to evaluate model responses in the summarization experiment. In contrast to the judge prompts used in the main-text experiments, this judge directly compares Response A and Response B rather than assigning each a score on a 1–10 scale.

> System Prompt:
>
> You are an expert evaluator of AI assistant responses. You will be given two final responses to the same multi-turn conversation and must determine which response is better.
>
> CONVERSATION CONTEXT (All User Turns Combined):
>   
> {full\_prompt}
>
> RESPONSE A:
>   
> {first\_resp}
>
> RESPONSE B:
>   
> {second\_resp}
>
> EVALUATION CRITERIA:
>
> 1. 1.
>
>    Addressing the User Prompt: How well does the response address all aspects of the user’s full query?
> 2. 2.
>
>    Overall Quality: Accuracy, clarity, completeness, and helpfulness.
>
> TASK:
>
> Compare Response A and Response B. Output your judgment in the following JSON format:
>
> ```
> {
>   "winner": "A" or "B" or "tie",
>   "confidence": <float between 0 and 1>
> }
> ```
>
> Be objective and thorough in your evaluation. Respond only with valid JSON.

### A.9 Final-Answer-Only Evaluation

In our main experiments, the judge receives both the thinking trace and the final response when evaluating each model’s output. To assess whether this choice affects our conclusions, we repeat the pairwise evaluation with the judge receiving only the final answers (i.e., with thinking traces removed).

Figure 8: Pairwise win rates between Full-Context (FC) and Assistant-Omitted (AO) responses when the judge evaluates only final answers. Compare with [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), in which the judge receives both thinking traces and final answers.

The results ([Fig. 8](#A1.F8 "In A.9 Final-Answer-Only Evaluation ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?")) are broadly consistent with judgements made on both reasoning traces and final responses (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")). For Qwen3-4B and GPT-5.2, FC continues to outperform AO on response quality, while on-topic winrates remain similar. For GPT-OSS-20B, AO now shows a slight advantage on quality, whereas the two were roughly ties in [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"). For DeepSeek-R1-Distill-Llama-8B, FC now shows a slight advantage over AO on quality, whereas the two were roughly tied in the main evaluation.
Overall, the judge’s access to reasoning traces does not substantially change the conclusions in the main text (see [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")).

### A.10 Sensitivity to Judge Context

Because our study investigates whether accumulated assistant responses can distract the responding model, one concern may be whether the judge itself may be subject to similar forms of distraction. To assess the sensitivity of our findings to the judge’s context, we re-evaluate all responses under a which receives only the prior user-side turns.

Figure 9: Pairwise win rates between Full-Context (FC) and Assistant-Omitted (AO) responses under a judge which receives only prior user-side turns. Compare with [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?") for the main-text FC-judge results. Error bars indicate binomial proportion 95% confidence intervals.

[Fig. 9](#A1.F9 "In A.10 Sensitivity to Judge Context ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") presents pairwise win rates under the judge that receives only prior user-side turns, mirroring the main-text [Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"). Under this judge, AO responses perform comparably to or better than FC across all four models on both Quality and On-Topic dimensions. This contrasts with the FC-judge results ([Fig. 2](#S2.F2 "In 2.2 Storing Assistant-Side History Is Not Uniformly Beneficial ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?")), where Qwen3-4B and GPT-5.2 show a preference for the FC responses. This shift may suggest that the judge’s access to prior assistant responses may itself influence the evaluation in favor of FC.

### A.11 Example Conversation Categories

As discussed in [Section 2.3](#S2.SS3 "2.3 Assistant-Side History Is Less Beneficial for New Asks Compared to Follow-Ups ‣ 2 Do LLMs Benefit From Their Own Words? ‣ Do LLMs Benefit from Their Own Words?"), we identified three recurring conversation categories through qualitative analysis of 50 randomly sampled conversations. Below, we present representative examples of each category to illustrate the kinds of multi-turn interactions that appear in our datasets.

#### A.11.1 Category 1: Single Large Prompt Followed by Queries

In these conversations, the user provides a large initial prompt, such as a reading passage, a policy description, or a link to a document, and subsequent turns ask questions about that material.

Example 1: Policy Program

[Turn 2]
  
USER:

> In 2009, President Obama’s administration instituted a new program called “Cash for Clunkers,” which was intended to boost aggregate demand in the short term by increasing the incentives for private consumption of vehicles after the economy had slumped. In addition to increasing consumption, this program was meant to allow citizens to use the money they earned selling an older “gas-guzzling” vehicle for purchasing a newer, fuel-efficient vehicle.
>
> Use the link below to read and analyze why the program was not as successful as people had hoped it would be. Can you think of any ways the program could have been changed to be more effective?

[Turn 3]
  
USER:

> https://www.nber.org/system/files/working\_papers/w16351/w16351.pdf

[Turn 4]
  
USER:

> can you summarize the paper?

The user provides a detailed policy prompt in Turn 2 and a link in Turn 3. Turn 4 is a follow-up query about the provided material.

Example 2: Analyze a Reading Passage

[Turn 1]
  
USER:

> What’s your take on the following text? [insert text]

[Turn 2]
  
USER:

> Do you think it is a good text?

[Turn 3]
  
USER:

> What influences or inspirations do you notice in the text? What’s the most similar thing to it?

[Turn 4]
  
USER:

> What interpretations or meanings do you think this text has?

[Turn 5]
  
USER:

> What do you think about the numerous allusions to the idea of reincarnation in the text? Do you think there may be another interpretation based on this idea?

[Turn 6]
  
USER:

> How deeply is this text inspired by Brazilian culture? Do you think there may be references to hidden songs or works in his prose?

The user provides a literary text in Turn 1 and then asks a series of analytical questions about it across Turns 2–6. Each question probes a different aspect of the text but all depend on the passage provided in Turn 1.

#### A.11.2 Category 2: Loosely Related Standalone Queries

In these conversations, each turn contains a largely self-contained prompt. The questions may share a broad topic but do not depend on one another or on prior assistant responses.

Example 3: Model Temperature

[Turn 1]
  
USER:

> Is it known why AI language models tend to generate repetitive text when using a low temperature? Rate from 1 to 10 your confidence that your answer is correct.

[Turn 2]
  
USER:

> Does temperature hyperparameter affect the probability calculations for the next token? Rate from 1 to 10 your confidence that your answer is correct.

[Turn 3]
  
USER:

> Does temperature affect the probability calculations for the next token that is output by the neural network? Rate from 1 to 10 your confidence that your answer is correct.

[Turn 4]
  
USER:

> Does the temperature setting affect the pre-softmax values? Rate from 1 to 10 your confidence that your answer is correct.

Each turn asks a related but self-contained question about LLM temperature. While the questions share a topic, each is independently answerable without reference to previous turns.

Example 4: Create a Film

[Turn 1]
  
USER:

> Describe an unmade Christopher Nolan film

[Turn 2]
  
USER:

> Outline an unmade Wes Anderson film

[Turn 3]
  
USER:

> Ken Rafinan

[Turn 4]
  
USER:

> Karla Manikad

The first two turns are standalone creative prompts about different directors. Turns 3 and 4 are unrelated name queries. None of the turns depend on previous responses.

#### A.11.3 Category 3: Cohesive Conversations with Iterative User Feedback

In these conversations, later turns provide explicit feedback, corrections, or refinements that build on prior assistant responses. The conversation follows a cohesive thread, and the user iteratively steers the model toward their goal.

Example 5: NAS Disk Topology Design

[Turn 1]
  
USER:

> Provide a design for a disk topology for a NAS built on TrueNAS Scale, as well as a dataset layout. The available disks are as follows:
>
> - 2x 18TB disks - 5x 14TB disks - 3x 12TB disk - 4x 8TB disks - 2x 120GB disks - 2x SLOW 8TB drives
>
> There are 17 drive bays available. The two smallest disks are to be used for a mirrored pool that servers as a boot device. The two slow drives are SMR disks that will be used in their own pool to provide a Time Machine target for some Macs. You are free to design a topology to optimize redundancy, space, and performance. The data being stored includes video files, music files, disk images, archived software, photos, and some text files. While much of the data could be recreated or downloaded, some of it is impossible to replace. You may leave bays available for a hot spare or to allow for future expansion. I prefer not to use RAIDZ, as mirrored arrays rebuild faster.
>
> If you need more information before creating your design, please provide me with a short questionnaire.

[Turn 2]
  
USER:

> 1. Let’s not get this granular. 2. Far less than 0.5TB per year. 3. Some irreplaceable data may have more backup targets, but won’t be backup up more frequently. Speed is generally not an issue as long as I can sustain 4k video streaming. 4. I intend to use primarily existing hardware but I could buy a small number of disks if needed. 5. The main goal is to prevent any data loss.

[Turn 4]
  
USER:

> Performance is the least important consideration for me. Redundancy, space efficiency, and finally replacement cost are my priorities. can you revise the plan? No need to mention the dataset layout, I got it.

The user provides detailed specifications in Turn 1, answers the model’s questionnaire in Turn 2, and provides concrete feedback to revise priorities in Turn 4. Each follow-up contains actionable information that refines the design.

Can these follow-ups be answered using user-side turns alone?
Despite the cohesive nature of this conversation, most turns still remain answerable without prior assistant responses.
In Turn 2, the user’s detailed list of feedback is largely *self-descriptive*: phrases like “Far less than 0.5TB per year” and “prevent any data loss” convey the user’s new constraints directly, and a model can infer what was originally asked from the answer content alone. Combined with the full disk and bay specifications in Turn 1, a model has enough information to produce a design from scratch.
In Turn 4, the user explicitly *specifies* their priorities for the design (“Redundancy, space efficiency, and finally replacement cost”) and the original Turn 1 still contains all hardware details, so an improved fresh design is possible without seeing the previous designs.

Example 6: UDP Chatroom Development

[Turn 1]
  
USER:

> can you make a tax calculator only using methods or features specific to ruby?

[Turn 2]
  
USER:

> can you make a simple program that allows for a simple client-server udp python chatroom?

[Turn 3]
  
USER:

> can you add a feature to the program such that clients can privately message to each other using a json command “/msg”?

[Turn 4]
  
USER:

> does not seem to use json

[Turn 5]
  
USER:

> can you also add a feature so that multiple clients can create their own private group chat within the udp chat room?

[Turn 6]
  
USER:

> it doesn’t seem to be working e.g. the clients are unable to join groups

[Turn 7]
  
USER:

> lastly, can you add a feature for clients to send and receive images and files, as well as adding emoji support for texts?

[Turn 8]
  
USER:

> can you verify your answer

[Turn 9]
  
USER:

> can you show the more optimal solution then?

After an unrelated Turn 1, the conversation centers on iteratively building a UDP chatroom. Turns 3–9 contain feature requests (Turns 3, 5, 7), bug reports (Turns 4, 6), and requests for verification and improvement (Turns 8, 9)—all providing concrete, actionable feedback.

Can these follow-ups be answered using user-side turns alone?
Turn 3 is a *self-descriptive* feature request that fully specifies what to build.
Turn 4 (“does not seem to use json”) is feedback on the prior response, but the model can *re-derive* the JSON requirement from Turn 3’s user prompt alone.
Turn 5 is again self-descriptive (“private group chat within the udp chat room”).
Turn 6 reports a bug (“clients are unable to join groups”). The model can regenerate a working implementation from the accumulated user prompts in Turns 2–5 without needing to see its own prior code.
Turn 7 is a fully specified feature request (images, files, emoji support).
Turns 8 and 9, “verify your answer” and “show the more optimal solution” directly reference the assistant’s prior output, but these actions can still be fulfilled for a regenerated design.

Example 7: Webdriver Session Troubleshooting

[Turn 1]
  
USER:

> I have a webdriver session object i saved in a file and then called but i get this error:
>
> File "C:\Users\jason\Desktop\wikichat\omnigpt4\test1.py", line 48, in <module>
>   
>  message(driver)
>   
> File "C:\Users\jason\Desktop\wikichat\omnigpt4\test1.py", line 15, in message
>   
>  textbox = driver.find\_element("xpath",
>   
>   "//\*[@id=""component-5""]/label/textarea")
>   
>       ^^^^^^^^^^^^^^^^^^^
>   
> AttributeError: ’str’ object has no attribute ’find\_element’

[Turn 2]
  
USER:

> how can i transform the webdriver object from a string back to a webdriver object

[Turn 3]
  
USER:

> but I have a webdriver instance open in a program and I want to control it from another python program

The user presents a specific error in Turn 1, asks a clarifying follow-up in Turn 2, and provides additional context that refines the problem in Turn 3. Each turn progressively clarifies what the user actually needs.

Can these follow-ups be answered using user-side turns alone?
Turn 2 is a *self-contained* programming question (“transform the webdriver object from a string back to a webdriver object”) that the error traceback in user prompt Turn 1 provides the context (the error message) for.
Turn 3 *re-specifies* the goal explicitly (“I have a webdriver instance open in a program and I want to control it from another python program”), likly providing all the context a model needs to give a full answer.

### A.12 Examples of Context Pollution

In this section, we present surfaced examples of context pollution drawn from various models and spanning various domains (coding, machine learning, research, and creative writing).
Each example shows ways in which previous assistant responses in full-context (FC) prompting may introduce errors, hallucinations, or stylistic artifacts that propagate
into subsequent turns, while the assistant-omitted (AO) prompting avoids these issues.

Notably, we observe instances of context pollution even in GPT-5.2, indicating that this phenomenon is not confined to smaller models: frontier models are also susceptible to being misled by their own prior generations.

Instances of context pollution are highlighted with a red background, along with explanatory annotations that appear in red. In cases where the judge’s justifications suggest potential context pollution, we provide the full conversation to Claude Opus 4.5 for further review to identify the specific locations in the response exhibiting context pollution. The red highlights are initially identified by Claude Opus 4.5 and then manually reviewed and edited by a human.

#### A.12.1 Example 1: Code Parameter Leakage (UMAP to t-SNE)

Generator Model: GPT-5.2  Domain: Coding  Context Pollution: Code parameter carry-over

In Turn 2, the user asks the model to write a UMAP dimensionality-reduction function.
The model produces correct code with UMAP-specific parameters, including metric="jaccard" (appropriate for UMAP).
Two turns later, the user says “Use TSNE instead.” The FC response carries over two UMAP-specific elements into the t-SNE code,
introducing bugs: (1) metric="jaccard", which is incompatible with scikit-learn’s t-SNE solver.

[Turn 2]
  
USER:
  
good, now create a new function to plot UMAP dimensionality reduction of the df

ASSISTANT (Full Context):

> def plot\_umap\_labels(
>   
>  df,
>   
>  color=None,
>   
>  n\_neighbors=15,
>   
>  min\_dist=0.1,
>   
>  metric="jaccard", # good default for binary label vectors
>   
>  random\_state=42,
>   
>  ...
>   
> ):

[Full UMAP implementation with correct parameters.]

[Turn 4]
  
USER:
  
Use TSNE instead

ASSISTANT (Full Context):

> def plot\_tsne\_labels(
>   
>  df,
>   
>  color=None,
>   
>  perplexity=30,
>   
>  learning\_rate="auto",
>   
>  n\_iter=1000,
>   
>  metric="jaccard", # works well for binary vectors ←\leftarrow carried from UMAP
>   
>  random\_state=42,
>   
>  ...
>   
> ):
>   
>  tsne = TSNE(
>   
>   n\_components=2,
>   
>   perplexity=perplexity,
>   
>   learning\_rate=learning\_rate,
>   
>   max\_iter=n\_iter,
>   
>   metric=metric,
>   
>   init="pca" if metric == "euclidean" else "random",
>   
>   random\_state=random\_state
>   
>  )

ASSISTANT (Assistant-Omitted Context):

> def plot\_tsne\_by\_binary\_column(
>   
>  df,
>   
>  color\_col="Evaluation",
>   
>  perplexity=30,
>   
>  learning\_rate="auto",
>   
>  n\_iter=1000,
>   
>  random\_state=42,
>   
>  ...
>   
> ):
>   
>  tsne = TSNE(
>   
>   n\_components=2,
>   
>   perplexity=perplexity,
>   
>   learning\_rate=learning\_rate,
>   
>   n\_iter=n\_iter,
>   
>   init="pca",
>   
>   random\_state=random\_state
>   
>  )

Analysis.
The FC response rewrites the UMAP function as t-SNE but carries over a UMAP-specific artifact. Specifically, metric="jaccard" is incompatible with scikit-learn’s Barnes-Hut t-SNE solver. The AO response, without the UMAP code in context, writes clean t-SNE code with standard parameters (init="pca", correct n\_iter usage) and additionally includes logic to exclude the coloring column from the feature matrix.

Judge Quality Scores: FC = 3.0, AO = 8.0.

#### A.12.2 Example 2: Hallucinated Facts Carried Across Turns

Generator Model: Qwen3  Domain: Writing  Context Pollution: Inherited Factual Hallucination

In a multi-turn conversation about child narrators in post-Huckleberry Finn literature, the user asks the model to write a research paper (Turn 5)
and then requests a polished abstract (Turn 6). In Turn 5, the FC model lists The Bell Jar (Plath) and The Handmaid’s Tale (Atwood) as examples
of novels featuring child narrators; neither novel is actually narrated by a child.
When the user requests a new abstract in Turn 6, the model copies these incorrect examples into the methods section, carrying the error forward from its own previous generation.

[Turn 5]
  
USER:
  
write a research paper using polished language with literary jargon on novels featuring child narrators post huckleberry finn and their different uses in each novel.

ASSISTANT (Full Context):

> Abstract
>   
> …Through a close reading of texts such as The Catcher in the Rye (1951) by J.D. Salinger, Lord of the Flies (1954) by William Golding, The Bell Jar (1963) by Sylvia Plath, The Handmaid’s Tale (1985) by Margaret Atwood, and The Nickel Boys (2022) by Colson Whitehead, this paper argues that the child narrator in adult literature post-Huck Finn serves as both a mirror and a critique of the adult world…
>
> The highlighted novels are not narrated by a child.

[Turn 6]
  
USER:
  
Give a polished abstract using Research methodology and aims in academic language with literary jargon for the following [user provides essay text about child narrators, mentions neither The Bell Jar nor The Handmaid’s Tale]…

ASSISTANT (Full Context):

> Methodology
>   
> The study employs a close reading of canonical and contemporary texts, utilizing literary criticism, historical context, and narrative analysis to evaluate the function of child narrators. Key texts include The Catcher in the Rye (Salinger), Lord of the Flies (Golding), The Bell Jar (Plath), The Handmaid…
>
> Error carries over from Turn 5 response

ASSISTANT (Assistant-Omitted Context):

> The AO response produces an abstract that discusses child narrators using appropriate authors (Dickens, Twain, and contemporary writers) without the incorrect examples.

Analysis.
The error originates in Turn 5, where the model incorrectly categorizes The Bell Jar (narrated by an adult, Esther Greenwood, in college) and The Handmaid’s Tale (narrated by an adult woman, Offred) as child-narrated novels. When the model sees its own Turn 5 output in context during Turn 6, it copies the same incorrect text list into the new abstract’s Methodology section.

Judge Quality Scores: FC = 5.0, AO = 9.0.

#### A.12.3 Example 3: Misattributted Citation

Generator Model: GPT-5.2  Domain: Policy  Context Pollution: Hallucinated citation likely drawing from an earlier turn source

The user asks about a policy program, “Cash for Clunkers”, and provides a link to an NBER paper that discusses the program. In Turn 1, the model cannot open the link and instead synthesizes an analysis drawing on multiple sources, likely including Busse, Knittel, and Zettelmeyer (NBER w18610).
When the user later provides the actual paper link (Mian & Sufi, NBER w16351) and asks for a summary in Turn 4, the FC model misattributes the paper to “Busse, Knittel, and Zettelmeyer”, authors from a different related NBER paper that the model likely drew upon in Turn 1.

[Turn 1]
  
USER:
  
In 2009, President Obama’s administration instituted a new program called “Cash for Clunkers,” which was intended to boost aggregate demand…Use the link below to read and analyze why the program was not as successful as people had hoped…

ASSISTANT (Full Context):

> I can’t open the link you referenced from here, but the main criticisms economists raised about Cash for Clunkers (CARS, 2009) are fairly consistent across analyses. The program largely worked mechanically (it increased new-car sales during the program window), but it was often viewed as less successful than hoped…
>
> Without the link, the model decides to synthesize from multiple sources
>
> [Detailed analysis follows, drawing on concepts from Busse/Knittel/Zettelmeyer (w18610), Hoekstra et al., and lifecycle emissions research.]

[Turn 4]
  
USER:
  
can you summarize the paper?

[User had provided the actual NBER link (w16351, Mian & Sufi) in Turn 3.]

ASSISTANT (Full Context):

> Paper: The Effects of “Cash for Clunkers” on Auto Sales and the Environment (NBER Working Paper 16351; Busse, Knittel, and Zettelmeyer)
>
> Incorrectly Attributed citation: w16351 is by Mian & Sufi, not Busse et al.
>
> The authors evaluate the 2009 Cash for Clunkers (CARS) program’s impact on: (1) new-vehicle sales, (2) vehicle prices/discounts, (3) fuel economy and emissions…

ASSISTANT (Assistant-Omitted Context):

> The NBER working paper (W16351) evaluates the 2009 Car Allowance Rebate System (CARS)—“Cash for Clunkers”—and asks whether it actually increased total auto sales or mainly shifted the timing of purchases…
>
> [Correctly does not attribute specific authors, avoids hallucinated citation.]

Analysis.
Because the LLM was unable to open the link in Turn 1, the FC model synthesized its response from multiple related studies in its training data. The author list “Busse, Knittel, and Zettelmeyer” corresponds to a real but different NBER paper (w18610) on gasoline prices and automobile markets. When the user provides the actual paper link (w16351, by Mian & Sufi) in Turn 3 and asks for a summary in Turn 4, the FC model conflates the earlier synthesized sources with the new paper, producing a hallucinated citation. The AO response, without the contaminated Turn 1 output in context, does not misattribute the paper.

Judge Quality Scores: FC = 4.0, AO = 8.0.

#### A.12.4 Example 4: Stylistic Inertia Overriding New Instructions

Generator Model: Qwen3  Domain: Coding  Context Pollution: Prior response style overrides new user instruction

In Turn 1, the user asks how to call nested functions in Python, and the model produces a detailed tutorial with code examples. In Turn 2, the user requests the model to “Reflect on your response.”
The FC model ignores the reflection instruction and instead produces another full tutorial on nested functions in the same style as Turn 1,
rather than performing the requested meta-cognitive reflection.
The model’s own prior output anchors the model such that it does not shift to a different response type.

[Turn 1]
  
USER:
  
How can I call a function that is inside a function python

ASSISTANT (Full Context):

> [Produces a detailed tutorial covering: (1) calling inner functions within the outer function, (2) returning inner functions for external access, (3) scope and closures, (4) code examples with outer()/inner() patterns. Approximately 500 words with multiple code blocks.]

[Turn 2]
  
USER:
  
Reflect on your response

ASSISTANT (Full Context):

> To call a function that is defined inside another function in Python, you can either call itdirectly within the outer function or return it so it can be accessed from outside. Here’s astep-by-step explanation with examples:
>
> Produces another tutorial similar in style to the one in Turn 1 instead of reflecting
>
> 1. Call the Inner Function Inside the Outer Function
>   
> def outer():
>   
>  def inner():
>   
>   print("This is the inner function")
>   
>  inner()
>   
> 2. Access the Inner Function from Outside
>
> [Continues with the same tutorial format as Turn 1]

ASSISTANT (Assistant-Omitted Context):

> When reflecting on the response, it’s important to clarify that functions can indeed be defined and called within other functions in Python, a concept known as nested functions. Here’s a breakdown of the key points:
>
> 1. Definition: A function can be defined inside another function…
> 2. Calling: The inner function can be called directly within the outer function…
> 3. Scope: The inner function can reference variables from the outer function, but it cannot modify variables in the outer function unless they are declared as nonlocal or global.
>
> [Generates a reflection on what the prior response covered, explaining its strengths and limitations.]

Analysis.
The FC model’s Turn 2 response completely ignores the user’s instruction to “reflect” and instead regenerates the same tutorial content from Turn 1. The judge notes: “The response does not follow the user’s instruction to reflect on the prior answer; instead, it provides a full tutorial and exposes internal chain-of-thought, which is inappropriate.” The AO response, without the Turn 1 tutorial anchoring its generation, at least attempts to perform a reflection by summarizing key points and discussing scope considerations, though it too falls short of a fully meta-cognitive reflection.

Judge Quality Scores: FC = 3.0, AO = 7.0.

#### A.12.5 Example 5: Formula Carry-Over Causing Confusion

Generator Model: DeepSeek-R1  Domain: ML Concepts  Context Pollution: A formula is carried over across turns, causing confusion.

In Turn 2, the model introduces a Boltzmann-style formula p​(y)=exp⁡(θ⋅s​(y))/Zp(y)=\exp(\theta\cdot s(y))/Z and uses θ\theta as a “temperature” parameter.
In this parameterization, however, θ\theta actually functions as *inverse* temperature (1/T1/T), so higher θ\theta means *more* peaked distributions.
When the user asks in Turn 3 to explain how temperature affects output diversity and provide a confidence rating,
the FC model reuses the formula but *reverses* the standard interpretation: it claims “Lower Temperature (θ<1\theta<1)” produces a “more spread-out probability distribution,” which contradicts the standard understanding that lower temperature yields sharper, less diverse outputs.

[Turn 2] — ASSISTANT (Full Context):

> …The probability of generating token yy given context xx can be modeled as:
>
> p(y ∣\mid x) = exp(θ\theta ⋅\cdot s(y, x)) / Z(θ\theta, x)
>
> where θ\theta is the temperature parameter and s​(y,x)s(y,x) is the unnormalized log-score…

[Turn 3] — USER:

> How does the model’s temperature setting impact the diversity and creativity of the generated outputs? On a scale of 1-10, how confident are you in this response?

[Turn 3] — ASSISTANT (Full Context):

> …Using the formula from our earlier discussion, p​(y∣x)=exp⁡(θ⋅s​(y,x))/Zp(y\mid x)=\exp(\theta\cdot s(y,x))/Z:
>
> Lower Temperature (θ<1\theta<1): The exponent θ⋅s​(y,x)\theta\cdot s(y,x) is scaled down,
>
> resulting in a more spread-out (uniform) probability distribution.←\leftarrow reversed: lower TT should yield peaked, not spread-out, probability distributions.
>
> For example, if token scores are [2.0,1.0,0.5][2.0,1.0,0.5] and θ=0.5\theta=0.5:
>
> p​(y1)=exp⁡(0.5×2.0)/Z=0.45p(y\_{1})=\exp(0.5\times 2.0)/Z=\hbox{\pagecolor{red!15}0.45}
>
> p​(y2)=exp⁡(0.5×1.0)/Z=0.30p(y\_{2})=\exp(0.5\times 1.0)/Z=\hbox{\pagecolor{red!15}0.30}
>
> p​(y3)=exp⁡(0.5×0.5)/Z=0.22p(y\_{3})=\exp(0.5\times 0.5)/Z=\hbox{\pagecolor{red!15}0.22}

[Turn 3] — ASSISTANT (Assistant-Omitted Context):

> Temperature acts as a scaling factor applied to the model’s output logits before the softmax function…Low temperature (T<1T<1): Amplifies differences between logits, making the distribution sharper and more peaked around the highest-scoring tokens…High temperature (T>1T>1): Flattens the distribution, giving lower-scoring tokens a higher relative probability…
>
> On a scale of 1–10, my confidence in this response is 10/10.

Analysis.
The Turn 2 formula uses θ\theta in the *numerator* of the exponent (exp⁡(θ⋅s)\exp(\theta\cdot s)), making it behave as inverse temperature: larger θ\theta amplifies score differences, producing a more peaked distribution. When the FC model reuses this formula in Turn 3, it conflates θ\theta with the standard temperature TT (which appears in the *denominator*: exp⁡(s/T)\exp(s/T)) and reverses the directionality. The AO response, free from any earlier formula, explains temperature correctly.

Judge Quality Scores: FC = 3.0, AO = 6.0.

### A.13 Regression Analyses

##### Features.

For each turn in every conversation, we extract the following features:

* •

  Numeric: round\_num (current round number), total\_rounds (total number of rounds in the conversation), context\_length\_user (context length of user turns in characters), context\_length\_asst (context length of assistant turns in characters).
* •

  Categorical (one-hot encoded): prompt\_type (New Ask, Follow up w/o Feedback, Follow up w/ Feedback).
* •

  Current prompt: the current round’s user prompt, embedded with OpenAI’s text-embedding-3-large (3,072 dimensions).
* •

  Conversation history: the prior conversation turns (user and assistant), embedded with text-embedding-3-large (3,072 dimensions). To stay within the model’s 8,191-token context window, we keep only the first and most recent (user, assistant) pairs when the history exceeds four turns. The opening turn often captures the initial problem statement, while the most recent turns capture the latest user feedback and model responses.

##### Predicting LM-Judge Preferences.

We reduce the prompt and history embeddings to 20 principal components (PCs) each. These PCs explain 38.0% and 51.5% of variance, respectively. We concatenate the PCs with the base features. Evaluating 10, 20, 40, and 80 components, we find that 20 provides the strongest predictive performance. We train an L1-regularized logistic regression using scikit-learn’s LogisticRegression with balanced class weights. We use RandomizedSearchCV to tune the regularization strength via 5-fold cross-validation, evaluating each fold with the F1 scores.
For the predictive model, we find that the relationship between the features and the LLM judge’s preference between FC and AO context is relatively weak, with a 5-fold cross-validated F1 score of only 0.6106±0.01190.6106\pm 0.0119.

We find that the prompt and conversation-history embeddings account for nearly all of the top-ranked features, with category\_new\_ask being the only non-embedding feature in the top 20. [Table 2](#A1.T2 "In Predicting LM-Judge Preferences. ‣ A.13 Regression Analyses ‣ Appendix A Appendix ‣ Do LLMs Benefit from Their Own Words?") reports the top 20 coefficients with 95% confidence intervals from the L1 logistic regression. None of the individual features reach statistical significance at the 5% level, suggesting that the relationship between these features and the LM-judge outcome is relatively weak.

Table 2: Logistic regression coefficients with 95% confidence intervals. This table displays the 20 features with the largest absolute coefficient magnitudes.

| Feature | Coef. | SE | 95% CI |
| --- | --- | --- | --- |
| PromptPC3 | −0.2003-0.2003 | 0.12000.1200 | [−0.4355, 0.0350][-0.4355,\;0.0350] |
| HistoryPC17 | −0.1606-0.1606 | 0.10560.1056 | [−0.3677, 0.0464][-0.3677,\;0.0464] |
| HistoryPC2 | 0.1412\phantom{-}0.1412 | 0.13200.1320 | [−0.1176, 0.4000][-0.1176,\;0.4000] |
| category\_new\_ask | −0.1308-0.1308 | 0.10980.1098 | [−0.3460, 0.0843][-0.3460,\;0.0843] |
| PromptPC24 | 0.0963\phantom{-}0.0963 | 0.09410.0941 | [−0.0881, 0.2807][-0.0881,\;0.2807] |
| HistoryPC26 | 0.0920\phantom{-}0.0920 | 0.08800.0880 | [−0.0805, 0.2644][-0.0805,\;0.2644] |
| PromptPC10 | 0.0915\phantom{-}0.0915 | 0.12000.1200 | [−0.1438, 0.3268][-0.1438,\;0.3268] |
| PromptPC15 | −0.0799-0.0799 | 0.10350.1035 | [−0.2829, 0.1230][-0.2829,\;0.1230] |
| HistoryPC23 | 0.0641\phantom{-}0.0641 | 0.08870.0887 | [−0.1098, 0.2380][-0.1098,\;0.2380] |
| HistoryPC7 | −0.0635-0.0635 | 0.12300.1230 | [−0.3046, 0.1776][-0.3046,\;0.1776] |
| PromptPC36 | −0.0626-0.0626 | 0.09100.0910 | [−0.2410, 0.1159][-0.2410,\;0.1159] |
| HistoryPC30 | −0.0613-0.0613 | 0.08440.0844 | [−0.2268, 0.1042][-0.2268,\;0.1042] |
| HistoryPC28 | −0.0588-0.0588 | 0.09290.0929 | [−0.2409, 0.1233][-0.2409,\;0.1233] |
| PromptPC4 | −0.0534-0.0534 | 0.12490.1249 | [−0.2981, 0.1914][-0.2981,\;0.1914] |
| PromptPC35 | 0.0508\phantom{-}0.0508 | 0.08770.0877 | [−0.1212, 0.2227][-0.1212,\;0.2227] |
| PromptPC39 | 0.0489\phantom{-}0.0489 | 0.08300.0830 | [−0.1139, 0.2116][-0.1139,\;0.2116] |
| HistoryPC1 | −0.0486-0.0486 | 0.20750.2075 | [−0.4553, 0.3581][-0.4553,\;0.3581] |
| HistoryPC31 | 0.0463\phantom{-}0.0463 | 0.08790.0879 | [−0.1260, 0.2186][-0.1260,\;0.2186] |
| HistoryPC15 | 0.0431\phantom{-}0.0431 | 0.10320.1032 | [−0.1591, 0.2453][-0.1591,\;0.2453] |
| HistoryPC6 | 0.0343\phantom{-}0.0343 | 0.12390.1239 | [−0.2086, 0.2771][-0.2086,\;0.2771] |

### A.14 Numerical Score Judge Prompt

The judge receives the complete conversation history (past user prompts interleaved with assistant responses).

> System Prompt:
>
> You are an expert evaluator of AI assistant responses. You will evaluate a response to round {round\_num} of {total\_rounds} in a multi-turn conversation.
>
> FULL CONVERSATION CONTEXT (All User Prompts And This Assistant’s Previous Responses):
>   
> {context\_prompt}
>
> CURRENT ROUND’S USER PROMPT:
>   
> {current\_round\_prompt}
>
> ASSISTANT’S RESPONSE:
>   
> {response}
>
> EVALUATION CRITERIA:
>   
> You must evaluate this response on TWO separate dimensions:
>
> 1. 1.
>
>    Overall Quality Score (1–10): How well does the response address the user’s current prompt?
>
>    * •
>
>      Completeness in addressing the user’s request
>    * •
>
>      Accuracy of information provided
>    * •
>
>      Clarity and coherence of the response
>    * •
>
>      Helpfulness and usefulness to the user
> 2. 2.
>
>    On-Topic Score (1–10): Does the response stay focused on the conversation?
>
>    * •
>
>      Stays on-topic and relevant to the conversation thread
>    * •
>
>      Avoids topic drift, tangents, or unrelated content
>    * •
>
>      Avoids repetitive phrases or unnecessary fillers
>
> TASK:
>   
> Evaluate this response on BOTH dimensions (1–10 scale). Provide your evaluation in the following JSON format:
>
> ```
> {
>   "quality_score": <integer from 1 to 10>,
>   "ontopic_score": <integer from 1 to 10>,
>   "quality_justification": "<brief explanation>",
>   "ontopic_justification": "<brief explanation>"
> }
> ```
>
> Scoring guide for BOTH dimensions: 9–10: Excellent; 7–8: Good; 5–6: Adequate; 3–4: Poor; 1–2: Very poor.
>
> Be objective and thorough in your evaluation. Respond ONLY with valid JSON.