# Method Name Discussion

## Goal
Replace the placeholder **"Agentic Context Curation (ACC)"** with a memorable name. The MSR mentor's design brief:

- Must be memorable — think *Memento* (compaction, each summary is a memento) or other "word-salad" ML names that blend partial words.
- Should convey the two features that distinguish us from the existing context-engineering literature:
  1. **Multi-turn human–AI conversation** (most prior compaction work targets single-query + long CoT).
  2. **Pollution removal / correctness**, not compaction / efficiency.
- Not strictly an acronym: mixed-capitalization partials (like *BERT*, *Memento*, *MuSR*, *CURATE*, *ARC-AGI*) are fine.
- "Agentic Context Management" / "Agentic Context Editing" are ruled out (too generic; the latter is already taken).
- Advisor nudged toward verbs of selective attention: *focus*, *mute*, etc.

## Shortlist (my favorites, ranked)

### 1. **MUTE** — *Multi-turn Utterance Triage & Editing*
- **Hook:** mute = silence → the method silences the parts of the assistant's prior reasoning that mislead. Sharp and memorable.
- **Fits the axis:** "multi-turn" is literally the M; "triage" emphasizes selective keep-vs-remove, not compaction.
- **Works as a verb in prose:** "we MUTE the polluting turns."
- **Risks:** short acronym; search-discoverability is moderate (words like "mute" are common). Easy to confuse with mute-attention mechanisms in transformers.

### 2. **CURATE-MT** — *Context Update via Re-specification and Attention Triage, for Multi-Turn*
- **Hook:** "curate" is already the paper's core verb; the MT suffix directly encodes the setting.
- **Fits the axis:** explicit "Multi-Turn" in the name; "re-specification" captures Subtask 1, "attention triage" captures Subtask 2.
- **Risks:** six syllables, acronym feels forced. Some papers have used "CURATE" before.

### 3. **FoCus** — *Filtering of Context for User-grounded Specifications*
- **Hook:** "focus" = selective attention, the exact cognitive-science analog.
- **Fits the axis:** the backronym foregrounds the user-grounded specification (our Subtask 1).
- **Risks:** "FoCus" is a crowded namespace in ML (at least 3–4 papers).

### 4. **ReTURN** — *REwriting Turns for User-grouNded context*
- **Hook:** ReTURN reads naturally in prose ("we ReTURN each turn"). Puns on "turn" as the unit of conversation.
- **Fits the axis:** "turns" encodes multi-turn; "rewriting" encodes the intervention.
- **Risks:** "ReTurn" is overloaded in coding contexts; the acronym cuts oddly.

### 5. **ConvoCurate** (or **CONVOCURATE**) — coined blend
- **Hook:** a Memento-style portmanteau (convo + curate). Very memorable; signals the content without needing a backronym.
- **Fits the axis:** "convo" pins it to conversations; "curate" is the method verb.
- **Risks:** not a "real" acronym; some venues prefer acronym-derivable names. Also slightly cutesy.

### 6. **CLEAR** — *Curating Long Exchanges to Attend to Requirements*
- **Hook:** "clear" semantically matches "removing pollution" and positive connotation.
- **Risks:** CLEAR is hugely overloaded (at least a dozen ML papers). Poor search SEO.

## Second-tier / honorable mentions

- **TURNTIDE** — Turn-level Task-Informed Dialog Editor. Cute, evokes "turning the tide," but a stretch.
- **REFRAME** — Re-Examining Failures via Requirement-grounded Attention Management Editing. Good verb; crowded namespace.
- **TALKCURE** — portmanteau; evokes "talk cure" (psychoanalysis), playful, fits executive-function motif.
- **DECONVO** — DEcontaminating CONVersation history. Punchy; may sound too negative.
- **MUSE-MT** — Multi-turn User-grounded Specification Editor. Soft, memorable, "muse" feels disconnected from selective-removal though.
- **PurgeMT** — not recommended, "purge" is too aggressive and mischaracterizes the method.
- **MemoFree / NoMemento** — explicitly anti-compaction framing ("the opposite of Memento: forget on purpose"). Cute but niche.
- **CURSE** — *Conversation Understanding via Re-Specification & Editing*. Punchy and memorable… but negative connotation is a major liability.

## Design tradeoffs

- **Short (≤ 6 letters) acronyms travel further in citations and slide decks but collide more in search.** MUTE, FOCUS, CLEAR fall here.
- **Portmanteaux (ConvoCurate, TalkCure) are more distinctive and harder to confuse with other papers,** but some reviewers view them as un-serious.
- **Suffix disambiguation ("-MT", "-HAI")** helps distinguish from neighbors in crowded namespaces, at the cost of polysyllabicity.
- **Negative-framed names** (MUTE, PURGE, DECONVO) match our "remove pollution" story, but can feel aggressive — especially in a paper whose best-performing intervention (Gated Reset) is fairly surgical and preserves most context.
- **Positive-framed names** (CURATE, CLEAR, FOCUS) match the "preserve what's correct" side of the story better, but sound more generic.

## Recommendation

Lead candidate: **MUTE** — *Multi-turn Utterance Triage & Editing.*

- Short, easy to say, works as both a verb and noun, carries the selective-silencing metaphor cleanly, and pins the setting (multi-turn) in the first letter.
- Pairs naturally with the executive-function framing in the paper: "inhibitory control" literally means muting the inappropriate response.
- Lets the title be method-name-forward without becoming a tongue-twister: e.g., *"MUTE: Harness-Level Context Curation for Multi-Turn Human–AI Conversations."*

Backup candidate: **ConvoCurate** — a less-acronym-dependent Memento-style blend, in case MUTE feels too negatively framed or collides with existing work in a way that turns up during lit search.

## To decide
1. **Degree of acronym purity.** Strict first-letter (none of the above are strict) vs. selective-letter mix (MUTE, CURATE) vs. pure blend (ConvoCurate).
2. **Positive vs. negative framing.** MUTE leans negative ("silence the bad"); CURATE/FOCUS lean positive ("elevate the good"). We technically do both, but a single-word branding has to pick one emphasis.
3. **Should the method name also appear in the title?** See `title_discussion.md` — Group D titles assume yes; most other options work with or without.
