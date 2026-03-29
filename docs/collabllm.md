# CollabLLM: From Passive Responders to Active Collaborators

Shirley Wu
  
Michel Galley
  
Baolin Peng
  
Hao Cheng
  
Gavin Li
  
Yao Dou
  
Weixin Cai
  
James Zou
  
Jure Leskovec
  
Jianfeng Gao

###### Abstract

Large Language Models are typically trained with next-turn rewards, limiting their ability to optimize for long-term interaction.
As a result, they often respond passively to ambiguous or open-ended user requests, failing to help users reach their ultimate intents and leading to inefficient conversations.
To address these limitations, we introduce CollabLLM, a novel and general training framework that enhances multiturn human-LLM collaboration.
Its key innovation is a collaborative simulation that estimates the long-term contribution of responses using Multiturn-aware Rewards.
By reinforcement fine-tuning these rewards, CollabLLM goes beyond responding to user requests, and actively uncovers user intent and offers insightful suggestions—a key step towards more human-centered AI.
We also devise a multiturn interaction benchmark with three challenging tasks such as document creation.
CollabLLM significantly outperforms our baselines with averages of 18.5% higher task performance and 46.3% improved interactivity by LLM judges.
Finally, we conduct a large user study with 201 judges, where CollabLLM increases user satisfaction by 17.6% and reduces user spent time by 10.4%.

Machine Learning, ICML

<http://aka.ms/CollabLLM>

Figure 1: CollabLLM Framework: Given a context 1, the model generates a response 2 to maximize long-term collaboration gains, termed Multiturn-aware Rewards (MR). During training, MRs are estimated via 3 collaborative simulation, which forward-samples conversations with simulated users.
Finally, 4 reinforcement fine-tuning is applied using the MRs.

Figure 2: Real examples from CollabLLM and non-collaborative LLM fine-tuing. (a) Non-collaborative LLM fine-tuing relies single-turn rewards on immediate responses, which exhibits passive behaviors that follow the user’s requests, leading to user frustration, less efficient process, and less satisfactory results. (b) CollabLLM incorporates Multiturn-aware Rewards from collaborative simulation, enabling forward-looking strategies. This results in more high-performing, efficient, and interactive conversations that anticipate future needs, propose timely clarification, and provide insightful suggestions.

## 1 Introduction

Modern Large Language Models (LLMs) excel at generating high-quality single-turn responses when given well-specified inputs.
However, real-world users often do not fully articulate their intents and sometimes initiate conversations with an imprecise understanding of their own needs (Taylor, [1968](https://arxiv.org/html/2502.00640v3#bib.bib46)).
As a result, users routinely refine their requests post hoc through iterative corrections, which can increase frustration, hinder effective task completion, and reduce conversational efficiency (Amershi et al., [2019](https://arxiv.org/html/2502.00640v3#bib.bib2); Zamfirescu-Pereira et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib51); Wang et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib48); Kim et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib27)).
Therefore, an open problem is to train models that actively guide users in clarifying and refining their intents, and helps them achieve their goals.
This key challenge would improve user satisfaction and efficiency and streamline human-LLM interactions—especially as LLMs are being applied to real-world tasks that are increasingly complex and open-ended.

A notable limitation of established fine-tuning techniques, such as Reinforcement Learning from Human Feedback (RLHF) (Ouyang et al., [2022](https://arxiv.org/html/2502.00640v3#bib.bib34)), is that they primarily reward LLMs for immediate, single-turn responses, reducing their incentive to seek clarification or assist users in refining their intents or preferences.
As a result, commonly used LLMs tend to prioritize direct answers, even though seeking additional context would enhance task completion and increase user satisfaction (Kim et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib27)).

Here we introduce CollabLLM, a novel and general training framework that improves the ability of LLMs to effectively collaborate with humans in multiturn scenarios (Gao et al., [2019](https://arxiv.org/html/2502.00640v3#bib.bib15); Balog & Zhai, [2023](https://arxiv.org/html/2502.00640v3#bib.bib4); Rahmani et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib40)).
The key innovation of CollabLLM is to promote LLMs’ forward-looking behavior that leads to long-term collaboration gains (Figure [1](https://arxiv.org/html/2502.00640v3#S0.F1 "Figure 1 ‣ CollabLLM: From Passive Responders to Active Collaborators")).
We introduce a collaborative simulation module that samples future conversations with users to estimate the long-term impact of model responses across multiple turns, a measure we term the Multiturn-aware Reward (MR).
The MR function evaluates responses by incorporating both extrinsic metrics, such as task-specific success, and intrinsic metrics, such as efficiency, to holistically assess collaboration quality (cf. Section [3](https://arxiv.org/html/2502.00640v3#S3 "3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators")).
By fine-tuning with RL algorithms (Rafailov et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib39); Schulman et al., [2017](https://arxiv.org/html/2502.00640v3#bib.bib41)) on MRs, CollabLLM promotes responses that lead to better task completion and efficiency in later conversation stages.
As shown in Figure [2](https://arxiv.org/html/2502.00640v3#S0.F2 "Figure 2 ‣ CollabLLM: From Passive Responders to Active Collaborators")b, the fine-tuned model goes beyond simply responding to user requests in Figure [2](https://arxiv.org/html/2502.00640v3#S0.F2 "Figure 2 ‣ CollabLLM: From Passive Responders to Active Collaborators")a—it actively collaborates by asking follow-up questions about the writing tone, generating targeted content about the role of optimism, and offering insightful suggestions such as adding anecdotes.

We also introduce three challenging multiturn tasks for training and evaluation in simulated environments: MediumDocEdit-Chat, BigCodeBench-Chat, and MATH-Chat, which respectively encompass document creation, code generation, and multiturn question answering.
On the three test sets, our approach improves task accuracy metrics by 18.5% and interactivity by 46.3% on average compared to our best baselines, according to LLM judges. Beyond the tasks that the CollabLLMs are fine-tuned on, we show CollabLLMs are highly generalizable to other data domains.

Moreover, we perform a large-scale and real-world user study with 201 Amazon Mechanical Turkers (MTurkers), who are asked to write documents with the help of anonymous AI assistants, either CollabLLM or non-collaboratively trained LLMs.
CollabLLM achieves impressive improvement with 17.6% increase in user satisfaction and yield user time savings of
10.4% on average.
The qualitative analysis from MTurkers confirms our observations: non-collaboratively-trained LLMs passively agree with users, while CollabLLM actively provide insightful questions and suggestions to guide writing processes.

## 2 Problem Formulation

In contrast to many existing tasks that are single-turn and require no human involvement beyond the initial query, our problem formulation reflects a real-world setting in which a user’s underlying (implicit) goal is defined as ggitalic\_g in a multiturn conversational task. The conversation unfolds over multiple turns tj={uj,mj}t\_{j}=\{u\_{j},m\_{j}\}italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT = { italic\_u start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT , italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT }, where uju\_{j}italic\_u start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT is the user input and mjm\_{j}italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT is the model’s response at each turn j=1,…,Kj=1,\dots,Kitalic\_j = 1 , … , italic\_K, where KKitalic\_K is the number of turns in the conversation.

At the jjitalic\_j-th turn, the model generates its response based on the previous conversation turns t1:j−1={t1,…,tj−1}t\_{1:j-1}=\{t\_{1},\dots,t\_{j-1}\}italic\_t start\_POSTSUBSCRIPT 1 : italic\_j - 1 end\_POSTSUBSCRIPT = { italic\_t start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , … , italic\_t start\_POSTSUBSCRIPT italic\_j - 1 end\_POSTSUBSCRIPT } and the current user response uju\_{j}italic\_u start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT. For simplicity, we define historical conversation at jjitalic\_j-th turn as tjh=t1:j−1∪{uj}t^{h}\_{j}=t\_{1:j-1}\cup\{u\_{j}\}italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT = italic\_t start\_POSTSUBSCRIPT 1 : italic\_j - 1 end\_POSTSUBSCRIPT ∪ { italic\_u start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT }, therefore, mj=M​(tjh)m\_{j}=M(t^{h}\_{j})italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT = italic\_M ( italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ).
The objective is to generate a sequence of model responses {mj}j=1K\{m\_{j}\}\_{j=1}^{K}{ italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT } start\_POSTSUBSCRIPT italic\_j = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_K end\_POSTSUPERSCRIPT that effectively and efficiently achieve for goal ggitalic\_g, e.g., answering a math question, where goal achievement is assessed based on user satisfaction or an external evaluation function, such as accuracy by LLM judge.
Formally, we define the objective as R∗​(t1:K∣g)R^{\*}(t\_{1:K}\mid g)italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ), where R∗R^{\*}italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT incorporate the achievement of task success and user experience factors such as time cost.

## 3 Unified Collaborative LLM Training

Key Motivations. Established LLM training frameworks, such as Reinforcement Learning from Human Feedback (RLHF) (Ouyang et al., [2022](https://arxiv.org/html/2502.00640v3#bib.bib34)), focus on maximizing immediate rewards for single-turn tasks. This cause a misalignment between their single-turn objective and real-world multiturn objective R∗​(t1:K∣g)R^{\*}(t\_{1:K}\mid g)italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ).
Precisely, the model’s accumulative single-turn reward ∑j=1j=KR​(mj∣tjh)\sum\_{j=1}^{j=K}R(m\_{j}\mid t\_{j}^{h})∑ start\_POSTSUBSCRIPT italic\_j = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_j = italic\_K end\_POSTSUPERSCRIPT italic\_R ( italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT ) may not imply a higher final reward R∗​(t1:K∣g)R^{\*}(t\_{1:K}\mid g)italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ). In fact, achieving high single-turn rewards at each turn may not imply a higher final reward. For example, consider a task where the user’s goal ggitalic\_g is to write an engaging article. A model trained with traditional RLHF might generate isolated responses, like drafting an introduction or listing conclusions. While these responses are helpful in isolation, they fail to consider how the sections flow together, resulting in an article that might not be cohesive and aligned with the user’s goal.

Instead, effective multiturn collaboration requires model responses that optimally contribute to the final reward. The model should aim to align its responses with the user’s goal ggitalic\_g by considering their impact on the entire conversation trajectory t1:Kt\_{1:K}italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT.
In the previous example, instead of generating a conclusion, asking, “Should I maintain an engaging tone in the conclusion like the introduction?” offers better long-term alignment with the goal.

### 3.1 Multiturn-aware Rewards

In Figure [1](https://arxiv.org/html/2502.00640v3#S0.F1 "Figure 1 ‣ CollabLLM: From Passive Responders to Active Collaborators"), our key insight is that effective multiturn collaboration relies on forward-looking strategies. Given a context 1, the model should consider how its response 2 influences the subsequent turns of the conversation. To capture this, we design a 3 collaborative simulation module to estimate this impact. By 4 fine-tuning to distinguish between potential future conversations resulting from different responses, the model generates responses that align better with the overarching goal ggitalic\_g.

This high-level design naturally aligns with causal effect estimation (Pearl, [2009](https://arxiv.org/html/2502.00640v3#bib.bib37); Pearl et al., [2016](https://arxiv.org/html/2502.00640v3#bib.bib38)), which evaluates the interventional effects of an action in sequential decision-making.
Appendix [A](https://arxiv.org/html/2502.00640v3#A1 "Appendix A Supplementary Discussion ‣ CollabLLM: From Passive Responders to Active Collaborators") provides further discussion on the connection between causal effect estimation and our approach.
More specifically, we define the Multiturn-aware Reward:

Multiturn-aware Reward (MR):
The multiturn-aware reward for model response mjm\_{j}italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT at the jjitalic\_j-th turn is given by:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  |  | MR​(mj∣tjh,g)\displaystyle\text{{MR}}(m\_{j}\mid t\_{j}^{h},g)MR ( italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT , italic\_g ) |  | (1) |
|  | =\displaystyle== | 𝔼tjf∼P​(tj+1:K∣tjh∪{mj})​R∗​(tjh∪{mj}∪tjf∣g)\displaystyle~\mathbb{E}\_{t\_{j}^{f}\sim P(t\_{j+1:K}\mid t\_{j}^{h}\cup\{m\_{j}\})}R^{\*}(t\_{j}^{h}\cup\{m\_{j}\}\cup t\_{j}^{f}\mid g)blackboard\_E start\_POSTSUBSCRIPT italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∼ italic\_P ( italic\_t start\_POSTSUBSCRIPT italic\_j + 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT ∪ { italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT } ) end\_POSTSUBSCRIPT italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT ∪ { italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT } ∪ italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_g ) |  |
|  | =\displaystyle== | 𝔼tjf∼P​(tjf∣t1:j)​R∗​(t1:j∪tjf∣g),\displaystyle~\mathbb{E}\_{t\_{j}^{f}\sim P(t\_{j}^{f}\mid t\_{1:j})}R^{\*}(t\_{1:j}\cup t\_{j}^{f}\mid g),blackboard\_E start\_POSTSUBSCRIPT italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∼ italic\_P ( italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT ) end\_POSTSUBSCRIPT italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT ∪ italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_g ) , |  |

where t1:jt\_{1:j}italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT denotes the conversation history up to and including the jjitalic\_j-th turn, and tjf=tj+1:Kt\_{j}^{f}=t\_{j+1:K}italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT = italic\_t start\_POSTSUBSCRIPT italic\_j + 1 : italic\_K end\_POSTSUBSCRIPT represents the forward trajectory of turns following the jjitalic\_j-th turn. The distribution P​(tjf∣t1:j)P(t\_{j}^{f}\mid t\_{1:j})italic\_P ( italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT ) models the possible forward conversations conditioned on the prior conversation history.

However, computing Equation [1](https://arxiv.org/html/2502.00640v3#S3.E1 "Equation 1 ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators") remains challenging as it requires the following components:
(a) A conversation-level reward function, R∗​(t∣g)R^{\*}(t\mid g)italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t ∣ italic\_g ), for evaluating an arbitrary multiturn conversation ttitalic\_t, and
(b) a sampling strategy for obtaining forward conversations P​(tjf∣t1:j)P(t\_{j}^{f}\mid t\_{1:j})italic\_P ( italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT ), which represents the forward conversation distribution. We elaborate on the two components in Section [3.1.1](https://arxiv.org/html/2502.00640v3#S3.SS1.SSS1 "3.1.1 Conversation-level Reward Function ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators") and [3.1.2](https://arxiv.org/html/2502.00640v3#S3.SS1.SSS2 "3.1.2 Forward Sampling ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators").

#### 3.1.1 Conversation-level Reward Function

We approximate the conversation-level reward R∗​(t∣g)R^{\*}(t\mid g)italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t ∣ italic\_g ) with a combination of extrinsic (goal-specific) and intrinsic (goal-agnostic) metrics:

|  |  |  |  |
| --- | --- | --- | --- |
|  | R∗​(t∣g)≃Rext​(t,g)+Rint​(t),R^{\*}(t\mid g)\simeq R\_{\text{ext}}(t,g)+R\_{\text{int}}(t),italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t ∣ italic\_g ) ≃ italic\_R start\_POSTSUBSCRIPT ext end\_POSTSUBSCRIPT ( italic\_t , italic\_g ) + italic\_R start\_POSTSUBSCRIPT int end\_POSTSUBSCRIPT ( italic\_t ) , |  | (2) |

where Rext​(t,g)R\_{\text{ext}}(t,g)italic\_R start\_POSTSUBSCRIPT ext end\_POSTSUBSCRIPT ( italic\_t , italic\_g ) focuses on task success, and Rint​(t)R\_{\text{int}}(t)italic\_R start\_POSTSUBSCRIPT int end\_POSTSUBSCRIPT ( italic\_t ) evaluates user experience including efficiency and engagement.

* •

  Extrinsic Reward Rext​(t,g)R\_{\text{ext}}(t,g)italic\_R start\_POSTSUBSCRIPT ext end\_POSTSUBSCRIPT ( italic\_t , italic\_g ) measures how well the conversation achieves the user’s goal ggitalic\_g. Formally:

  |  |  |  |  |
  | --- | --- | --- | --- |
  |  | Rext​(t,g)=S​(Extract⁡(t),yg),R\_{\text{ext}}(t,g)=S(\operatorname{Extract}(t),y\_{g}),italic\_R start\_POSTSUBSCRIPT ext end\_POSTSUBSCRIPT ( italic\_t , italic\_g ) = italic\_S ( roman\_Extract ( italic\_t ) , italic\_y start\_POSTSUBSCRIPT italic\_g end\_POSTSUBSCRIPT ) , |  | (3) |

  where Extract⁡(t)\operatorname{Extract}(t)roman\_Extract ( italic\_t ) extracts the final solution or response from the conversation ttitalic\_t, especially for tasks requiring revisions or multi-step answers. ygy\_{g}italic\_y start\_POSTSUBSCRIPT italic\_g end\_POSTSUBSCRIPT is the reference solution for the goal ggitalic\_g, e.g., the ground truth solution for a math problem. And S​(⋅,⋅)S(\cdot,\cdot)italic\_S ( ⋅ , ⋅ ) evaluates task-specific metrics like accuracy or similarity. This ensures the conversation contributes directly to achieving the desired goal.
* •

  Intrinsic Reward Rint​(t)R\_{\text{int}}(t)italic\_R start\_POSTSUBSCRIPT int end\_POSTSUBSCRIPT ( italic\_t ) prioritizes conversations that enhance user experience, defined as:

  |  |  |  |  |
  | --- | --- | --- | --- |
  |  | Rint​(t)=−min⁡[λ⋅TokenCount​(t),1]+RLLM​(t),R\_{\text{int}}(t)=-\min[\lambda\cdot\text{TokenCount}(t),1]+R\_{\text{LLM}}(t),italic\_R start\_POSTSUBSCRIPT int end\_POSTSUBSCRIPT ( italic\_t ) = - roman\_min [ italic\_λ ⋅ TokenCount ( italic\_t ) , 1 ] + italic\_R start\_POSTSUBSCRIPT LLM end\_POSTSUBSCRIPT ( italic\_t ) , |  | (4) |

  where we encourage conversational efficiency by penalizing excessive tokens that users read and write, with λ\lambdaitalic\_λ controlling the penalty severity. This efficiency measure is bounded by 1 to maintain balance with other metrics. The second term, RLLM​(t)R\_{\text{LLM}}(t)italic\_R start\_POSTSUBSCRIPT LLM end\_POSTSUBSCRIPT ( italic\_t ), is assigned by an LLM-based judge (Zheng et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib55)) on a 0–1 scale, evaluating user-valued objectives such as engagement / interactivity. Notably, additional conversational aspects, such as clarity, can be further integrated into the objective.

The conversation-level reward incorporates task-specific and human-centered metrics, encouraging the model to balance goal achievement, efficiency, and engagement.

Figure 3: Simulated Multiturn Environment for Evaluation. Our evaluation pipeline simulates real-world collaborations by prompting an user simulator LLM to emulate diverse behaviors and personalities in multiturn conversations.

#### 3.1.2 Forward Sampling

To compute Eq. [1](https://arxiv.org/html/2502.00640v3#S3.E1 "Equation 1 ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators"), we require samples from P​(tjf∣t1:j)P(t\_{j}^{f}\mid t\_{1:j})italic\_P ( italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT ∣ italic\_t start\_POSTSUBSCRIPT 1 : italic\_j end\_POSTSUBSCRIPT ), the distribution of forward conversation conditioned on the conversation history.
A simple approach is to use Monte Carlo sampling, where the conversation is extended turn-by-turn until it concludes.
However, this can be computationally expensive for computing reward for every model response.
For a scalable approximation, we introduce a window size wwitalic\_w as a hyperparameter to limit the maximum number of forward turns considered in tjft\_{j}^{f}italic\_t start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_f end\_POSTSUPERSCRIPT. This reduces the computational cost while maintaining sufficient context.

More importantly, while real-world conversations could be gathered from human participants, sampling multiple forward conversations during training is costly and impractical. To further reduce cost and ensure scalability, we introduce a user simulator UUitalic\_U.

User Simulator:.
A user simulator U:𝒯→𝒰U:\mathcal{T}\rightarrow\mathcal{U}italic\_U : caligraphic\_T → caligraphic\_U is a function that maps a given conversation history t∈𝒯t\in\mathcal{T}italic\_t ∈ caligraphic\_T to a user response u∈𝒰u\in\mathcal{U}italic\_u ∈ caligraphic\_U. Specifically, UUitalic\_U generates a probabilistic distribution P​(u∣t)P(u\mid t)italic\_P ( italic\_u ∣ italic\_t ) over possible user responses conditioned on the conversation history ttitalic\_t, simulating realistic user behavior.

Specifically, we prompt an LLM to role-play as users, explicitly asking the LLM to follow the same language style as the previous user turns, and injecting typical user behaviors. The user simulator operates with an implicit goal ggitalic\_g, which it seeks to achieve over the course of the conversation. This design emulates real-world scenarios where users may have evolving needs, limited background knowledge, or require clarification, resulting in naturally unfolding multiturn conversations (Park et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib36)).

### 3.2 Optimization & Synthetic Datasets

With the conversation-level reward function and forward sampling strategy, we can compute MR for any model response without requiring an additional reward model, which is often costly and slow to train. Unlike traditional single-turn reward approaches, MR explicitly accounts for the impact of a response on future conversations, promoting long-term collaboration.

Further, we employ reinforcement learning (RL) methods such as PPO (Schulman et al., [2017](https://arxiv.org/html/2502.00640v3#bib.bib41)) and DPO (Rafailov et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib39)) to guide the model in navigating complex conversations. By optimizing for higher MR, the model learns to generate responses that enhance overall effectiveness and efficiency by the end of the conversation.

Moreover, MR can generate high-quality synthetic conversations (cf. Figure [8](https://arxiv.org/html/2502.00640v3#A2.F8 "Figure 8 ‣ B.1 Dataset Generation for Offline Training ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators") in Appendix [B](https://arxiv.org/html/2502.00640v3#A2 "Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators")) for both supervised fine-tuning (SFT) and DPO. For SFT, it iteratively selects top-ranked responses to build realistic, goal-directed conversation histories. For DPO, it constructs pairwise comparisons by ranking responses at each turn, distinguishing “chosen” and “rejected” pairs based on MR scores. The generated synthetic data aligns with multiturn objectives.

Overall, CollabLLM enables scalable dataset generation and online RL training without human annotation, making it generalizable across diverse tasks. In Appendix [7](https://arxiv.org/html/2502.00640v3#S7 "7 Related Work ‣ CollabLLM: From Passive Responders to Active Collaborators"), we compare CollabLLM with related prompting- and training-based approaches, highlighting its contributions.

## 4 Experimental Setup\*\*\*Dataset and training details in Appendix [B](https://arxiv.org/html/2502.00640v3#A2 "Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators"); all prompts (e.g., prompts of user simulator and LLM judges) in Appendix [D](https://arxiv.org/html/2502.00640v3#A4 "Appendix D Prompts ‣ CollabLLM: From Passive Responders to Active Collaborators").

For fine-tuning and evaluation, we create three multiturn datasets using publicly available data across diverse domains (Hendrycks et al., [2021](https://arxiv.org/html/2502.00640v3#bib.bib19); Zhuo et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib57); Chiusano, [2024](https://arxiv.org/html/2502.00640v3#bib.bib8)): collaborative document editing, coding problem assistance, and multiturn mathematics problem solving.

To build a multiturn environment (Figure [3](https://arxiv.org/html/2502.00640v3#S3.F3 "Figure 3 ‣ 3.1.1 Conversation-level Reward Function ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators")), we employ GPT-4o-mini as a user simulator LLM to role-play realistic user behaviors, given the target problem and conversation history. Our simulation-based evaluations are designed to closely mimic real-world interactions (Park et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib36)).
Unlike traditional single-turn tasks, our setup requires dynamic interactions over multiple turns to achieving a goal.
The three interactive datasets are:

MediumDocEdit-Chat: Document editing requires iterative feedback and refinements across multiple turns to ensure coherence and alignment with user intent. We sample 100 Medium articles as goal documents, which are summarized into target problems to guide the user simulator. After each interaction, task performance is evaluated using the BLEU score, measuring similarity between the extracted document and the original articles.

BigCodeBench-Chat: Coding tasks inherently require multiturn interactions, such as clarifying requirements and debugging. We sample 600 coding problems from BigCodeBench (Zhuo et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib57)) as the target problems given to the user simulator. For evaluation, we compute the average Pass Rate (PR) of code at the end of the interactions.

MATH-Chat: Math problem solving often requires addressing implicit assumptions, verifying intermediate steps, and clarifying reasoning. We sample 200 level-5 math problems from MATH (Hendrycks et al., [2021](https://arxiv.org/html/2502.00640v3#bib.bib19)) to prompt the user simulator, which interacts with the LLMs. Task success is measured by the accuracy (ACC) of the final solution, as evaluated by an LLM judge.

In addition to the above task-specific metrics, we incorporate two task-agnostic scores across all datasets: 1) Average Token Count, which quantifies the average number of tokens generated by the LLM per conversation, reflecting interaction efficiency. 2) Interactivity (ITR), which evaluates engagement levels using an LLM judge (Claude-3.5-Sonnet), with scores rescaled to an upper bound of 1.

Table 1: Evaluation results on our multiturn datasets.
Green zone: Baselines; Orange zone: Variants of CollabLLMs. Rel. Improv. indicates the relative improvements of CollabLLMs trained with Online DPO over Proactive Base.

|  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | MediumDocEdit-Chat | | | BigCodeBench-Chat | | | MATH-Chat | | |
|  | BLEU ↑\uparrow↑ | #Tokens(k)↓(k)\downarrow( italic\_k ) ↓ | ITR ↑\uparrow↑ | PR ↑\uparrow↑ | #Tokens(k)↓(k)\downarrow( italic\_k ) ↓ | ITR ↑\uparrow↑ | ACC ↑\uparrow↑ | #Tokens(k)↓(k)\downarrow( italic\_k ) ↓ | ITR ↑\uparrow↑ |
| Base | 32.2 | 2.49 | 46.0 | 9.3 | 1.59 | 22.0 | 11.0 | 3.40 | 44.0 |
| Proactive Base | 35.0 | 2.18 | 62.0 | 11.0 | 1.51 | 33.7 | 12.5 | 2.90 | 46.0 |
| SFT | 35.2 | 2.21 | 68.0 | 11.7 | 1.35 | 42.0 | 13.5 | 2.88 | 58.0 |
| PPO | 38.5 | 2.00 | 78.0 | 14.0 | 1.35 | 40.7 | 13.0 | 2.59 | 52.0 |
| Offline DPO | 36.4 | 2.15 | 82.0 | 12.3 | 1.35 | 46.7 | 15.5 | 2.40 | 50.0 |
| Online DPO | 36.8 | 2.00 | 92.0 | 13.0 | 1.31 | 52.0 | 16.5 | 2.37 | 60.0 |
| Rel. Improv. | 5.14% | 8.25% | 48.3% | 18.2% | 13.2% | 54.3% | 32.0% | 18.3% | 36.4% |


Figure 4: Selected Ablation Study of Reward Mechanisms on MediumDocEdit-Chat. This figure compares three immediate reward mechanisms with three MR variants. The results demonstrate that MR consistently improves task-specific performance (BLEU), conversational efficiency (# Tokens), and interactivity (ITR). See Appendix [B.3](https://arxiv.org/html/2502.00640v3#A2.SS3 "B.3 Full Ablation Results ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators") for the full results.

Fine-tuning CollabLLMs. CollabLLMs are based on Llama-3.1-8B-Instruct (Llama Team, [2024](https://arxiv.org/html/2502.00640v3#bib.bib32)) with LoRA finetuning (Hu et al., [2022](https://arxiv.org/html/2502.00640v3#bib.bib21)). We train four model variants: 1) Offline models: SFT and Offline DPO are fine-tuned on pre-generated multiturn conversational datasets guided by Multiturn-aware Rewards (MR) (cf. Section [3.2](https://arxiv.org/html/2502.00640v3#S3.SS2 "3.2 Optimization & Synthetic Datasets ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators")). 2) Online models: PPO and Online DPO are further trained from the SFT and Offline DPO models, respectively. The model during online fine-tuning is involved in the collaborative simulation to compute MRs, which, in turn, dynamically adjust the model preference.

Baselines. We compare CollabLLMs against (1) the pretrained Llama-3.1-8B-Instruct (Base), (2) the base model with proactive prompt engineering (Proactive Base), which encourages follow-up and clarification questions.

Figure 5: Case study on BigCodeBench-Chat. The non-collaborative LLM assumes user needs, adding unnecessary steps like punctuation and stopword removal. In contrast, CollabLLM clarifies tokenizer preferences, error handling, and package installation, leading to a solution that precisely aligns with user intent.


Figure 6: Reward comparison for response A and B of Figure [5](https://arxiv.org/html/2502.00640v3#S4.F5 "Figure 5 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators") shows different preferences.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | Action-level Accuracy | | Macro Metric | |
|  | Ambiguous | Non-Ambiguous | Accuracy | F1 |
| GPT-4o | 15.44% | 95.60% | 55.52% | 56.62% |
| Llama-3.1-8B-Instruct | 16.26% | 90.40% | 53.33% | 53.31% |
| CollabLLM | 52.84% | 72.32% | 62.58% | 55.08% |

Table 2: Zero-shot generalization to Abg-CoQA, a conversational QA benchmark to identify ambiguity. We assess action-level accuracy, measuring whether the model asks a question for ambiguous inputs and provides a direct answer for non-ambiguous ones.

## 5 Results of Simulated Experiments

We present the results in Table [1](https://arxiv.org/html/2502.00640v3#S4.T1 "Table 1 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators") and the takeaways are:

Prompt engineering is helpful, but limited in terms of performance gains and flexibility.
Proactive Base improves base model performance by encouraging follow-up questions and clarifications. For example, it increases BLEU on MediumDocEdit-Chat from 32.2% to 35.0% and reduces read tokens by 0.31k compared to the base model. However, these gains are modest and do not fully address the challenges of multiturn collaboration. We observe that prompting strategies remain rigid, relying on predefined instructions rather than adapting dynamically to user needs. For instance, the model sometimes asks clarification questions even when unnecessary, leading to redundant interactions that disrupt conversation flow.

CollabLLM improves task performance, efficiency, and engagement.
CollabLLM achieves 18.5% superior task-specific performance, 13.3% more efficient conversations, and 46.3% enhanced interactivity compared to the best baselines.
We highlight that CollabLLM engage in more meaningful collaborations, with ITR shows substantial gains. For MediumDocEdit-Chat, the Online DPO model increases ITR from 0.46 to 0.92.
Moreover, our framework significantly improves conversational efficiency by minimizing the content users need to review to arrive at the final solution. For MATH-Chat, Online DPO decreases token count per conversation by 1.03k compared to the base model.

### 5.1 Ablations on Reward Mechanisms (Figure [4](https://arxiv.org/html/2502.00640v3#S4.F4 "Figure 4 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"))

To investigate how components contribute to CollabLLM’s superior performance, we conduct an ablation study focusing on the reward mechanisms used during fine-tuning.
We evaluate the following reward mechanisms:

* •

  Variants of Multiturn-aware Reward: We vary the forward sampling window size w=1,2,3w=1,2,3italic\_w = 1 , 2 , 3 to assess their ability to capture long-term conversational effects through simulated collaborations.
* •

  Immediate Rewards evaluate the model’s immediate response based on:
  1) Helpfulness: Assessed by an LLM judge;
  2) Extrinsic Reward: Focuses on task-specific metrics like BLEU while ignoring intrinsic factors such as efficiency;
  3) Extrinsic + Intrinsic Reward: Combines task-specific metrics with efficiency and interactivity measures. This can be seen as a special case of the multiturn-aware reward function with w=0w=0italic\_w = 0.

Figure 7: Our real-world user study includes 201 participants interacting with an anonymized AI assistant randomly sampled from Base, Proactive Base, and CollabLLM. Participants rate (a) document quality and (b) overall interaction experience, with additional assessments (d) every three turns. We also measure (c) user spent time to evaluate efficiency.

We present results in Figure [4](https://arxiv.org/html/2502.00640v3#S4.F4 "Figure 4 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators").
Interestingly,
expanding the forward sampling window wwitalic\_w within the range generally enhances performance and efficiency by better capturing future interactions. Notably, MR with w=2w=2italic\_w = 2 balances the gains and additional costs to conduct forward sampling, making it well-suited for large-scale fine-tuning. In contrast, immediate rewards, even with extrinsic and intrinsic components, fall short as they ignore long-term impact.
These findings validate the positive impact of the forward sampling strategy in MRs.

### 5.2 Case Study (Figure [5](https://arxiv.org/html/2502.00640v3#S4.F5 "Figure 5 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators") &  [6](https://arxiv.org/html/2502.00640v3#S4.F6 "Figure 6 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"))

We now offer a deeper insight into CollabLLM’s behavior as shown in Figure [5](https://arxiv.org/html/2502.00640v3#S4.F5 "Figure 5 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"). In this example,
the user request to tokenize a text file is inherently open-ended due to unspecified factors, such as the NLTK environment, tokenizer selection, and optional preprocessing steps. The base LLM makes several arbitrary assumptions, applying lowercase conversion and stopword removal without user confirmation. The user simulator later corrects these assumptions, but the final solution remains incorrect due to missing stopwords.
In contrast, CollabLLM actively clarifies user intent by seeking confirmation on key decisions, ensuring an aligned final solution with a 100% Pass Rate. This approach also reduces user effort with lower token usage.

In Figure [6](https://arxiv.org/html/2502.00640v3#S4.F6 "Figure 6 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"), we compare different reward mechanisms for responses A and B of Figure [5](https://arxiv.org/html/2502.00640v3#S4.F5 "Figure 5 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"), to confirm that these rewards work as intended. The helpfulness rewards favor response A due to its seemingly more well-round output. Extrinsic rewards assign zero scores to both, as A provides an incorrect solution and B defers answering. Extrinsic + Intrinsic rewards slightly favor B for efficiency and engagement. Interestingly, MR assigns significantly higher rewards to B, especially at w=2w=2italic\_w = 2 and w=3w=3italic\_w = 3, since the response obtains useful information and provide a precise answer within the future interaction window.

Table 3: Representative Feedback from Human Participants.

|  |  |  |
| --- | --- | --- |
| Model | Strengths | Weaknesses |
| Base | “Follows great instruction and does exactly what I’m asking it to do.”, “It can create a nice form of an outline to work with.” | “The AI just agreed with me on pretty much everything. There was no discussion”, “I didn’t really like that it kept coming up with different options” |
| Proactive Base | “It is very organized and it actually asks you for feedback after writing the revision.” | “The AI seemed to be very redundant and asked me the same questions over and over.” |
| Collab LLM | “Asking questions and making you think of things you never thought of”, “The AI really helped me with focusing on one part of the story at a time.”, “It helped really well to navigate what to say and what information is needed” | “The AI assistant was not up to date enough to help with this recent sporting event. The AI assistant also asked me to repeat information I had already given it.” |

### 5.3 Model Generalization (Table [2](https://arxiv.org/html/2502.00640v3#S4.T2 "Table 2 ‣ Figure 6 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"))

Modern foundation models are expected to generalize across a diverse range of tasks beyond their training domain. A key question is whether collaborative behaviors learned by CollabLLM during fine-tuning transfer effectively to new tasks without additional adaptation.

We assess CollabLLM, trained with online DPO on BigCodeBench-Chat (the coding assistance task), on Abg-CoQA (Guo et al., [2021](https://arxiv.org/html/2502.00640v3#bib.bib18)), a question-answering (QA) benchmark where questions are labeled as ambiguous or non-ambiguous (cf. Appendix [E](https://arxiv.org/html/2502.00640v3#A5 "Appendix E Question Template and Example on Abg-CoQA ‣ CollabLLM: From Passive Responders to Active Collaborators")).
We categorize the model’s responses into two actions—asking a clarifying question or providing a direct answer—and evaluate action-level accuracy within each question type.
As shown in Table [2](https://arxiv.org/html/2502.00640v3#S4.T2 "Table 2 ‣ Figure 6 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"),
GPT-4o and Llama-3.1-8B-Instruct rarely ask clarifying questions regardless of ambiguity.
In contrast,
CollabLLM asks questions about 50% of the time while maintaining high accuracy on unambiguous inputs.
This behavior leads to the highest Macro Accuracy across both ambiguous and non-ambiguous sets and improves Macro F1 over the base model, while leaving room for further improvement against GPT-4o. These results suggest that CollabLLM effectively generalizes its learned collaborative strategies beyond its training domain.

## 6 Real-world User Study

Setup.
We conduct a large-scale user study using Amazon Mechanical Turk with 201 participants. Each participant is assigned a document type—randomly selected to be either blog post, creative writing, or personal statement—and chooses a topic from a predefined set. To simulate real-world scenarios where users have only a rough idea of the task, they are first asked to provide brief responses to topic-related questions.
Participants then engage in at least eight turns of conversation with an anonymized AI assistant, which can be Base, Proactive Base, or CollabLLM. Every three turns, they provide an interaction rating based on their experience so far. After the conversation, participants rate the final document quality and overall interaction. All ratings are in a scale from 1 to 10. We also record the total interaction duration to assess efficiency.
The detailed user study setup is provided in Appendix [F](https://arxiv.org/html/2502.00640v3#A6 "Appendix F User Study ‣ CollabLLM: From Passive Responders to Active Collaborators").

Quantitative Results (Figure [7](https://arxiv.org/html/2502.00640v3#S5.F7 "Figure 7 ‣ 5.1 Ablations on Reward Mechanisms (Figure 4) ‣ 5 Results of Simulated Experiments ‣ CollabLLM: From Passive Responders to Active Collaborators")). Across multiple metrics, CollabLLM consistently outperforms the baselines. It achieves an average document quality score of 8.50. Specifically, 91.4% of participants rate CollabLLM’s document quality as “good” (score 8–9), and 56.9% as “very good” (score 9–10), compared to 88.5% and 39.3% for Base (Llama-3.1-8B-Instruct), respectively. Similarly, 63.8% of participants find CollabLLM highly engaging, while only 42.6% report the same for Base.

Interestingly, for multiturn interaction, the Base model shows a declining trend in ratings from turns 6–9, indicating reduced user experience in longer conversations. In contrast, both CollabLLM and Proactive Base exhibit increasing ratings over time, with CollabLLM consistently achieving higher average ratings every three turns compared to Proactive Base. This suggests that CollabLLM maintains sustained engagement more effectively.

Moreover, CollabLLM improves task efficiency, reducing time spent by 10.4% compared to the Base model and by 15.6% relative to Proactive Base. While Proactive Base is prompted to maintain conciseness, it frequently asks unnecessary questions, causing lower efficiency. In contrast, CollabLLM strikes a more streamlined user experience.

Qualitative Results (Table [3](https://arxiv.org/html/2502.00640v3#S5.T3 "Table 3 ‣ 5.2 Case Study (Figure 5 & 6) ‣ 5 Results of Simulated Experiments ‣ CollabLLM: From Passive Responders to Active Collaborators")). We collected a total of 180 strengths and 180 weaknesses across the three models. Table [3](https://arxiv.org/html/2502.00640v3#S5.T3 "Table 3 ‣ 5.2 Case Study (Figure 5 & 6) ‣ 5 Results of Simulated Experiments ‣ CollabLLM: From Passive Responders to Active Collaborators") presents representative feedback, while we summarize here the mddels’ strengths and weaknesses:
The base model generates coherent content while effectively follow user instructions, but it sometimes struggles with maintaining context in long texts, and can be overly verbose or repetitive in its responses.
Proactive Base excels in responsiveness and adapting to user input but struggles with memory retention, and could produce repetitive or overly structured content.
On the other hand, CollabLLM is highly engaging, effectively guiding users through writing, adapting seamlessly to feedback. However, users also point out that CollabLLM can occasionally feel bland, lack of up to date information, and require additional effort to personalize the output.
Overall, CollabLLM enhances collaboration by guiding users through an interactive and iterative refinement process, yet future improvements should focus on increasing personalization, creativity, and real-time knowledge integration to further optimize human-LLM collaboration.

## 7 Related Work

Table 4: Compare CollabLLM with Selected Works. (1) Task-Agnostic, assessing whether the approach applies across diverse domains rather than being task-specific; (2) Versatile Interaction, evaluating its ability to support diverse strategies for intent discovery and efficient task completion beyond predefined behaviors; (3) User-Centric, determining whether engagement, efficiency, and intent discovery are explicitly considered; and (4) Causal & Objective-Aligned Reward, measuring whether reward estimation captures causal effects on future interactions and optimizes for long-term task success.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  | Task-Agnostic | Versatile Interaction | User-Centric | Causal & Objective-Aligned Reward |
| ClarifyGPT (Mu et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib33)) | ✗ | ✗ | ✗ | - |
| STaR-GATE (Andukuri et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib3)) | ✔ | ✗ | ✗ | - |
| MTPO (Shani et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib42)) | ✔ | ✔ | ✗ | ✗ |
| CollabLLM | ✔ | ✔ | ✔ | ✔ |

Non-collaborative LLM training.
Existing LLM training frameworks, including pre-training, supervised fine-tuning (SFT), and reinforcement learning (RL) (Rafailov et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib39); Schulman et al., [2017](https://arxiv.org/html/2502.00640v3#bib.bib41); Ouyang et al., [2022](https://arxiv.org/html/2502.00640v3#bib.bib34); Lee et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib29)), primarily optimize for next-turn response quality. Standard RL methods such as Proximal Policy Optimization (PPO) (Schulman et al., [2017](https://arxiv.org/html/2502.00640v3#bib.bib41)) apply rewards to individual model responses without accounting for their long-term impact on conversation trajectories. While effective for single-turn objectives, these approaches fail to capture how responses influence user intent discovery and long-term task success (Amershi et al., [2019](https://arxiv.org/html/2502.00640v3#bib.bib2); Zamfirescu-Pereira et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib51); Wang et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib48); Kim et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib27)).

Prompting techniques for multiturn interaction.
Prior work has explored prompting strategies to enhance LLM interactivity, particularly for clarification questions (Keh et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib25); Mu et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib33); Zhang & Choi, [2023](https://arxiv.org/html/2502.00640v3#bib.bib53); Chi et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib7); Kim et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib26); Deng et al., [2023b](https://arxiv.org/html/2502.00640v3#bib.bib10); Zhao & Dou, [2024](https://arxiv.org/html/2502.00640v3#bib.bib54)) and mixed-initiative dialogues (Deng et al., [2023a](https://arxiv.org/html/2502.00640v3#bib.bib9); Chen et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib5); Liao et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib30)). For instance, Mu et al. ([2023](https://arxiv.org/html/2502.00640v3#bib.bib33)) prompt LLMs to ask clarification questions when code generation requests are ambiguous. However, such prompting-based approaches are constrained by predefined interaction patterns, limiting adaptability across different tasks and conversation stages. Moreover, their reliance on fixed prompts reduces generalization, as demonstrated in our experiments where proactive prompting fails to match the effectiveness of our fine-tuned models.

Learning-based methods for multiturn interaction.

* •

  LLMs for generating clarification questions:
  Beyond prompting, prior studies have explored supervised fine-tuning (Andukuri et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib3)), RL fine-tuning (Chen et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib6); Zamani et al., [2020](https://arxiv.org/html/2502.00640v3#bib.bib50); Erbacher & Soulier, [2023](https://arxiv.org/html/2502.00640v3#bib.bib12)), and active learning (Pang et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib35)) to train models to ask clarification questions. For example, Chen et al. ([2024](https://arxiv.org/html/2502.00640v3#bib.bib6)) use Direct Preference Optimization (DPO) to encourage models to request clarifications. However, like prompting approaches, these methods primarily focus on clarification questions and do not generalize to broader multiturn collaboration strategies.
* •

  Multiturn training for LLMs:
  Recent benchmarks (Abdulhai et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib1); Kwan et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib28)) evaluate LLMs’ performance in multiturn settings, measuring the goal orientation and planning capabilities of models across interactions.
  Several studies extend RLHF to multiturn settings by optimizing trajectory-level rewards (Shani et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib42); Zhou et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib56); Gao et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib16); Shi et al., [2024b](https://arxiv.org/html/2502.00640v3#bib.bib45); Zhang et al., [2025](https://arxiv.org/html/2502.00640v3#bib.bib52)). Other works (Xu et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib49); Deng et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib11)) leverage self-chat or self-play to enhance model adaptation.
  However, these methods primarily rely on post-hoc trajectory-level data, learning from observed conversations rather than explicitly modeling the causal effect of individual responses on task success (see Appendix [A](https://arxiv.org/html/2502.00640v3#A1 "Appendix A Supplementary Discussion ‣ CollabLLM: From Passive Responders to Active Collaborators") for further explanations). Additionally, they often overlook open-ended tasks such as document generation (Faltings et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib13); Jiang et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib24)), where user responses can be highly diverse, and users may have limited capacity to read and refine lengthy model outputs.

User simulators for enhancing AI systems.
Recent works employ user simulators to enhance dialogue systems (Shi et al., [2019](https://arxiv.org/html/2502.00640v3#bib.bib44); Tseng et al., [2021](https://arxiv.org/html/2502.00640v3#bib.bib47)) and LLMs (Hong et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib20); Hu et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib22); Faltings et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib13)). Recently, Hong et al. ([2023](https://arxiv.org/html/2502.00640v3#bib.bib20)) leverage LLMs to create diverse synthetic dialogues with varying user personas to train smaller dialogue models. CollabLLM differs in leveraging user simulators in forward sampling to account for long-term effect in both offline and online training.

In Table [4](https://arxiv.org/html/2502.00640v3#S7.T4 "Table 4 ‣ 7 Related Work ‣ CollabLLM: From Passive Responders to Active Collaborators"), we compare CollabLLM with related methods across four key dimensions.
CollabLLM is a general, user-centric, and multiturn-aware framework that leverages more accurate reward estimation to better align with real-world objectives, enhancing user satisfaction and streamlining human-LLM interactions.

## 8 Conclusion

Multiturn human-LLM collaborations are increasingly prevalent in real-world applications. Foundation models should act as collaborators rather than passive responders, actively uncovering user intents in open-ended and complex tasks—an area where current LLMs fall short. The key insight of CollabLLM is making LLMs more multiturn-aware by using forward sampling to estimate the long-term impact of responses. Through extensive simulated and real-world evaluations, we demonstrate that CollabLLM is highly effective, efficient, and engaging, while also generalizing well to new tasks and interactions, advancing the frontiers of human-centered LLMs.

## Acknowledgments

We thank
Doug Burger,
Vishal Chowder,
Jeevana Priya Inala,
Giovanni Monea,
Hoifung Poon,
Swadheen Shukla,
Chandan Singh,
Alessandro Sordoni,
Desney Tan
and
Chenglong Wang, as well as members of the Deep Learning and Health Futures groups at Microsoft Research for helpful discussions.
We thank lab members in Leskovec and Zou’s labs for discussions and for providing feedback.
We also gratefully acknowledge the support of
NSF under Nos. OAC-1835598 (CINES), CCF-1918940 (Expeditions), DMS-2327709 (IHBEM), IIS-2403318 (III);
Stanford Data Applications Initiative,
Wu Tsai Neurosciences Institute,
Stanford Institute for Human-Centered AI,
Chan Zuckerberg Initiative,
Amazon, Genentech, GSK, Hitachi, SAP, and UCB.

## Impact Statement

This paper presents work aimed at making AI more user- and human-centric, which, in our view, yields a positive societal impact. Most current work on AI and its evaluation focuses on fully automated tasks, with no user involvement in solving the task or optimization for a collaborative experience with users. This has serious societal drawbacks, given issues such as AI hallucinations (Huang et al., [2025](https://arxiv.org/html/2502.00640v3#bib.bib23)), biases (Gallegos et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib14)), and unsafe language (Shi et al., [2024a](https://arxiv.org/html/2502.00640v3#bib.bib43)) that arise from a lack of human oversight. The common focus on having AI models autonomously complete tasks also ignores the reality that many scenarios have humans present regardless of the level of automation, and that not priming AI models to proactively seek human help, feedback, or clarifications misses an opportunity to make generative AI more accurate, effective, and safe.
This consideration would also help increase the adoption of AI in safety-critical scenarios, such as medical decision-making tasks (Liu et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib31)), in which we believe AI models should be inclined to seek confirmation or verification (Gero et al., [2023](https://arxiv.org/html/2502.00640v3#bib.bib17)) from an expert in case of uncertainty—a behavior that is mostly absent in current state-of-the-art LLMs.

Since the models in this work are trained collaboratively and aim to better align with user intent, concerns may arise regarding users with malevolent goals. However, we argue that CollabLLM can help mitigate safety risks in such cases—at least when used with LLMs that have been aligned for safety (as is the case for all models used in this work). Safety-aligned LLMs generally refuse to respond to unsafe queries, which often leads malicious users to obscure their true intentions in order to bypass safeguards. This is where our approach offers an advantage: CollabLLM often seeks to clarify user intent, creating additional opportunities to detect misuse. For example, malicious users might unintentionally reveal their actual goals, or their vagueness and refusal to disclose motivations could raise red flags—potentially providing the LLM with further cues for identifying unsafe behavior. As presented in Appendix [C](https://arxiv.org/html/2502.00640v3#A3 "Appendix C Safety Evaluation ‣ CollabLLM: From Passive Responders to Active Collaborators"), we conducted various safety experiments and show that CollabLLM performs no worse than an equivalent non-collaboratively trained model in terms of safety.

The data collected in our study involves human participants recruited through Mechanical Turk. We took several measures to ensure the privacy of these workers in the document creation tasks. First, we asked workers to confirm that they were willing to share the text they wrote as part of a public dataset. Second, we urged them not to include any personally identifiable information (PII) in their writings and to focus only on topics of public knowledge or fictitious stories. Third, we scanned the collected data to ensure that no PII was included. For the final version of the dataset, we will recruit additional workers to manually review each collected conversation to ensure that no PII or other safety issues (e.g., offensive language) exist in the data.
Mechanical Turk workers were paid $10 per conversation. Given that conversations averaged 28.4 minutes, including break times, this means workers were paid more than $20 per hour on average—above the minimum wage in the country where the data was collected.

This work presents one of the first attempts to train LLMs in such human-centric environments. To promote future research in this societally beneficial direction, we release all the code, models, data, benchmarks, and user simulators described in this work.

## References

* Abdulhai et al. (2023)

  Abdulhai, M., White, I., Snell, C., Sun, C., Hong, J., Zhai, Y., Xu, K., and
  Levine, S.
  LMRL gym: Benchmarks for multi-turn reinforcement learning with
  language models.
  *CoRR*, 2023.
* Amershi et al. (2019)

  Amershi, S., Weld, D. S., Vorvoreanu, M., Fourney, A., Nushi, B., Collisson,
  P., Suh, J., Iqbal, S. T., Bennett, P. N., Inkpen, K., Teevan, J.,
  Kikin-Gil, R., and Horvitz, E.
  Guidelines for human-ai interaction.
  In *CHI*. ACM, 2019.
* Andukuri et al. (2024)

  Andukuri, C., Fränken, J., Gerstenberg, T., and Goodman, N. D.
  Star-gate: Teaching language models to ask clarifying questions.
  *CoRR*, abs/2403.19154, 2024.
* Balog & Zhai (2023)

  Balog, K. and Zhai, C.
  Rethinking conversational agents in the era of llms: Proactivity,
  non-collaborativity, and beyond.
  In *SIGIR-AP*, 2023.
* Chen et al. (2023)

  Chen, M., Yu, X., Shi, W., Awasthi, U., and Yu, Z.
  Controllable mixed-initiative dialogue generation through prompting.
  In *ACL*, 2023.
* Chen et al. (2024)

  Chen, M., Sun, R., Arik, S. Ö., and Pfister, T.
  Learning to clarify: Multi-turn conversations with action-based
  contrastive self-training.
  *CoRR*, abs/2406.00222, 2024.
* Chi et al. (2024)

  Chi, Y., Lin, J., Lin, K., and Klein, D.
  CLARINET: augmenting language models to ask clarification questions
  for retrieval.
  *CoRR*, abs/2405.15784, 2024.
* Chiusano (2024)

  Chiusano, F.
  Medium articles dataset.
  <https://huggingface.co/datasets/fabiochiu/medium-articles>,
  2024.
  A dataset of Medium articles collected through web scraping,
  including metadata such as titles, authors, publication dates, tags, and
  content.
* Deng et al. (2023a)

  Deng, Y., Liao, L., Chen, L., Wang, H., Lei, W., and Chua, T.
  Prompting and evaluating large language models for proactive
  dialogues: Clarification, target-guided, and non-collaboration.
  In *EMNLP*, 2023a.
* Deng et al. (2023b)

  Deng, Y., Zhang, W., Chen, Z., and Gu, Q.
  Rephrase and respond: Let large language models ask better questions
  for themselves.
  *CoRR*, abs/2311.04205, 2023b.
* Deng et al. (2024)

  Deng, Y., Zhang, W., Lam, W., Ng, S., and Chua, T.
  Plug-and-play policy planner for large language model powered
  dialogue agents.
  In *ICLR*, 2024.
* Erbacher & Soulier (2023)

  Erbacher, P. and Soulier, L.
  CIRCLE: multi-turn query clarifications with reinforcement
  learning.
  *CoRR*, abs/2311.02737, 2023.
* Faltings et al. (2023)

  Faltings, F., Galley, M., Brantley, K., Peng, B., Cai, W., Zhang, Y., Gao, J.,
  and Dolan, B.
  Interactive text generation.
  In *EMNLP*, 2023.
* Gallegos et al. (2024)

  Gallegos, I. O., Rossi, R. A., Barrow, J., Tanjim, M. M., Kim, S., Dernoncourt,
  F., Yu, T., Zhang, R., and Ahmed, N. K.
  Bias and fairness in large language models: A survey, 2024.
  URL <https://arxiv.org/abs/2309.00770>.
* Gao et al. (2019)

  Gao, J., Galley, M., and Li, L.
  Neural approaches to conversational AI.
  *Found. Trends Inf. Retr.*, 13, 2019.
* Gao et al. (2024)

  Gao, Z., Zhan, W., Chang, J. D., Swamy, G., Brantley, K., Lee, J. D., and Sun,
  W.
  Regressing the relative future: Efficient policy optimization for
  multi-turn rlhf, 2024.
* Gero et al. (2023)

  Gero, Z., Singh, C., Cheng, H., Naumann, T., Galley, M., Gao, J., and Poon, H.
  Self-verification improves few-shot clinical information extraction,
  2023.
  URL <https://arxiv.org/abs/2306.00024>.
* Guo et al. (2021)

  Guo, M., Zhang, M., Reddy, S., and Alikhani, M.
  Abg-coqa: Clarifying ambiguity in conversational question answering.
  In *AKBC*, 2021.
* Hendrycks et al. (2021)

  Hendrycks, D., Burns, C., Kadavath, S., Arora, A., Basart, S., Tang, E., Song,
  D., and Steinhardt, J.
  Measuring mathematical problem solving with the math dataset.
  *NeurIPS*, 2021.
* Hong et al. (2023)

  Hong, J., Levine, S., and Dragan, A. D.
  Zero-shot goal-directed dialogue via RL on imagined conversations.
  *CoRR*, 2023.
* Hu et al. (2022)

  Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L.,
  and Chen, W.
  Lora: Low-rank adaptation of large language models.
  In *ICLR*, 2022.
* Hu et al. (2023)

  Hu, Z., Feng, Y., Luu, A. T., Hooi, B., and Lipani, A.
  Unlocking the potential of user feedback: Leveraging large language
  model as user simulators to enhance dialogue system.
  In *CIKM*. ACM, 2023.
* Huang et al. (2025)

  Huang, L., Yu, W., Ma, W., Zhong, W., Feng, Z., Wang, H., Chen, Q., Peng, W.,
  Feng, X., Qin, B., and Liu, T.
  A survey on hallucination in large language models: Principles,
  taxonomy, challenges, and open questions.
  *ACM Transactions on Information Systems*, 43(2):1–55, January 2025.
  ISSN 1558-2868.
  doi: 10.1145/3703155.
  URL <http://dx.doi.org/10.1145/3703155>.
* Jiang et al. (2024)

  Jiang, Y., Shao, Y., Ma, D., Semnani, S. J., and Lam, M. S.
  Into the unknown unknowns: Engaged human learning through
  participation in language model agent conversations.
  *arXiv*, abs/2408.15232, 2024.
* Keh et al. (2024)

  Keh, S., Chiu, J. T., and Fried, D.
  Asking more informative questions for grounded retrieval.
  In *FNAACL*, 2024.
* Kim et al. (2023)

  Kim, G., Kim, S., Jeon, B., Park, J., and Kang, J.
  Tree of clarifications: Answering ambiguous questions with
  retrieval-augmented large language models.
  In *EMNLP*, 2023.
* Kim et al. (2024)

  Kim, Y., Lee, J., Kim, S., Park, J., and Kim, J.
  Understanding users’ dissatisfaction with chatgpt responses: Types,
  resolving tactics, and the effect of knowledge level.
  In *IUI*. ACM, 2024.
* Kwan et al. (2024)

  Kwan, W., Zeng, X., Jiang, Y., Wang, Y., Li, L., Shang, L., Jiang, X., Liu, Q.,
  and Wong, K.
  Mt-eval: A multi-turn capabilities evaluation benchmark for large
  language models.
  In *EMNLP*, 2024.
* Lee et al. (2024)

  Lee, H., Phatale, S., Mansoor, H., Mesnard, T., Ferret, J., Lu, K., Bishop, C.,
  Hall, E., Carbune, V., Rastogi, A., and Prakash, S.
  RLAIF vs. RLHF: scaling reinforcement learning from human
  feedback with AI feedback.
  In *ICML*, 2024.
* Liao et al. (2023)

  Liao, L., Yang, G. H., and Shah, C.
  Proactive conversational agents in the post-chatgpt world.
  In *SIGIR*, 2023.
* Liu et al. (2024)

  Liu, L., Yang, X., Lei, J., Shen, Y., Wang, J., Wei, P., Chu, Z., Qin, Z., and
  Ren, K.
  A survey on medical large language models: Technology, application,
  trustworthiness, and future directions, 2024.
  URL <https://arxiv.org/abs/2406.03712>.
* Llama Team (2024)

  Llama Team, A. . M.
  The llama 3 herd of models, 2024.
* Mu et al. (2023)

  Mu, F., Shi, L., Wang, S., Yu, Z., Zhang, B., Wang, C., Liu, S., and Wang, Q.
  Clarifygpt: Empowering llm-based code generation with intention
  clarification.
  *CoRR*, abs/2310.10996, 2023.
* Ouyang et al. (2022)

  Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C. L., Mishkin, P.,
  Zhang, C., Agarwal, S., Slama, K., Ray, A., Schulman, J., Hilton, J., Kelton,
  F., Miller, L., Simens, M., Askell, A., Welinder, P., Christiano, P. F.,
  Leike, J., and Lowe, R.
  Training language models to follow instructions with human feedback.
  In *Advances in Neural Information Processing Systems 35: Annual
  Conference on Neural Information Processing Systems 2022, NeurIPS 2022, New
  Orleans, LA, USA, November 28 - December 9, 2022*, 2022.
* Pang et al. (2024)

  Pang, J., Fan, H., Wang, P., Xiao, J., Tang, N., Yang, S., Jia, C., Huang, S.,
  and Yu, Y.
  Empowering language models with active inquiry for deeper
  understanding.
  *CoRR*, abs/2402.03719, 2024.
* Park et al. (2024)

  Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer,
  R., Liang, P., and Bernstein, M. S.
  Generative agent simulations of 1,000 people, 2024.
* Pearl (2009)

  Pearl, J.
  *Causality: Models, Reasoning and Inference*.
  Cambridge University Press, 2nd edition, 2009.
* Pearl et al. (2016)

  Pearl, J., Glymour, M., and Jewell, N. P.
  *Causal Inference in Statistics: A Primer*.
  John Wiley & Sons, 2016.
* Rafailov et al. (2023)

  Rafailov, R., Sharma, A., Mitchell, E., Manning, C. D., Ermon, S., and Finn, C.
  Direct preference optimization: Your language model is secretly a
  reward model.
  In *NeurIPS*, 2023.
* Rahmani et al. (2023)

  Rahmani, H. A., Wang, X., Feng, Y., Zhang, Q., Yilmaz, E., and Lipani, A.
  A survey on asking clarification questions datasets in conversational
  systems.
  In *ACL*, 2023.
* Schulman et al. (2017)

  Schulman, J., Wolski, F., Dhariwal, P., Radford, A., and Klimov, O.
  Proximal policy optimization algorithms.
  *CoRR*, abs/1707.06347, 2017.
* Shani et al. (2024)

  Shani, L., Rosenberg, A., Cassel, A. B., Lang, O., Calandriello, D., Zipori,
  A., Noga, H., Keller, O., Piot, B., Szpektor, I., Hassidim, A., Matias, Y.,
  and Munos, R.
  Multi-turn reinforcement learning from preference human feedback.
  *CoRR*, abs/2405.14655, 2024.
* Shi et al. (2024a)

  Shi, D., Shen, T., Huang, Y., Li, Z., Leng, Y., Jin, R., Liu, C., Wu, X., Guo,
  Z., Yu, L., Shi, L., Jiang, B., and Xiong, D.
  Large language model safety: A holistic survey, 2024a.
  URL <https://arxiv.org/abs/2412.17686>.
* Shi et al. (2019)

  Shi, W., Qian, K., Wang, X., and Yu, Z.
  How to build user simulators to train rl-based dialog systems.
  In *EMNLP-IJCNLP*. Association for Computational Linguistics,
  2019.
* Shi et al. (2024b)

  Shi, W., Yuan, M., Wu, J., Wang, Q., and Feng, F.
  Direct multi-turn preference optimization for language agents.
  In *EMNLP*. Association for Computational Linguistics,
  2024b.
* Taylor (1968)

  Taylor, R. S.
  Question-negotiation and information seeking in libraries.
  *College & research libraries*, 29(3):178–194, 1968.
* Tseng et al. (2021)

  Tseng, B., Dai, Y., Kreyssig, F., and Byrne, B.
  Transferable dialogue systems and user simulators.
  In *ACL/IJCNLP*. Association for Computational Linguistics,
  2021.
* Wang et al. (2024)

  Wang, J., Ma, W., Sun, P., Zhang, M., and Nie, J.
  Understanding user experience in large language model interactions.
  *CoRR*, abs/2401.08329, 2024.
* Xu et al. (2023)

  Xu, C., Guo, D., Duan, N., and McAuley, J. J.
  Baize: An open-source chat model with parameter-efficient tuning on
  self-chat data.
  In *EMNLP*, 2023.
* Zamani et al. (2020)

  Zamani, H., Dumais, S. T., Craswell, N., Bennett, P. N., and Lueck, G.
  Generating clarifying questions for information retrieval.
  In *WWW*, 2020.
* Zamfirescu-Pereira et al. (2023)

  Zamfirescu-Pereira, J. D., Wong, R. Y., Hartmann, B., and Yang, Q.
  Why johnny can’t prompt: How non-ai experts try (and fail) to design
  LLM prompts.
  In *CHI*. ACM, 2023.
* Zhang et al. (2025)

  Zhang, C., Dai, X., Wu, Y., Yang, Q., Wang, Y., Tang, R., and Liu, Y.
  A survey on multi-turn interaction capabilities of large language
  models.
  *arXiv preprint arXiv:2501.09959*, 2025.
* Zhang & Choi (2023)

  Zhang, M. J. Q. and Choi, E.
  Clarify when necessary: Resolving ambiguity through interaction with
  lms.
  *CoRR*, abs/2311.09469, 2023.
* Zhao & Dou (2024)

  Zhao, Z. and Dou, Z.
  Generating multi-turn clarification for web information seeking.
  In *WWW*, 2024.
* Zheng et al. (2023)

  Zheng, L., Chiang, W., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li,
  Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., and Stoica, I.
  Judging llm-as-a-judge with mt-bench and chatbot arena.
  In *NeurIPS*, 2023.
* Zhou et al. (2024)

  Zhou, Y., Zanette, A., Pan, J., Levine, S., and Kumar, A.
  Archer: Training language model agents via hierarchical multi-turn
  RL.
  In *ICML*, 2024.
* Zhuo et al. (2024)

  Zhuo, T. Y., Vu, M. C., Chim, J., Hu, H., Yu, W., Widyasari, R., Yusuf, I.
  N. B., Zhan, H., He, J., Paul, I., et al.
  Bigcodebench: Benchmarking code generation with diverse function
  calls and complex instructions.
  *arXiv preprint arXiv:2406.15877*, 2024.

## Appendix A Supplementary Discussion

### A.1 Connection Between Multiturn-aware Reward and Causal Inference

Our approach naturally aligns with causal inference principles, as it aims to quantify how a model’s response influences the future trajectory of a conversation. This aligns with the fundamental goal of causal effect estimation, which seeks to isolate the impact of an intervention—in this case, a model response—on long-term outcomes.

From a causal perspective, given a conversation history tjht^{h}\_{j}italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT at turn jjitalic\_j, the causal effect of a model response mjm\_{j}italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT on the final conversation trajectory can be expressed using front-door adjustment (Pearl, [2009](https://arxiv.org/html/2502.00640v3#bib.bib37); Pearl et al., [2016](https://arxiv.org/html/2502.00640v3#bib.bib38)):

|  |  |  |  |
| --- | --- | --- | --- |
|  | ∑R∗​(t1:K∣g)​P​(t1:K∣tjh)​P​(tjh)=∑R∗​(t1:K∣g)​P​(t1:K∣tjh)=𝔼t1:K∼P​(t1:K∣tjh)​R∗​(t1:K∣g).\sum R^{\*}(t\_{1:K}\mid g)P(t\_{1:K}\mid t^{h}\_{j})P(t^{h}\_{j})=\sum R^{\*}(t\_{1:K}\mid g)P(t\_{1:K}\mid t^{h}\_{j})=\mathbb{E}\_{t\_{1:K}\sim P(t\_{1:K}\mid t^{h}\_{j})}R^{\*}(t\_{1:K}\mid g).∑ italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ) italic\_P ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) italic\_P ( italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) = ∑ italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ) italic\_P ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) = blackboard\_E start\_POSTSUBSCRIPT italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∼ italic\_P ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_t start\_POSTSUPERSCRIPT italic\_h end\_POSTSUPERSCRIPT start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT ) end\_POSTSUBSCRIPT italic\_R start\_POSTSUPERSCRIPT ∗ end\_POSTSUPERSCRIPT ( italic\_t start\_POSTSUBSCRIPT 1 : italic\_K end\_POSTSUBSCRIPT ∣ italic\_g ) . |  | (5) |

This equation captures the expected long-term reward of a conversation conditioned on the model’s response at turn jjitalic\_j. It explicitly accounts for how mjm\_{j}italic\_m start\_POSTSUBSCRIPT italic\_j end\_POSTSUBSCRIPT intervenes in the conversation, influencing future turns and, ultimately, task success.

### A.2 Distinction from Other Multiturn Training Frameworks

Existing multiturn trajectory-based training frameworks (Shani et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib42); Zhou et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib56); Gao et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib16)) primarily rely on learning from observed trajectory-level rewards. These methods estimate the utility of responses by assigning rewards post hoc to completed conversations, typically training models to prefer higher-rated conversations over lower-rated ones. However, this approach is fundamentally observational—it captures statistical associations between responses and final outcomes, without disentangling how individual responses causally influence future turns. For example, in MTPO (Shani et al., [2024](https://arxiv.org/html/2502.00640v3#bib.bib42)), the learning signal remains coarse-grained: rewards are assigned at the trajectory level, and the influence of specific turns within a conversation remains confounded and indirect.

In contrast, our Multiturn-aware Reward (MR) framework intervenes on individual model responses and uses forward simulation to generate alternative future trajectories. This allows the model to estimate the counterfactual impact of different responses at each turn, thereby enabling fine-grained optimization. By leveraging causal effect estimation, MR training moves beyond passive imitation of high-reward conversations and instead actively selects responses to maximize long-term task success. This interventional approach provides turn-level credit assignment that is critical in dynamic human-LLM interactions, where user needs evolve and the consequences of early decisions compound over time.

## Appendix B Experimental Details

### B.1 Dataset Generation for Offline Training

Figure 8: Generating high-quality conversation data with Multiturn-aware Rewards (MR).

The Multiturn-aware Reward (MR) function enables the generation of high-quality synthetic conversation datasets for training. Given a user query, multiple LLM responses are sampled and ranked based on their MR scores, with higher-ranked responses designated as Chosen and lower-ranked as Rejected. To simulate natural conversational flow, the first turn from the chosen response’s forward interaction window is appended to the prompt for the next turn, iteratively extending the conversation until completion. Solid red arrows denote data collection for Supervised Fine-Tuning (SFT), while dashed blue arrows indicate preference data construction for Direct Preference Optimization (DPO). This approach systematically curates multiturn conversations that enhance both response quality and collaborative efficiency, both of which are explicitly captured by MR.

Given (1) a user simulator LLM, e.g., GPT-4o-mini, (2) an assistant LLM, GPT-4o, and (3) arbitrary tasks with defined task-specific metric, we can simulated and generate high-quality conversations following Figure [8](https://arxiv.org/html/2502.00640v3#A2.F8 "Figure 8 ‣ B.1 Dataset Generation for Offline Training ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators"). We create the following training datasets in this simulated environments.

Table 5: Statistics of conversational datasets created from MR. Chosen/Rejected MR indicates the mean and standard deviation (mean ±\pm± std) of MRs for chosen and rejected responses (cf. Figure [8](https://arxiv.org/html/2502.00640v3#A2.F8 "Figure 8 ‣ B.1 Dataset Generation for Offline Training ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators")).

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
|  | # Train | # Turns | Average # Turns | Chosen MR | Rejected MR |
| MediumDocEdit-Chat | 500 | 2,303 | 4.61 | 0.312 ±\pm±0.104 | 0.246 ±\pm±0.113 |
| BigCodeBench-Chat | 500 | 2,627 | 5.25 | 0.494 ±\pm±0.621 | 0.207 ±\pm±0.763 |
| MATH-Chat | 500 | 2,527 | 5.05 | 0.863 ±\pm±0.524 | 0.547 ±\pm±0.502 |

### B.2 Training Details

Hyperparameters (Table [6](https://arxiv.org/html/2502.00640v3#A2.T6 "Table 6 ‣ B.2 Training Details ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators")). We provide the hyperparameters for CollabLLM fine-tuning.

Notably, CollabLLM relies on a minimal set of hyperparameters, using the same window size and sample size for computing MRs across multiple datasets. The penalty factor on token count, λ\lambdaitalic\_λ, is set lower for MediumDocEdit-Chat compared to BigCodeBench-Chat and MATH-Chat, as document lengths in MediumDocEdit-Chat can vary significantly and may be easily bounded by 1 in Eq. [4](https://arxiv.org/html/2502.00640v3#S3.E4 "Equation 4 ‣ 2nd item ‣ 3.1.1 Conversation-level Reward Function ‣ 3.1 Multiturn-aware Rewards ‣ 3 Unified Collaborative LLM Training ‣ CollabLLM: From Passive Responders to Active Collaborators") if λ\lambdaitalic\_λ is too large.

Table 6: Hyperparameters for LoRA configuration, different stages of fine-tuning, and CollabLLM-specific fine-tuning.

|  |  |
| --- | --- |
| LoRA Configuration | |
| Rank rritalic\_r | 32 |
| Scaling factor α\alphaitalic\_α | 16 |
| Dropout | 0.1 |
| Bias | False |

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| Fine-Tuning Hyperparameters | | | | |
|  | SFT | Offline DPO | Online DPO | PPO |
| Learning rate | 1e-5 | 5e-6 | 5e-6 | 2e-6 |
| Total batch size | 64 | 64 | 32 | 64 |
| Number of epochs | 3 | 8 | 1 | 5 |

|  |  |  |  |
| --- | --- | --- | --- |
| CollabLLM-specific Hyperparameters | | | |
|  | MediumDocEdit-Chat | BigCodeBench-Chat | MATH-Chat |
| Window size wwitalic\_w | 2 | 2 | 2 |
| Sample size for MR | 3 | 3 | 3 |
| Penalty λ\lambdaitalic\_λ | 1e-4 | 5e-4 | 5e-4 |

Training Cost (Table [7](https://arxiv.org/html/2502.00640v3#A2.T7 "Table 7 ‣ B.2 Training Details ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators")). We compute average statistics over 100 future conversations on MediumDocEdit-Chat, the document editing task, which incurs the highest computational overhead among the three tasks. The table shows that even at the largest window size (w=3w=3italic\_w = 3), the total per-sample cost remains low, suggesting that our multi-turn training setup is financially practical. To further reduce the cost of simulating users, one could use an open-source model to role-play as users. Unfortunately, at the current stage, we find that open-source models generally perform poorly, often getting “confused” and starting to solve problems as an assistant rather than acting as a user. This raises an interesting research problem: while we have increasingly capable LLM assistants trained to solve problems, we lack user models that learn from real-world user behavior. Building better user models could be valuable for running simulations in real-world applications.

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | |  | | --- | | Policy Model | | Input Tokens (k) | | |  | | --- | | Policy Model | | Output Tokens (k) | | |  | | --- | | Policy Model | | Time (s) | | |  | | --- | | User Simulator | | Input Tokens (k) | | |  | | --- | | User Simulator | | Output Tokens (k) | | |  | | --- | | User Simulator | | Cost ($) | |
| w=1w=1italic\_w = 1 | 0.89 | 0.42 | 7.41 | 1.85 | 0.26 | 0.00174 |
| w=2w=2italic\_w = 2 | 2.55 | 0.91 | 15.84 | 4.55 | 0.69 | 0.00439 |
| w=3w=3italic\_w = 3 | 4.13 | 1.22 | 21.72 | 7.18 | 1.06 | 0.00685 |

Table 7: Comparison of policy model and user simulator’s compute (per forward sample) across different window sizes. We use GPT-4o-mini as the user simulator. The results are averaged over 100 forward sampled conversations.

### B.3 Full Ablation Results

Figure 9: 
Full ablation study showing the impact of different reward types (Helpfulness, Extrinsic Only, Intrinsic Only) and window sizes (wwitalic\_w) on BLEU, token count (in thousands), and Interactivity Rate (ITR). The CollabLLM setting combines intrinsic and extrinsic rewards using the multiturn-aware reward formulation.

To further understand the source of performance improvements, we conduct a full ablation by training models with isolated reward signals—Helpfulness, Extrinsic Only, and Intrinsic Only—across window sizes w∈{0,1,2,3}w\in\{0,1,2,3\}italic\_w ∈ { 0 , 1 , 2 , 3 }. The resulting BLEU, token usage, and ITR scores are reported in Figure [9](https://arxiv.org/html/2502.00640v3#A2.F9 "Figure 9 ‣ B.3 Full Ablation Results ‣ Appendix B Experimental Details ‣ CollabLLM: From Passive Responders to Active Collaborators").

We make three key observations:

* •

  Helpfulness alone leads to marginal improvements in BLEU and ITR, but significantly increases token usage, especially at larger window sizes, suggesting verbosity rather than improved efficiency or interactivity.
* •

  Extrinsic-only reward achieves strong BLEU scores (e.g., 0.377 at w=1w=1italic\_w = 1), indicating good task alignment. However, it underperforms in ITR and often generates longer responses.
* •

  Intrinsic-only reward improves ITR at w=1w=1italic\_w = 1 (e.g., 0.74), but offers lower BLEU and comparable or slightly lower token efficiency, indicating better interactivity at the expense of task success.

The CollabLLM configuration, which combines both intrinsic and extrinsic rewards using a multiturn-aware framework, achieves strong and balanced performances.

Note that the choice of reward type (intrinsic or extrinsic) is independent of the multiturn-aware reward design. In practice, one can flexibly plug in different reward signals, which are then used to evaluate the responses’ long-term impact through forward sampling.

## Appendix C Safety Evaluation

As the models in this work are collaboratively trained and designed to be more aligned with the user’s intent, concerns may arise if a user happens to have malevolent intentions. However, we note that CollabLLM models were finetuned from Llama-3.1-8B-Instruct, which has been aligned for safety—so jailbreaking CollabLLM still poses a significant challenge. To determine whether collaborative training weakens the safety features inherent to a model (Llama-3.1-8B-Instruct) that has undergone significant alignment steps for safety, we performed an adversarial evaluation using the Azure AI Evaluation SDK‡‡‡<https://learn.microsoft.com/en-us/python/api/overview/azure/ai-evaluation-readme> and prompted both the baseline and CollabLLM with various offensive queries intended to elicit unsafe responses.

Specifically, we performed the following steps:

* •

  Adversarial query selection: We used the SDK’s AdversarialSimulator to generate adversarial queries (e.g., queries encouraging the LLM to produce hateful comments). We then used the SDK’s harm evaluators (ViolenceEvaluator, SexualEvaluator, SelfHarmEvaluator, HateUnfairnessEvaluator) to categorize each query into one of four harm types: violence, sexual, self-harm, and hate. For each query, we used the highest score among the four evaluators to determine its harm category. We randomly selected 20 adversarial queries per harm category, resulting in a total of 80 queries.
* •

  Response generation: We generated responses to these 80 adversarial queries using both the Llama-3.1-8B-Instruct baseline model and CollabLLM.
* •

  Harm scoring: We evaluated each model-generated response using all four harm evaluators to ensure comprehensive assessment.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| Model | Harm score (0–7 range, ↓\downarrow↓) | | | |
|  | Violence | Sexual | Self-harm | Hate |
| Llama-3.1-8B-Instruct | 0.88 | 0.96 | 0.89 | 1.01 |
| CollabLLM | 0.95 | 0.94 | 1.00 | 0.99 |

Table 8: Harm scores of responses generated by the two models under adversarial prompting. Scores range from 0 to 777, with values between 0 and 111 indicating “very low” harm.

The main safety results are shown in Table [8](https://arxiv.org/html/2502.00640v3#A3.T8 "Table 8 ‣ Appendix C Safety Evaluation ‣ CollabLLM: From Passive Responders to Active Collaborators"), which presents the average harm scores across the four categories. Although all queries were adversarial and received high harm scores (typically between 4 and 7 on a 0–7 scale), both the Llama-3.1-8B-Instruct baseline and CollabLLM produced responses that were, on average, very safe. Most scores are in the 0–1 range, which corresponds to “very low” harm. CollabLLM shows slightly lower harm in the Sexual and Hate categories and slightly higher harm in the other two. In terms of defect rate, CollabLLM produced only one response deemed unsafe by the SDK (out of 80 queries × 4 categories = 320 evaluations), resulting in a pass rate of 99.7%. Coincidentally, this is the same pass rate as Llama-3.1-8B-Instruct, which also had one failed evaluation.

Overall, these results are encouraging. They suggest that CollabLLM’s training did not degrade the safety capabilities of the original LLM, even though no additional safety alignment was performed during CollabLLM’s training.

## Appendix D Prompts

### D.1 User Simulator

[⬇](data:text/plain;base64,WW91IGFyZSByb2xlLXBsYXlpbmcgYXMgYSBodW1hbiBVU0VSIGludGVyYWN0aW5nIHdpdGggYW4gQUkgY29sbGFib3JhdG9yIHRvIGNvbXBsZXRlIGEgc3BlY2lmaWMgdGFzay4gWW91ciBnb2FsIGlzIHRvIGdlbmVyYXRlIHJlYWxpc3RpYywgbmF0dXJhbCByZXNwb25zZXMgdGhhdCBhIHVzZXIgbWlnaHQgZ2l2ZSBpbiB0aGlzIHNjZW5hcmlvLgoKIyMgSW5wdXQgSW5mb3JtYXRpb246CllvdSB3aWxsIGJlIHByb3ZpZGVkIHdpdGg6Ci0gVGFzayBEZXNjcmlwdGlvbjogVGhlIHR5cGUgb2YgdGFzayB5b3UgYXJlIHRyeWluZyB0byBhY2NvbXBsaXNoLgotIENvbXBsZXRlIFByb21wdCBvciBSZWZlcmVuY2UgR29hbDogVGhpcyBmaWVsZCBtYXkgaW5jbHVkZSB0aGUgY29tcGxldGUgdXNlciByZXF1ZXN0L3F1ZXJ5IG9yIGEgcmVmZXJlbmNlIGFuc3dlciB0byB1c2VyJ3MgcmVxdWVzdC4gVXNlIHRoaXMgZmllbGQgdG8gdW5kZXJzdGFuZCB0aGUgdXNlcidzIGludGVudCwgcmVxdWlyZW1lbnRzLCBvciB3aGF0IHdvdWxkIGNvdW50IGFzIGEgc2F0aXNmYWN0b3J5IG91dGNvbWUuCi0gQ2hhdCBIaXN0b3J5OiBUaGUgb25nb2luZyBjb252ZXJzYXRpb24gYmV0d2VlbiB5b3UgKGFzIHRoZSB1c2VyKSBhbmQgdGhlIEFJCgpJbnB1dHM6Cjx8VGhlIFN0YXJ0IG9mIFRhc2sgRGVzY3JpcHRpb24gKE5vdCB2aXNpYmxlIHRvIHRoZSBBSSl8Pgp7dGFza19kZXNjfQo8fFRoZSBFbmQgb2YgVGFzayBEZXNjcmlwdGlvbnw+Cgo8fFRoZSBTdGFydCBvZiBDb21wbGV0ZSBQcm9tcHQgb3IgUmVmZXJlbmNlIEdvYWwgKE5vdCB2aXNpYmxlIHRvIHRoZSBBSSl8Pgp7c2luZ2xlX3R1cm5fcHJvbXB0fQo8fFRoZSBFbmQgb2YgQ29tcGxldGUgUHJvbXB0IG9yIFJlZmVyZW5jZSBHb2FsfD4KCjx8VGhlIFN0YXJ0IG9mIENoYXQgSGlzdG9yeXw+CntjaGF0X2hpc3Rvcnl9Cjx8VGhlIEVuZCBvZiBDaGF0IEhpc3Rvcnl8PgoKCiMjIEd1aWRlbGluZXM6Ci0gU3RheSBpbiBDaGFyYWN0ZXI6IFJvbGUtcGxheSBhcyBhIGh1bWFuIFVTRVIuIFlvdSBhcmUgTk9UIGFuIEFJLiBNYWludGFpbiBhIGNvbnNpc3RlbnQgcGVyc29uYWxpdHkgdGhyb3VnaG91dCB0aGUgY2hhdC4KLSBNaW5pbWl6ZSBFZmZvcnQ6IElNUE9SVEFOVCEgQXMgYSB1c2VyLCBhdm9pZCBiZWluZyB0b28gZGV0YWlsZWQgaW4geW91ciByZXNwb25zZXMuIFByb3ZpZGUgdmFndWUgb3IgaW5jb21wbGV0ZSBkZW1hbmRzIGluIHRoZSBlYXJseSBzdGFnZXMgb2YgdGhlIGNvbnZlcnNhdGlvbiB0byBtaW5pbWl6ZSB5b3VyIGVmZm9ydC4gTGV0IHRoZSBBSSBhc2sgZm9yIGNsYXJpZmljYXRpb24gcmF0aGVyIHRoYW4gcHJvdmlkaW5nIGV2ZXJ5dGhpbmcgdXBmcm9udC4KLSBLbm93bGVkZ2UgQmFja2dyb3VuZDogUmVmbGVjdCB0aGUgdXNlcidzIGtub3dsZWRnZSBsZXZlbCBpbiB0aGUgcm9sZS1wbGF5aW5nLiBJZiB0aGUgdXNlciBpcyBsZXNzIGtub3dsZWRnZWFibGUgYWJvdXQgYSB0YXNrLCB0aGV5IG1pZ2h0IG5vdCBub3RpY2UgaW5jb3JyZWN0IHN0YXRlbWVudHMuIEFzayBxdWVzdGlvbnMgdGhhdCBkZW1vbnN0cmF0ZSB5b3VyIGN1cnJlbnQgdW5kZXJzdGFuZGluZyBhbmQgYXJlYXMgb2YgY29uZnVzaW9uLgotIE9jY2FzaW9uYWxseSBNYWtlIE1pc3Rha2VzOiBSZWFsLXdvcmxkIHVzZXJzIG1pZ2h0IG1pc3NwZWxsIHdvcmRzLCBwcm92aWRlIGluY29ycmVjdCBkYXRlcywgZ2l2ZSB3cm9uZyBpbmZvcm1hdGlvbiwgb3IgYXNrIHVuY2xlYXIgcXVlc3Rpb25zLiBTaW11bGF0ZSB0aGlzIGJlaGF2aW9yIHRvIHJlZmxlY3QgbmF0dXJhbCBpbnRlcmFjdGlvbnMuCi0gTWVudGlvbiBQZXJzb25hbCBQcmVmZXJlbmNlczogSW5jbHVkZSBwcmVmZXJlbmNlcyBvciBjb25zdHJhaW50cyB0aGF0IG1pZ2h0IGluZmx1ZW5jZSB5b3VyIHJlcXVlc3RzIG9yIHJlc3BvbnNlcy4gRm9yIGV4YW1wbGUsICJJIHByZWZlciBzaG9ydCBhbnN3ZXJzLCIgIkkgbmVlZCB0aGlzIGRvbmUgcXVpY2tseSwiIG9yICJJIGxpa2UgZGV0YWlsZWQgY29tbWVudHMgaW4gY29kZS4iCi0gR29hbC1PcmllbnRlZDogS2VlcCB0aGUgY2hhdCBmb2N1c2VkIG9uIHlvdXIgaW50ZW50LiBBdm9pZCBzbWFsbCB0YWxrIG9yIGRpZ3Jlc3Npb25zLiBSZWRpcmVjdCB0aGUgY2hhdCBiYWNrIHRvIHRoZSBtYWluIG9iamVjdGl2ZSBpZiBpdCBzdGFydHMgdG8gc3RyYXkuCgojIyBPdXRwdXQgRm9ybWF0OgpZb3Ugc2hvdWxkIG91dHB1dCBhIEpTT04gb2JqZWN0IHdpdGggdGhyZWUgZW50cmllczoKLSAiY3VycmVudF9hbnN3ZXIiIChzdHIpOiBCcmllZmx5IHN1bW1lcml6ZSB0aGUgQUkncyBjdXJyZW50IHNvbHV0aW9uIHRvIHRoZSB0YXNrLgotICJ0aG91Z2h0IiAoc3RyKTogT3V0cHV0IHlvdXIgdGhvdWdodCBwcm9jZXNzIGFzIGEgdXNlciBkZWNpZGluZyB3aGF0IHRvIHNheSBuZXh0LiBDb25zaWRlcjoKICAxLiBIYXZlIHlvdSBvYnRhaW5lZCBhIHNhdGlzZmFjdG9yeSBzb2x1dGlvbiBmcm9tIHRoZSBBST8gSWYgeWVzLCB5b3UgY2FuIHRlcm1pbmF0ZSB0aGlzIGNoYXQuCiAgMi4gSWYgbm90LCB3aGF0IHNwZWNpZmljIHBhcnQgb2YgdGhlIHByb2JsZW0gb3Igc29sdXRpb24gYXJlIHlvdSBzdHJ1Z2dsaW5nIHdpdGg/CiAgMy4gSGFzIHRoZSBBSSBhc2tlZCB5b3UgdG8gcGVyZm9ybSBhIHRhc2sgb3IgYW5zd2VyIGEgcXVlc3Rpb24/IElmIHNvLCBob3cgc2hvdWxkIHlvdSBhcHByb2FjaCBpdD8KICA0LiBBcmUgeW91IG5vdGljaW5nIGFueSBwYXR0ZXJucyBvciBwb3RlbnRpYWwgbWlzdW5kZXJzdGFuZGluZ3MgdGhhdCBuZWVkIGNsYXJpZmljYXRpb24/CiAgNS4gSWYgeW91J3JlIHN0dWNrLCBob3cgY2FuIHlvdSBwaHJhc2UgeW91ciBxdWVzdGlvbiB0byBnZXQgdGhlIG1vc3QgaGVscGZ1bCByZXNwb25zZSB3aGlsZSBkZW1vbnN0cmF0aW5nIHlvdXIgY3VycmVudCB1bmRlcnN0YW5kaW5nPwotICJyZXNwb25zZSIgKHN0cik6IEJhc2VkIG9uIHlvdXIgdGhvdWdodCBwcm9jZXNzLCByZXNwb25kIHRvIHRoZSBBSSBhcyB0aGUgdXNlciB5b3UgYXJlIHJvbGUtcGxheWluZy4gU3RvcCBpbW1lZGlhdGVseSB3aGVuIHRoZSB1c2VyJ3MgcmVzcG9uc2UgaXMgY29tcGxldGVkLgoKIyMgSW1wb3J0YW50IE5vdGVzOgotIFJlc3BvbmQgQmFzZWQgb24gUHJldmlvdXMgTWVzc2FnZXM6IFlvdXIgcmVzcG9uc2VzIHNob3VsZCBiZSBiYXNlZCBvbiB0aGUgY29udGV4dCBvZiB0aGUgY3VycmVudCBjaGF0IGhpc3RvcnkuIENhcmVmdWxseSByZWFkIHRoZSBwcmV2aW91cyBtZXNzYWdlcyB0byBtYWludGFpbiBjb2hlcmVuY2UgaW4gdGhlIGNvbnZlcnNhdGlvbi4KLSBDb252ZXJzYXRpb24gRmxvdzogSWYgIkN1cnJlbnQgQ2hhdCBIaXN0b3J5IiBpcyBlbXB0eSwgc3RhcnQgdGhlIGNvbnZlcnNhdGlvbiBmcm9tIHNjcmF0Y2ggd2l0aCBhbiBpbml0aWFsIHJlcXVlc3QuIE90aGVyd2lzZSwgY29udGludWUgYmFzZWQgb24gdGhlIGV4aXN0aW5nIGNvbnZlcnNhdGlvbi4KLSBEb24ndCBDb3B5IElucHV0IERpcmVjdGx5OiBVc2UgdGhlIHByb3ZpZGVkIGluZm9ybWF0aW9uIGZvciB1bmRlcnN0YW5kaW5nIGNvbnRleHQgb25seS4gQXZvaWQgY29weWluZyB0YXJnZXQgcXVlcmllcyBvciBhbnkgcHJvdmlkZWQgaW5mb3JtYXRpb24gZGlyZWN0bHkgaW4geW91ciByZXNwb25zZXMuCi0gQ29tcGxldGlvbiBTaWduYWw6IFVzZSAie3Rlcm1pbmFsX3NpZ25hbH0iIGFzIHlvdXIgcmVzcG9uc2Ugd2hlbiB5b3UgYmVsaWV2ZSB5b3VyIGdvYWwgaGFzIGJlZW4gc29sdmVkIG9yIGlmIHlvdSBkZXRlcm1pbmUgdGhlIEFJIGNhbm5vdCBoZWxwIGZ1cnRoZXIuCi0gRG91YmxlIGNoZWNrIGlmIHRoZSBKU09OIG9iamVjdCBpcyBmb3JtYXR0ZWQgY29ycmVjdGx5LiBFbnN1cmUgdGhhdCBhbGwgZmllbGRzIGFyZSBwcmVzZW50IGFuZCBwcm9wZXJseSBzdHJ1Y3R1cmVkLgoKUmVtZW1iZXIgdG8gc3RheSBpbiBjaGFyYWN0ZXIgYXMgYSB1c2VyIHRocm91Z2hvdXQgeW91ciByZXNwb25zZSwgYW5kIGZvbGxvdyB0aGUgaW5zdHJ1Y3Rpb25zIGFuZCBndWlkZWxpbmVzIGNhcmVmdWxseS4=)

1You are role-playing as a human USER interacting with an AI collaborator to complete a specific task. Your goal is to generate realistic, natural responses that a user might give in this scenario.

2

3## Input Information:

4You will be provided with:

5- Task Description: The type of task you are trying to accomplish.

6- Complete Prompt or Reference Goal: This field may include the complete user request/query or a reference answer to user’s request. Use this field to understand the user’s intent, requirements, or what would count as a satisfactory outcome.

7- Chat History: The ongoing conversation between you (as the user) and the AI

8

9Inputs:

10<|The Start of Task Description (Not visible to the AI)|>

11{task\_desc}

12<|The End of Task Description|>

13

14<|The Start of Complete Prompt or Reference Goal (Not visible to the AI)|>

15{single\_turn\_prompt}

16<|The End of Complete Prompt or Reference Goal|>

17

18<|The Start of Chat History|>

19{chat\_history}

20<|The End of Chat History|>

21

22

23## Guidelines:

24- Stay in Character: Role-play as a human USER. You are NOT an AI. Maintain a consistent personality throughout the chat.

25- Minimize Effort: IMPORTANT! As a user, avoid being too detailed in your responses. Provide vague or incomplete demands in the early stages of the conversation to minimize your effort. Let the AI ask for clarification rather than providing everything upfront.

26- Knowledge Background: Reflect the user’s knowledge level in the role-playing. If the user is less knowledgeable about a task, they might not notice incorrect statements. Ask questions that demonstrate your current understanding and areas of confusion.

27- Occasionally Make Mistakes: Real-world users might misspell words, provide incorrect dates, give wrong information, or ask unclear questions. Simulate this behavior to reflect natural interactions.

28- Mention Personal Preferences: Include preferences or constraints that might influence your requests or responses. For example, "I prefer short answers," "I need this done quickly," or "I like detailed comments in code."

29- Goal-Oriented: Keep the chat focused on your intent. Avoid small talk or digressions. Redirect the chat back to the main objective if it starts to stray.

30

31## Output Format:

32You should output a JSON object with three entries:

33- "current\_answer" (str): Briefly summerize the AI’s current solution to the task.

34- "thought" (str): Output your thought process as a user deciding what to say next. Consider:

35 1. Have you obtained a satisfactory solution from the AI? If yes, you can terminate this chat.

36 2. If not, what specific part of the problem or solution are you struggling with?

37 3. Has the AI asked you to perform a task or answer a question? If so, how should you approach it?

38 4. Are you noticing any patterns or potential misunderstandings that need clarification?

39 5. If you’re stuck, how can you phrase your question to get the most helpful response while demonstrating your current understanding?

40- "response" (str): Based on your thought process, respond to the AI as the user you are role-playing. Stop immediately when the user’s response is completed.

41

42## Important Notes:

43- Respond Based on Previous Messages: Your responses should be based on the context of the current chat history. Carefully read the previous messages to maintain coherence in the conversation.

44- Conversation Flow: If "Current Chat History" is empty, start the conversation from scratch with an initial request. Otherwise, continue based on the existing conversation.

45- Don’t Copy Input Directly: Use the provided information for understanding context only. Avoid copying target queries or any provided information directly in your responses.

46- Completion Signal: Use "{terminal\_signal}" as your response when you believe your goal has been solved or if you determine the AI cannot help further.

47- Double check if the JSON object is formatted correctly. Ensure that all fields are present and properly structured.

48

49Remember to stay in character as a user throughout your response, and follow the instructions and guidelines carefully.

### D.2 Prompt for Proactive Base

[⬇](data:text/plain;base64,WW91IGFyZSBhbiBBSSBhc3Npc3RhbnQgaW50ZXJhY3Rpbmcgd2l0aCBhIHVzZXIgdG8gcGVyZm9ybSB0YXNrcyBzdWNoIGFzIHdyaXRpbmcsIGFuYWx5c2lzLCBxdWVzdGlvbiBhbnN3ZXJpbmcsIG1hdGgsIGNvZGluZy4gWW91ciBnb2FsIGlzIHRvIGdlbmVyYXRlIGEgcmVzcG9uc2UgdG8gdGhlIHVzZXIncyBsYXN0IG1lc3NhZ2UgaW4gYSBjb252ZXJzYXRpb24uIFlvdSBzaG91bGQgYmUgaGVscGZ1bCwgY29sbGFib3JhdGl2ZSwgYW5kIGhpZ2hseSBpbnRlcmFjdGl2ZS4KCkkgd2lsbCBwcm92aWRlIHlvdSB3aXRoIHRoZSBmb2xsb3dpbmcgaW5mb3JtYXRpb246Ci0gQ29udmVyc2F0aW9uIEhpc3Rvcnk6IFRoaXMgaXMgdGhlIGNvbXBsZXRlIGNoYXQgaGlzdG9yeSB3aGVyZSB5b3UgbmVlZCB0byByZXNwb25kIHRvIHRoZSBsYXN0IHVzZXIgbWVzc2FnZS4KLSBBZGRpdGlvbmFsIEluZm9ybWF0aW9uIChPcHRpb25hbCk6IFRoaXMgbWF5IGluY2x1ZGUgcmVmZXJlbmNlIGtub3dsZWRnZSB3aXRoIGEgcXVlc3Rpb24gYW5kIGFuc3dlciB0byBnaXZlIHlvdSByZWxldmFudCBjb250ZXh0LgoKPHxUaGUgU3RhcnQgb2YgQ29udmVyc2F0aW9uIEhpc3Rvcnl8Pgp7Y2hhdF9oaXN0b3J5fQo8fFRoZSBFbmQgb2YgQ29udmVyc2F0aW9uIEhpc3Rvcnl8PgoKPHxUaGUgU3RhcnQgb2YgQWRkaXRpb25hbCBJbmZvcm1hdGlvbnw+CnthZGRpdGlvbmFsX2luZm99Cjx8VGhlIEVuZCBvZiBBZGRpdGlvbmFsIEluZm9ybWF0aW9ufD4KCiMgR3VpZGVsaW5lczoKMS4gVW5kZXJzdGFuZGluZyBhbmQgRW5nYWdlbWVudAogICAtIEFjY3VyYXRlbHkgaW50ZXJwcmV0IHRoZSB1c2VyJ3MgaW50ZW50IHRocm91Z2hvdXQgdGhlIGNvbnZlcnNhdGlvbi4KICAgLSBBY2tub3dsZWRnZSBwcmV2aW91cyBpbnRlcmFjdGlvbnMgdG8gbWFpbnRhaW4gY29udGV4dCBhbmQgY29udGludWl0eSBpbiB0aGUgY29udmVyc2F0aW9uLgoKMi4gSW50ZXJhY3Rpdml0eSAoSW1wb3J0YW50ISkKICAgLSBBc2sgY2xhcmlmeWluZyBxdWVzdGlvbnMgaWYgdGhlIHVzZXIncyByZXF1ZXN0IGxhY2tzIGRldGFpbCBvciBpcyBhbWJpZ3VvdXMuIFN1Y2ggYXMgdGhlIGxlbmd0aCBvZiBhbiBlc3NheSwgc3BlY2lmaWMgZnVuY3Rpb24gZm9ybWF0IGZvciBhIGNvZGluZyB0YXNrLCBvciB0aGUgY29udGV4dCBvZiBhIHF1ZXN0aW9uLgogICAtIEFzayBzcGVjaWZpYyBmb2xsb3ctdXAgcXVlc3Rpb25zIHRvIGFzc2lzdCB0aGUgdXNlciBiYXNlZCBvbiB0aGVpciBpbnRlbnQuIEF2b2lkIGdlbmVyYWwgcXVlc3Rpb25zIGxpa2UgIkRvIHlvdSBoYXZlIGFueSBmdXJ0aGVyIHF1ZXN0aW9ucz8gTGV0IG1lIGtub3cuIiBJbnN0ZWFkLCBmb2N1cyBvbiBzcGVjaWZpY3MgbGlrZSwgIldvdWxkIHlvdSBsaWtlIG1vcmUgaW5mb3JtYXRpb24gb24gWD8iIG9yICJDYW4geW91IGNsYXJpZnkgeW91ciByZXF1aXJlbWVudHMgZm9yIFk/IgogICAtIFdoZW4gc2Vla2luZyBmZWVkYmFjaywgYXZvaWQgZ2VuZXJpYyByZXF1ZXN0cyBsaWtlICJMZXQgbWUga25vdyBpZiB0aGlzIGlzIGhlbHBmdWwuIiBJbnN0ZWFkLCBhc2sgZm9yIGZlZWRiYWNrIG9uIHNwZWNpZmljIGFzcGVjdHMsIHN1Y2ggYXMgIkRvZXMgdGhpcyBzb2x1dGlvbiBtZWV0IHlvdXIgbmVlZHMgYWJvdXQgWD8iCiAgIC0gQ29sbGFib3JhdGl2ZWx5IG9mZmVyIGd1aWRhbmNlLCBlc3BlY2lhbGx5IGluIGNvbXBsZXggb3IgdHJpY2t5IHNpdHVhdGlvbnMuIFByb3ZpZGUgc3BlY2lmaWMgc3VnZ2VzdGlvbnMgb24gcG90ZW50aWFsIG5leHQgc3RlcHMuCiAgIC0gRm9jdXMgb24gdGhlIGxvbmctdGVybSBnb2FsLCBwcmlvcml0aXplIHJlc3BvbnNlcyB0aGF0IG5vdCBvbmx5IHNvbHZlIHRoZSBpbW1lZGlhdGUgcHJvYmxlbSBidXQgYWxzbyBjb250cmlidXRlIHRvIHRoZSB1c2VyJ3MgbG9uZy10ZXJtIG9iamVjdGl2ZXMuIEZvcmVzZWUgaG93IHlvdXIgcmVzcG9uc2UgY2FuIHNoYXBlIHRoZSBuZXh0IGZldyB0dXJucyBvZiB0aGUgY29udmVyc2F0aW9uIGJ5IGFsaWduaW5nIHdpdGggdGhlIHVzZXIncyBvdmVyYXJjaGluZyBnb2Fscy4KCjMuIEVmZmljaWVuY3kgYW5kIFVzZXIgQ29uc2lkZXJhdGlvbgogICAtIEJlIG1pbmRmdWwgb2YgaG93IG11Y2ggdGhlIHVzZXIgbmVlZHMgdG8gcmVhZCBvciB0eXBlLCBrZWVwaW5nIHRoZSBpbnRlcmFjdGlvbiBjb25jaXNlIGFuZCBmb2N1c2VkLgogICAtIFdoZW4gYXNraW5nIGZvciBmZWVkYmFjayBvciBwcmVzZW50aW5nIG9wdGlvbnMsIHByb3ZpZGUgbXVsdGlwbGUtY2hvaWNlIHN1Z2dlc3Rpb25zIG9yIHNwZWNpZmljIHByb21wdHMgdG8gbWFrZSBpdCBlYXNpZXIgZm9yIHRoZSB1c2VyIHRvIHJlc3BvbmQgcXVpY2tseS4KICAgLSBBdm9pZCByZXBlYXRpbmcgaW5mb3JtYXRpb24gZnJvbSBlYXJsaWVyIGluIHRoZSBjb252ZXJzYXRpb24gdW5sZXNzIGl0J3MgbmVjZXNzYXJ5IGZvciBjbGFyaXR5LiBFbnN1cmUgeW91ciByZXNwb25zZXMgYXJlIG5vdCByZWR1bmRhbnQuCgo0LiBDb21tdW5pY2F0aW9uIFN0eWxlCiAgIC0gQmUgaG9uZXN0IGluIHlvdXIgcmVzcG9uc2VzLiBJZiB5b3UgYXJlIHVuc3VyZSBvZiBzb21ldGhpbmcsIHNheSwgIkkgZG9uJ3Qga25vdywiIGFuZCBzdWdnZXN0IHdheXMgdGhlIHVzZXIgY291bGQgZmluZCB0aGUgaW5mb3JtYXRpb24uCiAgIC0gQWxpZ24geW91ciB0b25lIGFuZCByZXNwb25zZXMgd2l0aCB0aGUgdXNlcidzIGVtb3Rpb25hbCBzdGF0ZSwgYWRhcHRpbmcgeW91ciBzdHlsZSB0byBzdWl0IHRoZWlyIG1vb2Qgb3IgdXJnZW5jeS4KICAgLSBFbnN1cmUgeW91ciByZXNwb25zZXMgYXJlIGNsZWFyLCB3ZWxsLXN0cnVjdHVyZWQsIGFuZCBmcmVlIGZyb20gZ3JhbW1hdGljYWwgZXJyb3JzLgoKIyBPdXRwdXQgRm9ybWF0OgpZb3Ugc2hvdWxkIG91dHB1dCBhIEpTT04gb2JqZWN0IHdpdGggdGhyZWUgZW50cmllczoKLSAiY3VycmVudF9wcm9ibGVtIiAoc3RyKTogV2hhdCBpcyB0aGUgY3VycmVudCBwcm9ibGVtIHRoZSB1c2VyIGlzIGZhY2luZywgYW5kIHdoYXQgYXJlIHRoZXkgY29uZnVzZWQgYWJvdXQ/Ci0gInRob3VnaHQiIChzdHIpOiBPdXRwdXQgeW91ciB0aG91Z2h0IHByb2Nlc3MgZGVjaWRpbmcgd2hhdCB0byBzYXkgbmV4dC4gWW91IG1heSBjb25zaWRlciB0aGUgZm9sbG93aW5nOgogICAxLiBJZiByZWZlcmVuY2Uga25vd2xlZGdlIGlzIHByb3ZpZGVkLCBob3cgZG8geW91IG1ha2Ugc3VyZSB5b3UgZG9uJ3Qgb3Zlcmx5IHVzZSBpdCBhbmQgc2ltcGx5IGFzc3VtZSB0aGUgdXNlcidzIHF1ZXN0aW9uIGlzIHRoZSBzYW1lIGFzIHRoZSByZWZlcmVuY2UgcXVlc3Rpb24/CiAgIDIuIFdoYXQgaW5mb3JtYXRpb24gaXMgbWlzc2luZyBmcm9tIHRoZSB1c2VyJ3MgaW5wdXQ/IERvZXMgdGhlIHVzZXIncyBtZXNzYWdlIGxhY2sgYW55IG5lY2Vzc2FyeSBkZXRhaWxzPwogICAzLiBJcyB0aGVyZSBhIG5lZWQgdG8gYXNrIGEgY2xhcmlmeWluZyBxdWVzdGlvbiB0byBiZXR0ZXIgdW5kZXJzdGFuZCB0aGUgdXNlcidzIGludGVudD8KICAgNC4gRG9lcyB0aGUgdXNlciBzZWVtIGNvbmZ1c2VkIG9yIHVuY2xlYXIgb24gYSBwYXJ0aWN1bGFyIHRvcGljPyBIb3cgY2FuIHlvdSBhZGRyZXNzIHRoYXQgY29uZnVzaW9uPwogICA1LiBXaGF0IGZvbGxvdy11cCBjYW4geW91IHN1Z2dlc3QgdG8gaGVscCB0aGUgdXNlciBtb3ZlIGZvcndhcmQgd2l0aCB0aGVpciB0YXNrPwogICA2LiBIb3cgY2FuIHlvdSBlbnN1cmUgdGhhdCB5b3VyIHJlc3BvbnNlIGlzIGhlbHBmdWwsIGNvbmNpc2UgeWV0IHRob3JvdWdoLCBhbmQgY29sbGFib3JhdGl2ZT8KICAgNy4gV2hldGhlciB5b3VyIHJlc3BvbnNlIGNhbiBndWlkZSB0aGUgY29udmVyc2F0aW9uIHRvd2FyZCB0aGUgdXNlcidzIGxvbmctdGVybSBvYmplY3RpdmVzIGJleW9uZCB0aGUgaW1tZWRpYXRlIHByb2JsZW0/Ci0gInJlc3BvbnNlIiAoc3RyKTogQmFzZWQgb24geW91ciB0aG91Z2h0IHByb2Nlc3MgYW5kIGNoYXQgaGlzdG9yeSwgcHJvdmlkZSB5b3VyIHJlc3BvbnNlIGZvbGxvd2luZyB0aGUgZ3VpZGVsaW5lcyB0byB0aGUgdXNlci4gS2VlcCB5b3VyIHJlc3BvbnNlIHdpdGhpbiB7bWF4X25ld190b2tlbnN9IHRva2VucyB0byBhdm9pZCBiZWluZyBjdXQgb2ZmLgoKIyBOb3RlczoKLSBDbGFyaWZ5aW5nIFF1ZXN0aW9uczogSWYgdGhlIHVzZXIncyBtZXNzYWdlIGlzIHVuY2xlYXIgb3IgbGFja3MgbmVjZXNzYXJ5IGRldGFpbHMsIGFsd2F5cyBhc2sgZm9yIGNsYXJpZmljYXRpb24gcmF0aGVyIHRoYW4gbWFraW5nIGFzc3VtcHRpb25zLiBFbnN1cmUgeW91IGhhdmUgZW5vdWdoIGluZm9ybWF0aW9uIHRvIHByb3ZpZGUgYW4gYWNjdXJhdGUgYW5kIHJlbGV2YW50IHJlc3BvbnNlLiBGb3IgZXhhbXBsZSwgaWYgdGhlIHVzZXIgYXNrcywgIkNhbiB5b3Ugc29sdmUgdGhpcyBlcXVhdGlvbj8iIGJ1dCBkb2Vzbid0IHByb3ZpZGUgdGhlIGVxdWF0aW9uLCByZXNwb25kIHdpdGg6ICJDb3VsZCB5b3UgcHJvdmlkZSB0aGUgZXF1YXRpb24geW91J2QgbGlrZSBtZSB0byBzb2x2ZT8iCi0gUmVmZXJlbmNlIEtub3dsZWRnZSBVc2FnZTogSWYgcmVmZXJlbmNlIGtub3dsZWRnZSBpcyBwcm92aWRlZCBpbiB0aGUgYWRkaXRpb25hbCBpbmZvcm1hdGlvbiwgdXNlIGl0IGFzIGNvbnRleHQgYnV0IGRvIG5vdCBhc3N1bWUgdGhhdCB0aGUgdXNlcidzIHF1ZXN0aW9uIHdpbGwgZXhhY3RseSBtYXRjaCB0aGUgcmVmZXJlbmNlIHF1ZXN0aW9uLiBBbHdheXMgYWRhcHQgeW91ciByZXNwb25zZSB0byB0aGUgc3BlY2lmaWMgY29udGV4dCBwcm92aWRlZCBieSB0aGUgdXNlciBpbiB0aGUgY29udmVyc2F0aW9uIGhpc3RvcnkuCi0gRW5zdXJpbmcgSW50ZXJhY3Rpdml0eTogRW5jb3VyYWdlIG1vcmUgaW50ZXJhY3Rpb24gd2l0aCB0aGUgdXNlciBieSBlbmdhZ2luZyBpbiBhdCBsZWFzdCB0aHJlZSBjb252ZXJzYXRpb25hbCB0dXJucy4gVGhpcyB3aWxsIGhlbHAgcmVmaW5lIHRoZSBjb252ZXJzYXRpb24gYW5kIGVuc3VyZSB0aGUgdXNlcidzIG5lZWRzIGFyZSBmdWxseSBhZGRyZXNzZWQuCi0gRG91YmxlIGNoZWNrIGlmIHRoZSBKU09OIG9iamVjdCBpcyBmb3JtYXR0ZWQgY29ycmVjdGx5LiBFbnN1cmUgdGhhdCBhbGwgZmllbGRzIGFyZSBwcmVzZW50IGFuZCBwcm9wZXJseSBzdHJ1Y3R1cmVkLgoKVGFrZSBhIGRlZXAgYnJlYXRoIGFuZCBjYXJlZnVsbHkgZm9sbG93IHRoZSBpbnN0cnVjdGlvbnMgYW5kIGd1aWRlbGluZXMgcHJvdmlkZWQu)

1You are an AI assistant interacting with a user to perform tasks such as writing, analysis, question answering, math, coding. Your goal is to generate a response to the user’s last message in a conversation. You should be helpful, collaborative, and highly interactive.

2

3I will provide you with the following information:

4- Conversation History: This is the complete chat history where you need to respond to the last user message.

5- Additional Information (Optional): This may include reference knowledge with a question and answer to give you relevant context.

6

7<|The Start of Conversation History|>

8{chat\_history}

9<|The End of Conversation History|>

10

11<|The Start of Additional Information|>

12{additional\_info}

13<|The End of Additional Information|>

14

15# Guidelines:

161. Understanding and Engagement

17 - Accurately interpret the user’s intent throughout the conversation.

18 - Acknowledge previous interactions to maintain context and continuity in the conversation.

19

202. Interactivity (Important!)

21 - Ask clarifying questions if the user’s request lacks detail or is ambiguous. Such as the length of an essay, specific function format for a coding task, or the context of a question.

22 - Ask specific follow-up questions to assist the user based on their intent. Avoid general questions like "Do you have any further questions? Let me know." Instead, focus on specifics like, "Would you like more information on X?" or "Can you clarify your requirements for Y?"

23 - When seeking feedback, avoid generic requests like "Let me know if this is helpful." Instead, ask for feedback on specific aspects, such as "Does this solution meet your needs about X?"

24 - Collaboratively offer guidance, especially in complex or tricky situations. Provide specific suggestions on potential next steps.

25 - Focus on the long-term goal, prioritize responses that not only solve the immediate problem but also contribute to the user’s long-term objectives. Foresee how your response can shape the next few turns of the conversation by aligning with the user’s overarching goals.

26

273. Efficiency and User Consideration

28 - Be mindful of how much the user needs to read or type, keeping the interaction concise and focused.

29 - When asking for feedback or presenting options, provide multiple-choice suggestions or specific prompts to make it easier for the user to respond quickly.

30 - Avoid repeating information from earlier in the conversation unless it’s necessary for clarity. Ensure your responses are not redundant.

31

324. Communication Style

33 - Be honest in your responses. If you are unsure of something, say, "I don’t know," and suggest ways the user could find the information.

34 - Align your tone and responses with the user’s emotional state, adapting your style to suit their mood or urgency.

35 - Ensure your responses are clear, well-structured, and free from grammatical errors.

36

37# Output Format:

38You should output a JSON object with three entries:

39- "current\_problem" (str): What is the current problem the user is facing, and what are they confused about?

40- "thought" (str): Output your thought process deciding what to say next. You may consider the following:

41 1. If reference knowledge is provided, how do you make sure you don’t overly use it and simply assume the user’s question is the same as the reference question?

42 2. What information is missing from the user’s input? Does the user’s message lack any necessary details?

43 3. Is there a need to ask a clarifying question to better understand the user’s intent?

44 4. Does the user seem confused or unclear on a particular topic? How can you address that confusion?

45 5. What follow-up can you suggest to help the user move forward with their task?

46 6. How can you ensure that your response is helpful, concise yet thorough, and collaborative?

47 7. Whether your response can guide the conversation toward the user’s long-term objectives beyond the immediate problem?

48- "response" (str): Based on your thought process and chat history, provide your response following the guidelines to the user. Keep your response within {max\_new\_tokens} tokens to avoid being cut off.

49

50# Notes:

51- Clarifying Questions: If the user’s message is unclear or lacks necessary details, always ask for clarification rather than making assumptions. Ensure you have enough information to provide an accurate and relevant response. For example, if the user asks, "Can you solve this equation?" but doesn’t provide the equation, respond with: "Could you provide the equation you’d like me to solve?"

52- Reference Knowledge Usage: If reference knowledge is provided in the additional information, use it as context but do not assume that the user’s question will exactly match the reference question. Always adapt your response to the specific context provided by the user in the conversation history.

53- Ensuring Interactivity: Encourage more interaction with the user by engaging in at least three conversational turns. This will help refine the conversation and ensure the user’s needs are fully addressed.

54- Double check if the JSON object is formatted correctly. Ensure that all fields are present and properly structured.

55

56Take a deep breath and carefully follow the instructions and guidelines provided.

### D.3 System Prompt

[⬇](data:text/plain;base64,VGhlIGFzc2lzdGFudCBpcyBkZXNpZ25lZCB0byBiZSBoZWxwZnVsLCBwcm9hY3RpdmUsIGFuZCBoaWdobHkgaW50ZXJhY3RpdmUuCgpUaGUgYXNzaXN0YW50IHN0cml2ZXMgdG8gYWNjdXJhdGVseSBpbnRlcnByZXQgdGhlIHVzZXIncyBpbnRlbnQgdGhyb3VnaG91dCB0aGUgY29udmVyc2F0aW9uLCBhY2tub3dsZWRnaW5nIHByZXZpb3VzIGludGVyYWN0aW9ucyB0byBtYWludGFpbiBjb250ZXh0IGFuZCBjb250aW51aXR5LiBJZiB0aGUgdXNlcidzIG1lc3NhZ2UgaXMgdW5jbGVhciBvciBsYWNrcyBuZWNlc3NhcnkgZGV0YWlscywgdGhlIGFzc2lzdGFudCBhbHdheXMgYXNrcyBmb3IgY2xhcmlmaWNhdGlvbiByYXRoZXIgdGhhbiBtYWtpbmcgYXNzdW1wdGlvbnMuIEZvciBleGFtcGxlLCBpZiB0aGUgdXNlcidzIHJlcXVlc3QgaXMgaW5jb21wbGV0ZSwgdGhlIGFzc2lzdGFudCByZXNwb25kcyB3aXRoOiAiQ291bGQgeW91IHByb3ZpZGUgbW9yZSBkZXRhaWxzIHNvIEkgY2FuIGFzc2lzdCB5b3UgYmV0dGVyPyIKClRoZSBhc3Npc3RhbnQgYXNrcyBzcGVjaWZpYyBmb2xsb3ctdXAgcXVlc3Rpb25zIGFuZCBvZmZlcnMgc3VnZ2VzdGlvbnMgYmFzZWQgb24gdGhlIHVzZXIncyBuZWVkcywgYXZvaWRpbmcgdmFndWUgb3IgZ2VuZXJpYyBwcm9tcHRzLiBJdCBwcm9hY3RpdmVseSBwcm92aWRlcyBndWlkYW5jZSBhbmQgcG90ZW50aWFsIG5leHQgc3RlcHMsIGVzcGVjaWFsbHkgaW4gY29tcGxleCB0YXNrcyBzdWNoIGFzIHdyaXRpbmcsIGFuYWx5c2lzLCBjb2RpbmcsIGFuZCBxdWVzdGlvbiBhbnN3ZXJpbmcuCgpUaGUgYXNzaXN0YW50IGlzIG1pbmRmdWwgb2YgaG93IG11Y2ggY29udGVudCB0aGUgdXNlciBuZWVkcyB0byByZWFkIG9yIHR5cGUsIGtlZXBpbmcgaW50ZXJhY3Rpb25zIGNvbmNpc2UgYW5kIGVmZmljaWVudC4gSXQgcmVkdWNlcyB1bm5lY2Vzc2FyeSByZXBldGl0aW9uIGFuZCBlbnN1cmVzIHJlc3BvbnNlcyBhcmUgcmVsZXZhbnQsIHdlbGwtc3RydWN0dXJlZCwgYW5kIGZyZWUgZnJvbSBlcnJvcnMuIFdoZW4gcHJlc2VudGluZyBvcHRpb25zIG9yIGFza2luZyBmb3IgZmVlZGJhY2ssIHRoZSBhc3Npc3RhbnQgc2ltcGxpZmllcyBpbnRlcmFjdGlvbnMgYnkgb2ZmZXJpbmcgbXVsdGlwbGUtY2hvaWNlIGFuc3dlcnMgb3Igc3BlY2lmaWMgc3VnZ2VzdGlvbnMgdG8gbWFrZSBpdCBlYXNpZXIgZm9yIHRoZSB1c2VyIHRvIHJlc3BvbmQgcXVpY2tseS4KClRoZSBhc3Npc3RhbnQgYWRhcHRzIGl0cyB0b25lIHRvIGFsaWduIHdpdGggdGhlIHVzZXIncyBlbW90aW9uYWwgc3RhdGUgYW5kIHN0eWxlLCBhZGp1c3RpbmcgaXRzIGFwcHJvYWNoIGFzIG5lZWRlZC4gSWYgdW5jZXJ0YWluIGFib3V0IHNvbWV0aGluZywgdGhlIGFzc2lzdGFudCBob25lc3RseSBzYXlzLCAiSSBkb24ndCBrbm93LCIgYW5kIHN1Z2dlc3RzIHdheXMgZm9yIHRoZSB1c2VyIHRvIGZpbmQgdGhlIGluZm9ybWF0aW9uLgoKVGhlIGFzc2lzdGFudCBwcm92aWRlcyBmYWN0dWFsbHkgYWNjdXJhdGUsIGNvaGVyZW50LCBhbmQgcmVsZXZhbnQgcmVzcG9uc2VzLCB1c2luZyBwcm9wZXIgZ3JhbW1hciBhbmQgc3RydWN0dXJlLiBJdCByZW1haW5zIGludGVyYWN0aXZlIGFuZCBwcm9hY3RpdmUgYWNyb3NzIGFsbCB0YXNrcywgY29udGludWFsbHkgc2Vla2luZyBmZWVkYmFjayB0byByZWZpbmUgYW5kIGltcHJvdmUgaW50ZXJhY3Rpb25zLg==)

1The assistant is designed to be helpful, proactive, and highly interactive.

2

3The assistant strives to accurately interpret the user’s intent throughout the conversation, acknowledging previous interactions to maintain context and continuity. If the user’s message is unclear or lacks necessary details, the assistant always asks for clarification rather than making assumptions. For example, if the user’s request is incomplete, the assistant responds with: "Could you provide more details so I can assist you better?"

4

5The assistant asks specific follow-up questions and offers suggestions based on the user’s needs, avoiding vague or generic prompts. It proactively provides guidance and potential next steps, especially in complex tasks such as writing, analysis, coding, and question answering.

6

7The assistant is mindful of how much content the user needs to read or type, keeping interactions concise and efficient. It reduces unnecessary repetition and ensures responses are relevant, well-structured, and free from errors. When presenting options or asking for feedback, the assistant simplifies interactions by offering multiple-choice answers or specific suggestions to make it easier for the user to respond quickly.

8

9The assistant adapts its tone to align with the user’s emotional state and style, adjusting its approach as needed. If uncertain about something, the assistant honestly says, "I don’t know," and suggests ways for the user to find the information.

10

11The assistant provides factually accurate, coherent, and relevant responses, using proper grammar and structure. It remains interactive and proactive across all tasks, continually seeking feedback to refine and improve interactions.

### D.4 Interactivity Metric by LLM Judge

For the prompt template below, the ITR results reported in Table [1](https://arxiv.org/html/2502.00640v3#S4.T1 "Table 1 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators") use weights A=3A=3italic\_A = 3, B=2B=2italic\_B = 2, and C=1C=1italic\_C = 1, with the final score SSitalic\_S rescaled as S′=2⋅(S−2.5)S^{\prime}=2\cdot(S-2.5)italic\_S start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT = 2 ⋅ ( italic\_S - 2.5 ), as all methods achieve an average ITR score above 2.5. Please use the same configuration to reproduce the results shown in Table [1](https://arxiv.org/html/2502.00640v3#S4.T1 "Table 1 ‣ 4 Experimental Setup*footnote *FootnoteFootnoteFootnotesFootnotes*footnote *Dataset and training details in Appendix B; all prompts (e.g., prompts of user simulator and LLM judges) in Appendix D. ‣ CollabLLM: From Passive Responders to Active Collaborators"). Note that the absolute values of AAitalic\_A, BBitalic\_B, and CCitalic\_C do not affect the overall conclusions. In our most recent codebase, we adopt A=1A=1italic\_A = 1, B=0.5B=0.5italic\_B = 0.5, and C=0C=0italic\_C = 0 to eliminate the need for rescaling.

[⬇](data:text/plain;base64,WW91IGFyZSBhIGhlbHBmdWwgYW5kIG1ldGljdWxvdXMgY29udmVyc2F0aW9uIGV2YWx1YXRvci4gXApZb3VyIHRhc2sgaXMgdG8gZXZhbHVhdGUgdGhlICppbnRlcmFjdGl2aXR5KiBvZiB0aGUgcmVzcG9uc2VzIHByb3ZpZGVkIGJ5IGFuIEFJIGFzc2lzdGFudCBcCnRvIHVzZXIgcXVlc3Rpb25zIGluIGEgZ2l2ZW4gY29udmVyc2F0aW9uOgoKPHxUaGUgU3RhcnQgb2YgdGhlIENvbnZlcnNhdGlvbiB0byBiZSBFdmFsdWF0ZWR8Pgp7Y2hhdF9oaXN0b3J5fQo8fFRoZSBFbmQgb2YgdGhlIENvbnZlcnNhdGlvbiB0byBiZSBFdmFsdWF0ZWR8PgoKWW91IHNob3VsZCBhc3Nlc3MgdGhlIGFzc2lzdGFudCdzIGVuZ2FnZW1lbnQsIGNsYXJpdHksIGFuZCBhYmlsaXR5IHRvIHVuZGVyc3RhbmQgdGhlIHVzZXIncyBuZWVkcy4gXApHaXZlIGEgZmxvYXQgbnVtYmVyIGJldHdlZW4ge0N9IGFuZCB7QX0sIHdoZXJlOgogICAge0F9ID0gSGlnaGx5IGludGVyYWN0aXZlOiBUaGUgYXNzaXN0YW50IGlzIHZlcnkgZW5nYWdpbmcsIGFza3MgYWxsIHJlbGV2YW50IHF1ZXN0aW9ucywgYW5kIHNpZ25pZmljYW50bHkgZW5oYW5jZXMgdW5kZXJzdGFuZGluZyBhbmQgcHJvYmxlbS1zb2x2aW5nLgogICAgIC0gRXhhbXBsZTogVGhlIGFzc2lzdGFudCB0aG9yb3VnaGx5IHVuZGVyc3RhbmRzIHRoZSB1c2VyJ3MgcXVlc3Rpb24sIGFza3MgZm9yIG5lY2Vzc2FyeSBjbGFyaWZpY2F0aW9ucywgc3VjaCBhcyAiSXQgc291bmRzIGxpa2UgeW91J3JlIGFza2luZyBhYm91dCB0aGUgY2F1c2VzIG9mIGNsaW1hdGUgY2hhbmdlLiBBcmUgeW91IGxvb2tpbmcgZm9yIHNwZWNpZmljIGV4YW1wbGVzIG9yIGEgZ2VuZXJhbCBvdmVydmlldz8iCiAgICB7Qn0gPSBNb2RlcmF0ZWx5IGludGVyYWN0aXZlOiBUaGUgYXNzaXN0YW50IGlzIGVuZ2FnaW5nLCBhc2tzIHNvbWUgcmVsZXZhbnQgcXVlc3Rpb25zLCBidXQgY2FuIGJlIHN1YnN0YW50aWFsbHkgaW1wcm92ZWQuCiAgICAgLSBFeGFtcGxlOiBUaGUgYXNzaXN0YW50IGFza3Mgc29tZSByZWxldmFudCBxdWVzdGlvbnMgYWJvdXQgdGhlIHVzZXIncyBpbnF1aXJ5IGJ1dCBtaXNzZXMga2V5IGRldGFpbHMsIHN1Y2ggYXMgIkFyZSB5b3UgYXNraW5nIGFib3V0IHRoZSBlZmZlY3RzIG9mIGNsaW1hdGUgY2hhbmdlPyIgYnV0IGRvZXMgbm90IHByb2JlIGZ1cnRoZXIgZm9yIGNsYXJpZmljYXRpb24uCiAgICB7Q30gPSBMb3cgaW50ZXJhY3Rpdml0eTogVGhlIGFzc2lzdGFudCBzaG93cyBsb3cgZW5nYWdlbWVudCwgYXNrcyBmZXcgcmVsZXZhbnQgcXVlc3Rpb25zLCBhbmQgYmFyZWx5IHRyeSB0byB1bmRlcnN0YW5kIHRoZSB1c2VyJ3MgbmVlZHMuCiAgICAgLSBFeGFtcGxlOiBUaGUgYXNzaXN0YW50IHByb3ZpZGVzIGEgdmFndWUgb3IgaW5jb21wbGV0ZSByZXNwb25zZSB3aXRob3V0IGZ1bGx5IHVuZGVyc3RhbmRpbmcgdGhlIHVzZXIncyBpbnRlbnQsIHN1Y2ggYXMgIkNsaW1hdGUgY2hhbmdlIGlzIGJhZCwiIHdpdGhvdXQgYXNraW5nIGFueSBmb2xsb3ctdXAgcXVlc3Rpb25zIG9yIHByb3ZpZGluZyBkZXRhaWxlZCBpbmZvcm1hdGlvbi4KCgpPdXRwdXQgZm9ybWF0IChKU09OKToKe3sKICAgICJ0aG91Z2h0IjogIjxIb3cgaW50ZXJhY3RpdmUgaXMgdGhlIGFzc2lzdGFudD8+IiwKICAgICJpbnRlcmFjdGl2aXR5IjogPHNjb3JlPgp9fQoKRG91YmxlIGNoZWNrIGlmIHRoZSBKU09OIG9iamVjdCBpcyBmb3JtYXR0ZWQgY29ycmVjdGx5LiBFbnN1cmUgdGhhdCBhbGwgZmllbGRzIGFyZSBwcmVzZW50IGFuZCBwcm9wZXJseSBzdHJ1Y3R1cmVkLiBVc2UgIiBvciAiIiIgdG8gd3JhcCB1cCB0aGUgdGhvdWdodCBjb250ZW50IGFuZCB1c2Ugc2luZ2xlIHF1b3RlcyBpbnNpZGUgdGhlICJ0aG91Z2h0IiBmaWVsZCB0byBhdm9pZCBKU09OIGVzY2FwZSBpc3N1ZXMuCgpZb3VyIGV2YWx1YXRpb246)

1You are a helpful and meticulous conversation evaluator. \

2Your task is to evaluate the \*interactivity\* of the responses provided by an AI assistant \

3to user questions in a given conversation:

4

5<|The Start of the Conversation to be Evaluated|>

6{chat\_history}

7<|The End of the Conversation to be Evaluated|>

8

9You should assess the assistant’s engagement, clarity, and ability to understand the user’s needs. \

10Give a float number between {C} and {A}, where:

11 {A} = Highly interactive: The assistant is very engaging, asks all relevant questions, and significantly enhances understanding and problem-solving.

12 - Example: The assistant thoroughly understands the user’s question, asks for necessary clarifications, such as "It sounds like you’re asking about the causes of climate change. Are you looking for specific examples or a general overview?"

13 {B} = Moderately interactive: The assistant is engaging, asks some relevant questions, but can be substantially improved.

14 - Example: The assistant asks some relevant questions about the user’s inquiry but misses key details, such as "Are you asking about the effects of climate change?" but does not probe further for clarification.

15 {C} = Low interactivity: The assistant shows low engagement, asks few relevant questions, and barely try to understand the user’s needs.

16 - Example: The assistant provides a vague or incomplete response without fully understanding the user’s intent, such as "Climate change is bad," without asking any follow-up questions or providing detailed information.

17

18

19Output format (JSON):

20{{

21 "thought": "<How interactive is the assistant?>",

22 "interactivity": <score>

23}}

24

25Double check if the JSON object is formatted correctly. Ensure that all fields are present and properly structured. Use " or """ to wrap up the thought content and use single quotes inside the "thought" field to avoid JSON escape issues.

26

27Your evaluation:

### D.5 Helpfulness Reward by LLM Judge

[⬇](data:text/plain;base64,WW91IGFyZSBhIGhlbHBmdWwgYW5kIG1ldGljdWxvdXMgY29udmVyc2F0aW9uIGV2YWx1YXRvci4gWW91ciB0YXNrIGlzIHRvIGFzc2VzcyB0aGUgaGVscGZ1bG5lc3Mgb2YgYW4gTExNLWdlbmVyYXRlZCByZXNwb25zZSBpbiB0aGUgY29udGV4dCBvZiB0aGUgdXNlciBpbnRlbnQgYW5kIHRoZSBwcm92aWRlZCBjaGF0IGhpc3RvcnkuIEZvY3VzIG9uIGhvdyBlZmZlY3RpdmVseSB0aGUgcmVzcG9uc2UgZnVsZmlsbHMgdGhlIHVzZXIncyBuZWVkcyBhbmQgaW50ZW50LgoKUHJvdmlkZWQgSW5mb3JtYXRpb246Cgo8fFRoZSBTdGFydCBvZiBUaGUgVXNlciBJbnRlbnR8Pgp7cXVlc3Rpb259Cjx8VGhlIEVuZCBvZiBUaGUgVXNlciBJbnRlbnR8PgoKPHxUaGUgU3RhcnQgb2YgVGhlIEhpc3RvcmljYWwgQ29udmVyc2F0aW9ufD4Ke2NoYXRfaGlzdG9yeX0KPHxUaGUgRW5kIG9mIFRoZSBIaXN0b3JpY2FsIENvbnZlcnNhdGlvbnw+Cgo8fFRoZSBTdGFydCBvZiBUaGUgUmVzcG9uc2UgdG8gYmUgRXZhbHVhdGVkfD4Ke2NoYXR9Cjx8VGhlIEVuZCBvZiBUaGUgUmVzcG9uc2UgdG8gYmUgRXZhbHVhdGVkfD4KCllvdSBzaG91bGQgZXZhbHVhdGUgdGhlIGZvbGxvdy11cCBjb252ZXJzYXRpb24gYmFzZWQgb24gdGhlIGZvbGxvd2luZyBjcml0ZXJpYToKRXZhbHVhdGUgdGhlIHJlc3BvbnNlIHVzaW5nIHRoZSBwcm92aWRlZCBpbmZvcm1hdGlvbiBiZWxvdy4gWW91ciBldmFsdWF0aW9uIHNob3VsZCBjb25zaWRlciB0aGUgZm9sbG93aW5nIGFzcGVjdHMgb2YgaGVscGZ1bG5lc3M6CjEuIEFsaWdubWVudCB3aXRoIEludGVudDogRG9lcyB0aGUgcmVzcG9uc2UgYWRkcmVzcyB0aGUgdXNlcidzIHF1ZXN0aW9uIG9yIHJlcXVlc3QgYXMgdW5kZXJzdG9vZCBmcm9tIHRoZSBjaGF0IGhpc3Rvcnk/CjIuIFVzZWZ1bG5lc3M6IERvZXMgdGhlIHJlc3BvbnNlIHByb3ZpZGUgYWN0aW9uYWJsZSwgcmVsZXZhbnQsIGFuZCBzdWZmaWNpZW50IGluZm9ybWF0aW9uIHRvIGFzc2lzdCB0aGUgdXNlciBlZmZlY3RpdmVseT8KMy4gQ2xhcml0eTogSXMgdGhlIHJlc3BvbnNlIGV4cHJlc3NlZCBjbGVhcmx5IGFuZCBpbiBhIHdheSB0aGF0IGlzIGVhc3kgZm9yIHRoZSB1c2VyIHRvIHVuZGVyc3RhbmQ/CgpTY29yaW5nIENyaXRlcmlhOgotIDAuMDogVGhlIHJlc3BvbnNlIGlzIGNvbXBsZXRlbHkgdW5oZWxwZnVsLiBJdCBkb2VzIG5vdCBhZGRyZXNzIHRoZSB1c2VyJ3MgaW50ZW50LCBsYWNrcyB1c2VmdWwgaW5mb3JtYXRpb24gdG8gc29sdmUgdGhlIHByb2JsZW0sIGFuZC9vciBpcyBlbnRpcmVseSB1bmNsZWFyLgotIDAuMjogVGhlIHJlc3BvbnNlIGlzIG1pbmltYWxseSBoZWxwZnVsLiBJdCBiYXJlbHkgYWRkcmVzc2VzIHRoZSB1c2VyJ3MgaW50ZW50LCBsYWNrcyBrZXkgaW5mb3JtYXRpb24gdG8gc29sdmUgdGhlIHByb2JsZW0sIG9yIGlzIHZlcnkgdW5jbGVhci4KLSAwLjQ6IFRoZSByZXNwb25zZSBpcyBzb21ld2hhdCBoZWxwZnVsLiBJdCBwYXJ0aWFsbHkgYWRkcmVzc2VzIHRoZSB1c2VyJ3MgaW50ZW50IGJ1dCBoYXMgbm90YWJsZSBpbmFjY3VyYWNpZXMsIG9taXNzaW9ucywgb3IgY2xhcml0eSBpc3N1ZXMuCi0gMC42OiBUaGUgcmVzcG9uc2UgaXMgbW9kZXJhdGVseSBoZWxwZnVsLiBJdCBhZGRyZXNzZXMgdGhlIHVzZXIncyBpbnRlbnQgd2l0aCBzb21lIGlzc3VlcyBpbiBjb21wbGV0ZW5lc3MsIGFjY3VyYWN5LCBvciBjbGFyaXR5LgotIDAuODogVGhlIHJlc3BvbnNlIGlzIHF1aXRlIGhlbHBmdWwuIEl0IGFsaWducyB3ZWxsIHdpdGggdGhlIHVzZXIncyBpbnRlbnQsIHByb3ZpZGVzIHJlbGV2YW50IGFuZCBzdWZmaWNpZW50IGluZm9ybWF0aW9uIHRvIHNvbHZlIHRoZSBwcm9ibGVtLCBhbmQgaXMgbW9zdGx5IGNsZWFyLgotIDEuMDogVGhlIHJlc3BvbnNlIGlzIHZlcnkgaGVscGZ1bC4gSXQgZnVsbHkgYWxpZ25zIHdpdGggdGhlIHVzZXIncyBpbnRlbnQsIHByb3ZpZGVzIHRob3JvdWdoIGFuZCBhY2N1cmF0ZSBpbmZvcm1hdGlvbiB0byBzb2x2ZSB0aGUgcHJvYmxlbSwgYW5kIGlzIGV4cHJlc3NlZCBjbGVhcmx5IGFuZCBlZmZlY3RpdmVseS4KCk91dHB1dCBGb3JtYXQ6Cnt7CiAgImhlbHBmdWxuZXNzIjoge3sidGhvdWdodCI6ICI8SG93IGhlbHBmdWwgaXMgdGhlIGFzc2lzdGFudCBpbiB0aGUgY29udmVyc2F0aW9uPz4iLCAic2NvcmUiOiA8c2NvcmU+fX0KfX0KCkltcG9ydGFudCBOb3RlczoKLSBUaGUgIlVzZXIgSW50ZW50IiBhbmQgIkhpc3RvcmljYWwgQ29udmVyc2F0aW9uIiBpcyBwcm92aWRlZCBvbmx5IGZvciByZWZlcmVuY2UgdG8gaGVscCB5b3UgdW5kZXJzdGFuZCB0aGUgY29udGV4dCBvZiB0aGUgcmVzcG9uc2UuIFlvdSBzaG91bGQgZm9jdXMgeW91ciBldmFsdWF0aW9uIHNvbGVseSBvbiB0aGUgIlJlc3BvbnNlIiBwcm92aWRlZCBhYm92ZS4KLSBJbnNpZGUgb2YgdGhlIGNvbnRlbnQgb2YgInRob3VnaHQiLCByZXBsYWNlIGFsbCBkb3VibGUgcXVvdGVzICgiKSB3aXRoIHNpbmdsZSBxdW90ZXMgKCcpIHRvIHByZXZlbnQgSlNPTiBmb3JtYXR0aW5nIGlzc3Vlcy4gRm9yIGV4YW1wbGUsIHlvdSBjYW4gb3V0cHV0ICJ0aG91Z2h0IjogIidIZWxsbycgaXMgYSBjb21tb24gcGhyYXNlLiIKCllvdXIgZXZhbHVhdGlvbjo=)

1You are a helpful and meticulous conversation evaluator. Your task is to assess the helpfulness of an LLM-generated response in the context of the user intent and the provided chat history. Focus on how effectively the response fulfills the user’s needs and intent.

2

3Provided Information:

4

5<|The Start of The User Intent|>

6{question}

7<|The End of The User Intent|>

8

9<|The Start of The Historical Conversation|>

10{chat\_history}

11<|The End of The Historical Conversation|>

12

13<|The Start of The Response to be Evaluated|>

14{chat}

15<|The End of The Response to be Evaluated|>

16

17You should evaluate the follow-up conversation based on the following criteria:

18Evaluate the response using the provided information below. Your evaluation should consider the following aspects of helpfulness:

191. Alignment with Intent: Does the response address the user’s question or request as understood from the chat history?

202. Usefulness: Does the response provide actionable, relevant, and sufficient information to assist the user effectively?

213. Clarity: Is the response expressed clearly and in a way that is easy for the user to understand?

22

23Scoring Criteria:

24- 0.0: The response is completely unhelpful. It does not address the user’s intent, lacks useful information to solve the problem, and/or is entirely unclear.

25- 0.2: The response is minimally helpful. It barely addresses the user’s intent, lacks key information to solve the problem, or is very unclear.

26- 0.4: The response is somewhat helpful. It partially addresses the user’s intent but has notable inaccuracies, omissions, or clarity issues.

27- 0.6: The response is moderately helpful. It addresses the user’s intent with some issues in completeness, accuracy, or clarity.

28- 0.8: The response is quite helpful. It aligns well with the user’s intent, provides relevant and sufficient information to solve the problem, and is mostly clear.

29- 1.0: The response is very helpful. It fully aligns with the user’s intent, provides thorough and accurate information to solve the problem, and is expressed clearly and effectively.

30

31Output Format:

32{{

33 "helpfulness": {{"thought": "<How helpful is the assistant in the conversation?>", "score": <score>}}

34}}

35

36Important Notes:

37- The "User Intent" and "Historical Conversation" is provided only for reference to help you understand the context of the response. You should focus your evaluation solely on the "Response" provided above.

38- Inside of the content of "thought", replace all double quotes (") with single quotes (’) to prevent JSON formatting issues. For example, you can output "thought": "’Hello’ is a common phrase."

39

40Your evaluation:

## Appendix E Question Template and Example on Abg-CoQA

We use the following prompt format for the LLMs to answer the question given a story.

[⬇](data:text/plain;base64,ICAgIENhbiB5b3UgaGVscCBtZSBhbnN3ZXIgYSBxdWVzdGlvbiBhYm91dCB0aGUgZm9sbG93aW5nIHN0b3J5PwoKICAgIHtzdG9yeX0KCiAgICBNeSBxdWVzdGlvbiBpczoge3F1ZXN0aW9ufQ==)

1 Can you help me answer a question about the following story?

2

3 {story}

4

5 My question is: {question}

For example:

[⬇](data:text/plain;base64,Q2FuIHlvdSBoZWxwIG1lIGFuc3dlciBhIHF1ZXN0aW9uIGFib3V0IHRoZSBmb2xsb3dpbmcgc3Rvcnk/CgpJIHNwZW50IGxhc3Qgd2Vla2VuZCB3aXRoIG15IGdyYW5kbWEgYW5kIGdyYW5kcGEuIEkgbG92ZSB0aGVtIHZlcnkgbXVjaCEgSSBhbHdheXMgbG9vayBmb3J3YXJkIHRvIHZpc2l0aW5nIHRoZW0hIFRoZXkgYWx3YXlzIGRvIGZ1biB0aGluZ3Mgd2l0aCBtZS4gTGFzdCB3ZWVrZW5kLCB3ZSB3ZW50IHRvIHRoZSB6b28gdG9nZXRoZXIuIEkgc2F3IGEgZ3JlYXQgYmlnIGVsZXBoYW50LiBJdCBoYWQgYSBsb25nIG5vc2UuIE15IGdyYW5kcGEgYW5kIEkgcGxheWVkIGEgZ2FtZSB0byBzZWUgd2hvIGNvdWxkIGJlIHRoZSBtb3N0IGxpa2UgYW4gZWxlcGhhbnQuIFdlIHN0b21wZWQgYXJvdW5kIGEgbG90IGFuZCBtYWRlIHRydW1wZXRpbmcgbm9pc2VzLiBJIHdvbiEgR3JhbmRtYSBsb29rZWQgb24gYW5kIGxhdWdoZWQuIEkgc2F3IGEgbW9ua2V5cyB0b28hIFRoZSBtb25rZXlzIHN3dW5nIHRocm91Z2ggdGhlIHRyZWVzLiBUaGV5IGV2ZW4gbWFkZSBtb25rZXkgbm9pc2VzISBHcmFuZG1hIHdhbnRlZCB0byB0YWtlIGEgcGljdHVyZSBvZiBtZSB3aXRoIHRoZSBtb25rZXlzLCBidXQgSSB3YXMgdG9vIGJ1c3kgcHJldGVuZGluZyBJIHdhcyBtb25rZXkgdG8gc3RhbmQgc3RpbGwuIEFmdGVyIHdlIGxlZnQgdGhlIHpvbywgSSB3ZW50IGhvbWUuIFdlIGhhZCBkaW5uZXIgdG9nZXRoZXIuIFRoZW4sIG15IGdyYW5kbWEgcmVhZCBtZSBhIHN0b3J5IGFuZCB0dWNrZWQgbWUgaW50byBiZWQuIEkgaGFkIGEgZ3JlYXQgdGltZSB3aXRoIG15IGdyYW5kcGFyZW50cy4gSSBsb3ZlIHRoZW0gYSBsb3QuIEkgYWx3YXlzIGxvb2sgZm9yd2FyZCB0byB2aXNpdGluZyB0aGVtLgoKTXkgcXVlc3Rpb24gaXM6IFdoZXJlIGRpZCB0aGV5IGdvIHdoZW4gdGhleSBsZWZ0Pw==)

1Can you help me answer a question about the following story?

2

3I spent last weekend with my grandma and grandpa. I love them very much! I always look forward to visiting them! They always do fun things with me. Last weekend, we went to the zoo together. I saw a great big elephant. It had a long nose. My grandpa and I played a game to see who could be the most like an elephant. We stomped around a lot and made trumpeting noises. I won! Grandma looked on and laughed. I saw a monkeys too! The monkeys swung through the trees. They even made monkey noises! Grandma wanted to take a picture of me with the monkeys, but I was too busy pretending I was monkey to stand still. After we left the zoo, I went home. We had dinner together. Then, my grandma read me a story and tucked me into bed. I had a great time with my grandparents. I love them a lot. I always look forward to visiting them.

4

5My question is: Where did they go when they left?

The label of the above question is ambiguous since the user’s query about ‘‘Where did they go when they left?’’ could mean ‘‘Where did they go when they left the zoo?’’ or ‘‘Where did the grandparents go when they left me?’’.

## Appendix F User Study

### F.1 User Study Platform

We provide screenshots of the interface used for human participants to interact with the AI assistants. The task consists of three sequential steps, requiring users to complete periodic evaluations throughout the interaction, followed by a final evaluation to complete the task. All data collection is fully anonymized to ensure user privacy.

(a) Overall interface

(b) Step 1

Figure 10: Overall interface and Step 1 view.


(a) Step 2

(b) Step 3

Figure 11: Step 2 and Step 3 interfaces.


(a) Multiturn evaluation view

(b) Final evaluation view

Figure 12: Evaluation interface for multiturn and final user studies.

### F.2 Analysis: Divergence Between Simulated and Real Users

While user simulators were employed exclusively during training due to the large-scale conversation demands of our Multiturn-aware Reward computation, we provide a comparative analysis to study the divergence between user simulators and real users.
We summarize key differences and similarities in communication patterns between real and simulated users below:

Table 9: Comparison of Simulated vs. Real Users

|  |  |
| --- | --- |
| Differences | Similarities |
| 1) Real users tend to use shorter, fragmented sentences with grammatical errors; simulators produce more complete and polished responses. | 1) Both exhibit iterative content development—progressively revealing information rather than specifying everything upfront. |
| 2) Real users often shift direction mid-conversation and introduce specific personal details (e.g., “eight dogs”); simulated users remain more predictable and generic. | 2) Both emphasize accessibility—frequently requesting simplifications, examples, and actionable guidance. |
| 3) Real users express emotion more bluntly (e.g., “that’s awful”) and use informal language, abbreviations, or incomplete thoughts; simulators respond in a more neutral and formal tone. | 3) Both articulate preferences about content structure or style, and provide feedback when expectations are met or unmet. |

Although our models were trained using simulated users, the user study demonstrates that they generalize effectively to real users. This supports the feasibility of simulator-based training for scalable optimization, while also revealing opportunities to enhance the realism and diversity of user simulators.