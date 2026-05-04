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

---

# Round 2 — positive-connotation candidates with explicit multi-turn

## What's new in this round
Mentor feedback on the round-1 favorites:
- **MUTE** reads as negative (silencing).
- **CURATE / CURATE-MT** evokes janitorial cleanup for him.

So this round's filters:
1. **Positive or constructive connotation** — frame the method as building/aligning/sharpening, not removing/scrubbing/silencing. Avoid: mute, purge, scrub, clean, sweep, decontaminate, sanitize, *and* curate.
2. **"Multi-turn" appears explicitly in the expansion** (typically as `-MT` suffix or via "Turn" inside the acronym), to distinguish us from agentic / single-query context-management work like ACE, Memento, MemGPT, ERGO.
3. **Distinct from existing names.** Avoid heavy-collision tokens (FOCUS, CLEAR, ANCHOR, ATTEND, GROUND, COMPASS, ALIGN are all crowded); prefer slightly off-the-beaten-path roots.

## Round-2 shortlist

### 1. **ATTUNE-MT** — *ATtention TUNing for Multi-Turn dialogue*
- **Hook:** *attune* = bring into harmonious alignment. Captures "shifting the assistant's attention back into accord with what the user actually said." Pairs naturally with executive-function framing (attentional control).
- **Connotation:** strongly positive — harmonization, awareness, alignment.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "Attune" appears in a couple of recommender-system papers but is essentially absent from the LLM context-management literature.
- **Reads as a verb:** "we attune the conversation to the user spec."

### 2. **REGROUND-MT** — *REasoning Re-GROUNDing for Multi-Turn conversations*
- **Hook:** the assistant's reasoning has drifted off the user-spec foundation; we re-ground it. "Grounding" is the standard NLP word for tying a model's output to source evidence — extending it to *re*-grounding the conversation history is a natural twist.
- **Connotation:** positive — restoring foundation, returning to truth.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "GROUND" alone is crowded, but "REGROUND" as a method name is essentially unused in this space.
- **Reads as a verb:** "we reground each turn against the user's stated requirements."

### 3. **HONE-MT** — *Honing On user iNtent through Editing across Multi-Turns*
- **Hook:** *hone* = sharpen by careful refinement (whetstone metaphor). Implies craftsmanship, precision, getting closer to the target — not removing dirt.
- **Connotation:** positive — refinement, mastery, precision.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** lightly used in ML; no major collisions in context engineering.
- **Risks:** four-letter acronym; the backronym is a slight stretch ("Editing" is forced).

### 4. **TURNTUNE** — *blend of "turn" + "tune"* (no strict backronym)
- **Hook:** Memento-style portmanteau. We re-tune each turn so the conversation stays in tune with user intent. The repetition of "tune" inside "TURNtune" makes it sticky.
- **Connotation:** positive — tuning a musical instrument, not cleaning. Suggests delicate adjustment, not removal.
- **Multi-turn:** "TURN" carries it without needing a suffix.
- **Distinctness:** very distinctive — searchable, no collisions found.
- **Risks:** non-acronym names sometimes feel less "serious" to reviewers; less obvious how to formalize it in a definition box.

### 5. **TAILOR-MT** — *Tailoring AssIstant Logic to User Requirements (Multi-Turn)*
- **Hook:** tailoring = bespoke, fitted-precisely-to-the-customer craftsmanship. Strong consumer-positive connotation, and "fitting the conversation to what the user actually asked for" is exactly our story.
- **Connotation:** positive — care, customization, expertise.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "TAILOR" has been used as an acronym in a few NLP papers (style transfer, instruction tuning); none specifically for multi-turn context management, but worth a 5-min lit-search before committing.
- **Risks:** mild namespace collision; backronym slightly forced.

### 6. **REFOCUS-MT** — *REview and FOCUS on User Specification (Multi-Turn)*
- **Hook:** preserves the advisor's "selective attention" angle (FOCUS family) while sidestepping the FOCUS namespace collision via the prefix. The "RE-" also makes the corrective story explicit: we re-focus a conversation that has drifted.
- **Connotation:** positive — clarity, restored attention.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** much less crowded than FOCUS alone.
- **Risks:** still vaguely in the FOCUS orbit; reviewers familiar with prior FOCUS papers might mentally bin it together.

## Honorable mentions (round 2)

- **CONTUNE-MT** — Conversation Tuning, MT. Same musical-tuning vibe as TURNTUNE but more acronym-shaped. A bit clunky to say.
- **REWEAVE-MT** — REWeaving Exchanges to Align with Verified user intent. Artisanal, positive. Slightly purple.
- **ORIENT-MT** — Orienting Reasoning toward Intent and Expressed Needs in Turns. Compass-style metaphor, positive. ORIENT has a few NLP collisions.
- **CRAFT-MT** — Conversational Refinement of Assistant Frame to Task. Positive, but CRAFT is moderately crowded.
- **REVIVE-MT** — Revising Intent-Violating Exchanges (Multi-Turn). Positive (revival/recovery), but implies the conversation was "dead," which is a stretch.
- **WAYPOINT-MT** — too long, but the "navigation checkpoint" metaphor is appealing.
- **FIDELIS** / **FIDELIO** — Latin "faithful." Elegant but obscure; reviewers may not parse the connotation quickly.

## Round-2 recommendation

Top pick: **ATTUNE-MT**.
- Positive, executive-function-flavored, multi-turn explicit, and basically uncrowded in our subarea.
- Reads cleanly as a verb in prose ("we ATTUNE the conversation history before each assistant turn").
- The "tuning" metaphor matches the actual operation better than "cleaning" — we're nudging emphasis, not removing dirt.

Strong backups, in order:
1. **REGROUND-MT** — if reviewers respond better to the standard NLP "grounding" vocabulary than to a sensory metaphor.
2. **TURNTUNE** — if the mentor wants something more *Memento*-style and less acronym-shaped.
3. **HONE-MT** — short, crisp, craftsmanlike; good fallback if ATTUNE feels too soft.

## What to bring to the mentor
A 3-way comparison is usually most useful: present **ATTUNE-MT**, **REGROUND-MT**, and **TURNTUNE** as one positive-attention pick, one grounding-vocabulary pick, and one Memento-style-blend pick respectively. That covers the three flavors of "positive framing" without overwhelming him with the full list.

---

# Round 3 — cute and "non-tuning" candidates

## What's new in this round
Additional filter on top of Round 2:
- **Drop "tune" / "tuning"** — too easy to misread as fine-tuning, which is not what we do. So ATTUNE-MT, TURNTUNE, CONTUNE-MT, etc. are retired.
- **Lean a little cute.** Memorable, mildly playful, slightly evocative — closer in vibe to *Memento*, *Llama*, *Orca*, *Mamba*, *Beaver*, *BLOOM* than to a dry acronym. Not silly — just a name with a little personality and visual handle.
- Still: positive connotation, multi-turn in the expansion or the root, low collision risk.

The cute angle is doing real work here — a name with a clean visual metaphor (lighthouse, north star, duet, homing pigeon) is much easier for the mentor to react positively to than a sterile acronym, and it gives the paper a hook for figures and slide titles.

## Round-3 shortlist

### 1. **DUET-MT** — *Dialog Understanding & Editing of Turns (Multi-Turn)*
- **Hook:** the user–assistant exchange *is* literally a duet — the cleanest metaphor in this list for the multi-turn setting. The method's job is to keep the two voices in agreement.
- **Cuteness:** musical-collaboration imagery without invoking "tuning." Reads sweet in prose: "DUET re-aligns each turn before the assistant sings back."
- **Positivity:** collaborative, generative, partner-y.
- **Multi-turn:** the metaphor itself encodes multi-turn; `-MT` makes it explicit.
- **Distinctness:** there's a "DUET" in some recsys / dialogue work but nothing dominant in context-editing space.

### 2. **TRUETURN** — *blend of "true" + "turn"*
- **Hook:** Memento-style portmanteau. We keep each turn *true* to the user's intent. Echoes "true north" without saying it.
- **Cuteness:** doubled "tu-" makes it sticky; reads as a single word, not an acronym.
- **Positivity:** "true" carries fidelity / honesty connotations.
- **Multi-turn:** "TURN" is the root.
- **Distinctness:** essentially unused as an ML method name.
- **Risks:** non-acronym; some reviewers prefer derivable names. Could pair with a soft backronym (*Turn-level Re-grounding to User-intent Expectations*) for the figure caption.

### 3. **POLARIS-MT** — *Preserving On-target Logic And Reasoning via Intent-grounded Surgery (Multi-Turn)*
- **Hook:** the user's intent is the north star; the assistant drifts; we re-orient toward Polaris. Aspirational guidance metaphor.
- **Cuteness:** celestial, evocative, looks great on a figure (a literal star icon).
- **Positivity:** unambiguously positive — guiding light, true north.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "Polaris" is taken in plenty of product names but not as a context-editing method.

### 4. **BEACON-MT** — *Bringing Exchanges back to user-grounded Anchors for CONversations (Multi-Turn)*
- **Hook:** a lighthouse cutting through fog — the conversation has drifted into mist, the beacon (re-applied user intent) brings it back to the right heading.
- **Cuteness:** strong visual handle for figures; "beacon" is warm without being saccharine.
- **Positivity:** guidance, safety, illumination.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "Beacon" appears in a handful of NLP/recsys works but none specifically about multi-turn context repair.

### 5. **HOMING-MT** — *Homing On user iNtent across Multi-turn Generation*
- **Hook:** homing-pigeon imagery — no matter how far the conversation has wandered, the assistant homes back to the user's stated requirements every turn.
- **Cuteness:** playful, friendly, has a clear mental picture (you can literally draw the pigeon in the figure).
- **Positivity:** instinctive return to home / target.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** "homing" is rarely used as a method name in NLP.

### 6. **REMIND-MT** — *REwriting Memory for INtent-grounded Dialog (Multi-Turn)*
- **Hook:** wordplay — we literally *re-mind* the assistant by editing what's in its context. The pun is the whole point.
- **Cuteness:** clever, low-effort, easy to explain in one breath.
- **Positivity:** gentle, supportive ("a friendly reminder"), not corrective-aggressive.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** as an acronym in this subarea, essentially unused.

### 7. **MEND-MT** — *Multi-turn Editing of Notes and Dialog*
- **Hook:** "mend" is the gentlest possible repair word in English — you mend socks, mend fences, mend a friendship. Repair without aggression, care without janitorial overtones.
- **Cuteness:** small, warm, domestic. The word itself feels handmade.
- **Positivity:** restorative, careful.
- **Multi-turn:** the M of MEND *is* multi-turn (so the suffix `-MT` becomes optional).
- **Distinctness:** uncrowded.
- **Risks:** could imply something was "broken" (rather than just drifted); slightly understates the active intervention.

### 8. **RUDDER-MT** — *Re-grounding Utterances and Dialog Drift to user Expectations & Requirements (Multi-Turn)*
- **Hook:** the rudder is small, but it steers a whole ship. Tiny edits in the context steer the whole assistant trajectory back on course.
- **Cuteness:** concrete object, sailing/maritime imagery, draws well in figures.
- **Positivity:** steering toward destination, not running away from anything.
- **Multi-turn:** explicit `-MT`.
- **Distinctness:** lightly used in robotics control papers but not in NLP context engineering.
- **Risks:** backronym is the most strained of this batch.

## Honorable mentions (round 3)

- **LATCH-MT** — *Locking Assistant Turns to Constraints from Human (Multi-Turn).* Cute "snap into place" feeling. Slightly possessive.
- **ECHO-MT** — *Editing Conversation History toward Original intent (Multi-Turn).* Cute reflective metaphor; "echo" is overloaded though.
- **MIRROR-MT** — *Mirroring User Requirements In Repaired Output Reasoning.* Reflection imagery; backronym is forced.
- **TURNTABLE** — Memento-style portmanteau (turn + table). DJ-remix vibe is cute but maybe too whimsical for a NeurIPS title.
- **WAYPOINT-MT** — Navigation imagery, but four-syllable root is heavy.
- **HARBOR-MT** — "Bringing the conversation safely back to port." Pleasant but quite soft.
- **PILOT-MT** — *Pruning Inferences and Logic On Track (Multi-Turn).* Cute "co-pilot" vibe but Microsoft Copilot brand collision.

## Round-3 recommendation

Top pick: **DUET-MT**.
- The metaphor maps onto the setting more cleanly than any other candidate — multi-turn human–AI dialogue *is* a duet, and the method's job is to keep the two voices in agreement. That alignment between the name and the problem is rare and worth a lot.
- Visually friendly: "two voices" is a one-glance figure.
- Positive without being saccharine; cute without being un-serious.

Strong backups, in order:
1. **POLARIS-MT** — if the mentor wants something more aspirational and figure-friendly. (North star icon = great teaser figure.)
2. **TRUETURN** — Memento-style word-salad pick; carries multi-turn in the root and feels distinctive.
3. **REMIND-MT** — if the mentor likes wordplay (the "re-mind" pun does a lot of work for one syllable).
4. **HOMING-MT** — if a friendly-animal mascot vibe is welcome.

## What to bring to the mentor (revised)
Show three different flavors of cute-but-credible so he can react to the style as well as the name:
- **DUET-MT** — metaphor-first (collaboration).
- **POLARIS-MT** — metaphor-first (navigation/aspirational).
- **TRUETURN** — wordplay-first (Memento-style blend).

If he likes one of those flavors, the others in that family (BEACON-MT / HOMING-MT for navigation; REMIND-MT for wordplay; MEND-MT / RUDDER-MT as quieter alternates) become the next round of refinement.

---

# DUET backronym refinement (and "context X" wrapping)

The original *Dialog Understanding & Editing of Turns* expansion reads as clunky — the "of" makes "Editing of Turns" feel padded. Below are cleaner reformulations, plus a note on wrapping "context engineering" into the name.

## Wrapping "context engineering" / "management" / "pollution"

- **"Context engineering"** is the right label to lean on — it's the live discourse the paper enters and helps reviewers place us. DUET can absorb it.
- **"Context pollution"** should stay a concept in the paper text (we use it to name the problem) but *not* in the method name. "De-polluting" in the name re-introduces the negative-framing trap that retired MUTE.
- **"Context management"** is fine but adds little beyond "context engineering."

## Cleaner DUET expansions

### Option A — direct, multi-turn explicit, context as modifier
**DUET-MT** — *Drift-Undoing context-Editing for Turns*
- All four letters direct; "context" enters as a lowercase modifier on "Editing."
- "Drift-undoing" is a positive corrective verb — we're restoring trajectory, not removing dirt.
- Multi-turn explicit through both `-MT` and "Turns."
- This is the recommended pick — cleanest read of the three.

### Option B — context up front, T = triage
**DUET-MT** — *Dialog-context Updates via Editorial Triage*
- "Context" appears at the front. T is reassigned from Turns to Triage, so multi-turn lives only in `-MT`.
- Reads more like a system description than a metaphor; closer in tone to a methods-section header.
- Tradeoff: loses the literal "turn" word inside the acronym.

### Option C — fold "context engineering" into the acronym itself
**DUET** — *Drift-aware User-grounded conText Engineering*
- The T is the T of "conText." Boldest move: folds the full discipline label into the name.
- Multi-turn must live in the title sentence (e.g., *"DUET: Context Engineering for Multi-Turn Human–AI Conversations"*) rather than the acronym.
- Tradeoff: most expressive, but multi-turn is no longer carried by the name itself.

## Recommendation

**Option A** — *Drift-Undoing context-Editing for Turns* — is the strongest of the three.
- Keeps multi-turn explicit (which Round 2 / Round 3 specifically wanted).
- Wraps "context" without forcing every letter to do new work.
- "Drift" names what we actually fix: the assistant drifts off the user's spec across turns. It's diagnostic, not janitorial.
- Reads cleanly in prose: *"DUET-MT undoes assistant drift via per-turn context edits."*

## POLARIS note

POLARIS is harder to absorb "context" into without forcing a letter. Best non-forced version:
- **POLARIS-MT** — *Pruning Off-spec Logic, Anchored to Requirements & Intent across Sessions (Multi-Turn)*

I'd let the discipline label live in the surrounding sentence rather than the backronym: *"POLARIS, a multi-turn context engineering method that..."* Forcing "context" into the acronym costs more than it gains here.

---

# MT-RUDDER (prefix variant) — note

The user is warming to **MT-RUDDER** over `RUDDER-MT`. Worth flagging as a structural choice, not just a cosmetic flip:

- **`MT-` prefix → multi-turn becomes the framing tag**, not an afterthought-suffix. The name reads as "multi-turn rudder," i.e., a rudder *for* the multi-turn setting — positioning the method squarely in the multi-turn axis of the context-engineering literature on first read.
- **The metaphor is doing real work.** A rudder is a small surface that steers a much larger ship: small per-turn context edits steer the whole assistant trajectory. That maps onto our method's actual mechanism (surgical edits, not wholesale reset) better than most alternatives in the list.
- **Connotation is positive and concrete.** Steering toward a destination, not removing dirt; navigation rather than cleanup.
- **Distinct.** Lightly used in robotics control papers but essentially absent from NLP / context-editing.

Backronym options (optional — the metaphor mostly carries the name):
- **MT-RUDDER** — *Multi-Turn Re-grounding of Utterances and Dialog via Drift-correcting Edits & Re-orientation*
- **MT-RUDDER** — *Multi-Turn Re-anchoring of User-grounded Dialog via Directed Edits & Re-grounding*

The first is more verb-y and matches the method's actual mechanism; the second is a touch cleaner but slightly redundant. Either works; the metaphor is the load-bearing element.

## Recommendation update

If we're picking a navigation-metaphor finalist between `BEACON-MT`, `POLARIS-MT`, and `MT-RUDDER`, I'd put `MT-RUDDER` first:
- **BEACON / POLARIS** are *guidance* metaphors (the user intent is the light/star you head toward). Nice but slightly passive.
- **RUDDER** is an *intervention* metaphor (the rudder *does* the steering). More accurately captures that we are taking an active corrective action, not just illuminating the goal.

Combined with the user's positive read, MT-RUDDER deserves to be in the top-3 short-list alongside DUET-MT and TRUETURN.

---

# Round 4 — fresh candidates from the naming brief (independent subagent runs)

Two general-purpose subagents were given only `writing/method_naming_brief.md` (no access to this discussion doc) and asked to generate 8–12 candidates each in fresh metaphor space. The brief listed all prior candidates as "do not re-propose" so this round is uncontaminated by Rounds 1–3.

## Convergent candidates (both runs surfaced these)

These appeared in *both* independent runs — high signal that the metaphor space is genuinely fitting.

### **PARLEY** — Memento-style, no acronym, no `-MT` needed
- **Hook:** a parley is, by dictionary definition, a *structured multi-turn negotiation between parties to clarify terms.* Intrinsically multi-turn; intrinsically constructive.
- **Why it stands out:** uniquely solves the multi-turn-positioning problem without a suffix. The word *means* multi-turn. Passes the Memento test cleanly: one concrete word whose dictionary meaning maps onto the method's central object.
- **Connotation:** positive (negotiation, mutual understanding, restoring agreement).
- **Distinctness:** essentially unused as an NLP method name.
- **Tradeoff:** slightly archaic register; "parley" is recognizable but not everyday. Some readers will think "pirate movie" before "diplomacy."
- **Run B's favorite.**

### **LOOM-MT** — weaving metaphor, intrinsic multi-thread structure
- **Hook:** a loom holds many threads in tension; you can pull a wrong row out and re-set it without losing the pattern. Conversation = warp (user intent) + weft (per-turn assistant work); we re-set bad weft without unraveling the cloth.
- **Connotation:** positive (craftsmanship, construction).
- **Distinctness:** lightly used in graph / 3D-vision papers; modest collision but not in our subarea.
- **Tradeoff:** common English word — search SEO is moderate.
- **Run A's favorite.**

### Also convergent (both runs):
- **TRELLIS-MT** — supportive scaffold for growth; gardening without pruning. Slightly passive (the trellis doesn't act).
- **RELAY-MT** — clean baton handed to the next runner. Strong mechanism story; "relay" is overloaded in networking/RL.
- **KILN-MT** — re-fire between stages, harden good work. Borderline on Hard Rule 1 ("burn off" leans janitorial).

## Single-run candidates worth keeping

### From Run A
- **WARP-MT** — *warp* = the structural lengthwise threads that run through all turns. Same weaving family as LOOM but emphasizes the "structural intent that persists across turns" angle. Risk: "warp" also means *distortion*, which is the opposite of what we want.
- **ATELIER-MT** — working studio where partial works sit on easels between sessions; the analyzer rearranges the easels before the next pass. Beautiful but five syllables — heavy on a slide.
- **PLINTH-MT** — the stable base under a sculpture; we rebuild a clean plinth (user intent) under the assistant's evolving work each turn. Less visually iconic than rudder/beacon.
- **CADENCE-MT** — musical resolution back to the tonic; we resolve back to user intent before the next phrase. Abstract; needs framing in prose.
- **PROMPTER-MT** — theatrical prompter offstage feeding the next line. On-metaphor for our analyzer, but "prompt" is dangerously overloaded in LLM contexts.
- **STANZA-MT** — between stanzas the poet revises and keeps the good lines. Ornamental for a systems paper.
- **ASTROLABE-MT** — re-take a fix on the stars at intervals to correct accumulated dead-reckoning error. Strong metaphor but obscure object.

### From Run B
- **KEEPSAKE-MT** — sibling of Memento that emphasizes *selective preservation* rather than memorialization. Risk: adjacency to Memento may read as derivative.
- **SEXTANT-MT** — re-fix position by sighting a known reference. Strong metaphor but the navigation lane is already crowded with POLARIS / BEACON / RUDDER.
- **APERTURE-MT** — controls what light (context) reaches the sensor (next turn). Risk: reads as a sparse-attention method.
- **ENCORE-MT** — re-performance of the good parts. Implies repetition, not correction — slightly off-target.
- **ATLAS-MT** — living map of where the conversation actually is. "Atlas" has multiple NLP system precedents.
- **SERIF-MT** — typographic flourishes that guide the eye across long passages. Subtle, possibly too decorative.
- **PARSLEY-MT** — culinary palate-cleanser; phonetic wink at PARLEY. Cute but risks "silly" at NeurIPS.

## Round 4 takeaways

1. **PARLEY is the standout** — it is the only candidate across all four rounds that doesn't need an `-MT` suffix because the word's meaning is intrinsically multi-turn. That is a structural advantage no other candidate has. It also passes the Memento test more cleanly than DUET, POLARIS, or MT-RUDDER (each of which needs a backronym or suffix to do part of the work).
2. **The weaving / textile lane is rich** — LOOM, WARP, and TRELLIS all came up. Worth considering as a coherent metaphor cluster if the mentor responds well to any one of them.
3. **The convergence between independent runs validates the brief.** When two independent runs surface the same five names from disjoint starting points, those names are likely strong on the rules, not just stylistic flukes.

## Updated top-tier short-list (across all rounds)

| Name | Style | Multi-turn signal | Best feature |
|---|---|---|---|
| **PARLEY** | Memento-style word | intrinsic to word | no suffix needed; dictionary meaning fits |
| **DUET-MT** | metaphor | -MT suffix; "duet" implies pairing | maps user/assistant pair onto the metaphor |
| **MT-RUDDER** | metaphor | MT- prefix | active intervention metaphor; small-thing-steers-big |
| **LOOM-MT** | Memento-style word | -MT + weaving structure | strong figure handle; constructive |
| **POLARIS-MT** | metaphor | -MT suffix | aspirational; figure-friendly icon |

If we present the mentor a final 3-way: **PARLEY** (Memento-style purist pick), **MT-RUDDER** (active-intervention pick), **DUET-MT** (collaborative-metaphor pick).
