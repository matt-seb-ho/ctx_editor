# Cluster 2: Memory-Augmented / External-Memory Agents

Survey date: 2026-08-03. Covers: MemGPT/Letta, Generative Agents, Memento, A-MEM,
MemoryBank, MemoryOS (BAI-LAB), Mem0, HiAgent, MemOS (MemTensor).

Evaluation axes:
- **ENTANGLEMENT**: later user turns contain pronouns/references to specific prior assistant
  outputs (e.g., "redo what you just wrote"). Deleting or abstracting the assistant turn
  leaves the reference dangling.
- **STATEFULNESS**: a persistent environment state (file system, code repo, database, tool
  output) must be tracked across turns; compression or eviction that discards action/
  observation pairs corrupts the agent's world model.

---

## Summary Table

| Method | Venue / Year | Mechanism (1 line) | Weakness re: ENTANGLEMENT | Weakness re: STATEFULNESS | Verified URL |
|---|---|---|---|---|---|
| **MemGPT / Letta** | arXiv 2310.08560, 2023 | OS-style paging: FIFO in-context queue + archival/recall storage; LLM issues function calls to read/write external store | Evicted turns replaced by recursive summary; user's anaphoric references to absent assistant content have no antecedent unless LLM proactively retrieves | Environment state is implicit in FIFO history; eviction + summarisation collapses sequential state transitions; reconstruction requires additional retrieval call | https://arxiv.org/abs/2310.08560 |
| **Generative Agents** | UIST 2023 / arXiv 2304.03442 | Memory stream with recency × importance × relevance retrieval; periodic LLM-generated "reflections" abstract raw observations | Reflections compress specific utterances into higher-level inferences; inter-turn reference chains (e.g., "as you explained in step 3") survive only if the reflection retained the phrasing | Designed for social simulation; no model of external env state; sequential action outcomes stored as flat observations without causal state transitions | https://arxiv.org/abs/2304.03442 |
| **Memento** | arXiv 2508.16153, 2025 | Memory-augmented MDP (M-MDP); episodic Case Bank with neural case-selection policy; adaptation via memory rewriting, not LLM weight updates | Cases stored at episode/task granularity; within-episode cross-turn reference chains are not explicitly resolved before archival | MDP structure tracks state transitions at episode level; fine-grained env state within an episode is not separately maintained after case compaction | https://arxiv.org/abs/2508.16153 |
| **A-MEM** | NeurIPS 2025 / arXiv 2502.12110 | Zettelkasten-style atomic notes with LLM-generated links; embedding retrieval + link-graph traversal | Conversation factorised into discrete atomic notes; inter-turn reference threads (user referring to prior assistant phrasing) are not a first-class link type | Notes capture isolated facts; cumulative env state (e.g., code edits layered on each other) fragmented across unrelated notes with no dependency ordering | https://arxiv.org/abs/2502.12110 |
| **MemoryBank** | arXiv 2305.10250, 2023 | Ebbinghaus-inspired forgetting + retrieval; memory strength decays with time, reinforced by access | Time-decay can drop low-accessed but entangled reference memories before they are needed for resolution | Companion-chat application (SiliconFriend); no environment state model; cumulative state changes not tracked | https://arxiv.org/abs/2305.10250 |
| **MemoryOS** | EMNLP 2025 / arXiv 2506.06326 | Three-tier hierarchy (short/mid/long-term); FIFO dialogue-chain promotion to mid; segmented page consolidation to long-term | Chronological FIFO promotion and segmented-page consolidation discard cross-turn references that are not temporally contiguous | Designed for personal conversational memory; no explicit env state model; long-term consolidation merges state-bearing observations into opaque pages | https://arxiv.org/abs/2506.06326 |
| **Mem0** | arXiv 2504.19413, 2025 | LLM extractor converts conversation into atomic facts; ADD/UPDATE/DELETE/NOOP operations on a semantic store; graph variant (Mem0^g) tracks entity relations | Extraction atomises conversation into facts, discarding the inter-turn dependency structure; "redo the fix you mentioned" becomes an orphaned user reference | Graph variant tracks entities/relations with timestamps but represents state as graph edits, not sequential action-outcome chains; partial state transitions can be missed | https://arxiv.org/abs/2504.19413 |
| **HiAgent** | ACL 2025 / arXiv 2408.09559 | Hierarchical working memory using subgoals as chunks; evicts prior subgoals as summaries; retains only active-subgoal action-observation pairs | Summary-replacement of prior subgoals loses cross-subgoal reference chains; user turns referring to output from a completed subgoal become unresolvable | Action-observation pairs for evicted subgoals are summarised away; fine-grained env state progression within completed subgoals is unavailable to later steps | https://arxiv.org/abs/2408.09559 |
| **MemOS** | arXiv 2507.03724, 2025 | Unified OS for plaintext, activation, and parameter memories (MemCube units with provenance/versioning); scheduler migrates memories across storage tiers | Parameterisation of memories into model weights loses precise conversational phrasing needed to resolve anaphoric references | Activation-layer memory is short-lived; parameter-level consolidation is too coarse to preserve sequential env state transitions across task sessions | https://arxiv.org/abs/2507.03724 |

---

## Positioning Note

External-memory approaches unanimously shift the core design question from "what fits in
context?" to "what is worth writing to memory?" — but this reframing does not resolve either
of our two evaluation axes; it displaces the failure mode into the memory-write decision.
For **entanglement**, every system in this cluster converts raw conversational turns into
some abstract representation (summaries, atomic facts, subgoal chunks, embedding-indexed
notes, or model-weight increments) before archival. This abstraction works well for
long-horizon factual recall but fails when a user's later turn contains an anaphoric
reference to the specific wording or structure of a prior assistant output: the referent was
overwritten by its abstraction, so no amount of retrieval can restore it.
For **statefulness**, most of these systems were designed for conversational or social
settings, not agentic environments with an explicit external state (file system, SQL
database, code under active editing); the few that address agentic use (MemGPT/Letta,
HiAgent) manage state implicitly through action-observation logs and summarise those logs
exactly where sequential state transitions matter most.
Our approach differs structurally: instead of abstracting history before storage, we first
*resolve* entangled references in-place (decontextualize), then selectively prune only the
content that is demonstrably harmful to the ongoing task — preserving both the referential
anchors that user turns depend on and the sequential environment state that the agent must
track.

---

## BibTeX

```bibtex
@misc{packer2023memgpt,
  title        = {{MemGPT}: Towards {LLMs} as Operating Systems},
  author       = {Charles Packer and Sarah Wooders and Kevin Lin and Vivian Fang
                  and Shishir G. Patil and Ion Stoica and Joseph E. Gonzalez},
  year         = {2023},
  eprint       = {2310.08560},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  url          = {https://arxiv.org/abs/2310.08560}
}

@inproceedings{park2023generative,
  title     = {Generative Agents: Interactive Simulacra of Human Behavior},
  author    = {Joon Sung Park and Joseph C. O'Brien and Carrie J. Cai and
               Meredith Ringel Morris and Percy Liang and Michael S. Bernstein},
  booktitle = {Proceedings of the 36th Annual ACM Symposium on User Interface
               Software and Technology (UIST '23)},
  year      = {2023},
  doi       = {10.1145/3586183.3606763},
  url       = {https://arxiv.org/abs/2304.03442}
}

@misc{zhou2025memento,
  title        = {Memento: Fine-tuning {LLM} Agents without Fine-tuning {LLMs}},
  author       = {Huichi Zhou and Yihang Chen and Siyuan Guo and Xue Yan and
                  Kin Hei Lee and Zihan Wang and Ka Yiu Lee and Guchun Zhang and
                  Kun Shao and Linyi Yang and Jun Wang},
  year         = {2025},
  eprint       = {2508.16153},
  archivePrefix= {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2508.16153}
}

@inproceedings{xu2025amem,
  title     = {{A-Mem}: Agentic Memory for {LLM} Agents},
  author    = {Wujiang Xu and Kai Mei and Hang Gao and Juntao Tan and
               Zujie Liang and Yongfeng Zhang},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2025},
  eprint    = {2502.12110},
  url       = {https://arxiv.org/abs/2502.12110}
}

@misc{zhong2023memorybank,
  title        = {{MemoryBank}: Enhancing Large Language Models with Long-Term Memory},
  author       = {Wanjun Zhong and Lianghong Guo and Qiqi Gao and He Ye and Yanlin Wang},
  year         = {2023},
  eprint       = {2305.10250},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  url          = {https://arxiv.org/abs/2305.10250}
}

@inproceedings{kang2025memoryos,
  title     = {Memory {OS} of {AI} Agent},
  author    = {Jiazheng Kang and Mingming Ji and Zhe Zhao and Ting Bai},
  booktitle = {Proceedings of the 2025 Conference on Empirical Methods in
               Natural Language Processing (EMNLP)},
  year      = {2025},
  eprint    = {2506.06326},
  url       = {https://arxiv.org/abs/2506.06326}
}

@misc{chhikara2025mem0,
  title        = {{Mem0}: Building Production-Ready {AI} Agents with Scalable
                  Long-Term Memory},
  author       = {Prateek Chhikara and Dev Khant and Saket Aryan and
                  Taranjeet Singh and Deshraj Yadav},
  year         = {2025},
  eprint       = {2504.19413},
  archivePrefix= {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2504.19413}
}

@inproceedings{hu2025hiagent,
  title     = {{HiAgent}: Hierarchical Working Memory Management for Solving
               Long-Horizon Agent Tasks with Large Language Model},
  author    = {Mengkang Hu and Tianxing Chen and Qiguang Chen and Yao Mu and
               Wenqi Shao and Ping Luo},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for
               Computational Linguistics (ACL), Long Papers},
  year      = {2025},
  eprint    = {2408.09559},
  url       = {https://arxiv.org/abs/2408.09559}
}

@misc{li2025memos,
  title        = {{MemOS}: A Memory {OS} for {AI} System},
  author       = {Zhiyu Li and others},
  year         = {2025},
  eprint       = {2507.03724},
  archivePrefix= {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2507.03724}
}
```
