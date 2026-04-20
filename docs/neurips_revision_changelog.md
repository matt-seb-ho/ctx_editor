# NeurIPS Revision Changelog

## 2026-04-20 — Feedback from Lianhui (17 Apr) and Michel (19 Apr)

---

### 1. Title: Remove "EF," rename approach

**Before:** `Curing Context Pollution: Externalized Executive Function for Multi-Turn LLM Conversations`  
**After:** `Agentic Context Curation for Multi-Turn LLM Conversations`

**Why:** Lianhui and Michel both asked to remove EF from the title. Michel wants the title to emphasize (1) solving a multi-turn problem and (2) agentic intervention—not a training method. The new title names the approach (Agentic Context Curation) and the setting (multi-turn LLM conversations). Michel also suggested drawing on the "LLMs managing their own context" framing; "Agentic Context Curation" captures that without too directly referencing the MSR paper.

**Alternative titles considered (for discussion with advisors):**
- `Staying on Track: Agentic Context Curation for Multi-Turn LLM Conversations` — more catchy, emphasizes navigation metaphor Michel mentioned
- `Agentic Context Curation: Helping LLMs Navigate Multi-Turn Conversations` — clearer but longer
- `Clearing the Context: Agentic Curation for Multi-Turn LLM Interactions` — avoids "pollution" in title per Michel

---

### 2. Abstract: Soften EF from "we frame this as" to "inspired by"

**Before:** "We frame this as a deficit of \emph{executive function}: the higher-order cognitive capacity..."  
**After:** "Inspired by \emph{executive function}---the higher-order cognitive capacity...---we propose a training-free, inference-time context curation method..."

**Why:** Lianhui's instruction: "ok to keep 'inspired by EF' in the abstract." The old phrasing made EF the central theoretical frame; the new phrasing positions EF as design inspiration while keeping the proposed method as the subject of the sentence.

---

### 3. Intro para 2: Remove student analogy, reduce EF weight

**Removed:** "A student who realizes one lemma in their proof is wrong can scratch out that lemma while keeping the rest; an LLM that has generated three turns of reasoning---some correct, some not---cannot selectively discard the flawed parts..."

**Why:** Lianhui explicitly asked to remove the student analogy.

**EF framing reduced:** Changed `\textbf{executive function}` to `\emph{executive function}` and replaced the extended EF explanation with a single sentence describing the LLM's parallel deficit. The detailed EF justification now lives in the Related Work section (moved—see below).

---

### 4. Method name: "Agentic Context Curation (ACC)"

**Changed throughout:** `context curation via externalized executive function` → `Agentic Context Curation (ACC)`

**Locations updated:**
- Intro para 4 (method proposal sentence)
- Figure 2 caption
- Algorithm 1 caption
- Conclusion opening sentence

**Why:** Lianhui asked to give the method an actual name. Michel wants to emphasize agentic intervention. "ACC" is memorable and describes what the method does without requiring the EF framing.

---

### 5. Self-correction localization citation (Tyen et al. 2024)

**Added citation in intro para 4:**  
"...then identifies *where* the assistant's work diverges from that specification~\citep{tyen2024errors}..."

**Paper:** Tyen, Mansoor, Carbune, Chen, Mak. "LLMs cannot find reasoning errors, but can correct them given the error location." *Findings of ACL 2024.*

**Why:** Lianhui noted that research shows pointing out *where* the problem is is as important as how to fix it. This is exactly what Tyen et al. demonstrate: LLMs can correct errors when given error location but cannot find the location themselves. Our method's core contribution is the structured pipeline that identifies *where* the context is polluted—this citation directly supports that framing.

**Also note:** This citation is a natural complement to `kamoi2024criticalselfcorrect` already in the methods section (line ~153), which shows intrinsic self-correction fails without external feedback. Tyen et al. adds the positive result: given location, correction succeeds.

---

### 6. Related Work: Moved from before Methods to after Discussion

**Before:** Related Work appeared immediately after the Introduction (standard position).  
**After:** Related Work appears between Discussion and Conclusion.

**Why:** Lianhui: "abstract + intro + related work means reader doesn't get to our method until several pages in." Moving it after Discussion lets the reader reach Methods immediately after the intro, reducing time-to-method. This is an increasingly common structure at NeurIPS/ICML for methods-heavy papers.

**Note on references:** `\label{sec:related}` is preserved. No cross-references to `\ref{sec:related}` were found in the main text, so this move is safe. Internal section cross-references (e.g., `Section~\ref{sec:decomposition}`) within the Related Work block are unaffected since those sections still exist.

---

### 7. Related Work: Trim U-Fold/MemoBrain paragraph

**Before:** ~100-word paragraph covering U-Fold and MemoBrain in detail.  
**After:** ~50-word summary, pointing to Appendix~\ref{app:agentic-context} for full comparison.

**Why:** The appendix already has a detailed comparison. This trims ~50 words from the main text to help with page budget. Combined with the student-analogy removal (~35 words) and minor intro tightening, this moves the paper toward the 9-page limit.

---

### 8. Related Work: Trim EF paragraph slightly

Removed "not merely as an analogy but as" from the EF paragraph (now in Related Work after Discussion). The connection is stated functionally without the meta-commentary about whether it's "merely an analogy."

---

## Outstanding items

- **Title final decision**: Three alternatives listed above—please confirm preferred title with advisors (especially in light of the upcoming LiC news Michel mentioned).
- **Tyen et al. citation placement**: Currently in intro para 4. Could also be strengthened by adding it to the methods section (Section 3.2, near `kamoi2024criticalselfcorrect`). Recommend adding once title/framing is settled.
- **New figure 1** (statefulness vs. performance): Lianhui requested a new Figure 1 that relates statefulness to performance to show where the method applies. Not addressed here—this is a data/visualization task.
- **Figure 2 redesign** (pollution illustration): Suggestion—use different background colors or fonts to distinguish the conversation turns from the analysis layer, making the pollution vs. curation contrast more visually obvious. Not edited in .tex since this is an asset change.
- **New experiment: reasoning effort vs. context pollution**: Michel/Lianhui suggest exploring how different reasoning effort levels relate to context pollution. Not addressed here.
- **Page count**: Student analogy removal (~35 words) + U-Fold/MemoBrain trim (~50 words) + minor EF tightening (~20 words) = ~105 words removed. At NeurIPS column width, ~100 words ≈ 0.3–0.4 pages. Should help move from 9.3 toward 9 pages, but compile and measure to confirm.
