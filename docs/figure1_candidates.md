# Figure 1 Candidates: Context Pollution Illustration

## Requirements

Single-column conference paper figure (short and wide). Shows an abbreviated multi-turn conversation illustrating the "lost in conversation" / context pollution problem, with annotations on the right explaining the failure.

### Pattern

1. **Turn 1 User:** General ask (underspecified)
2. **Turn 1 Assistant:** Establishes initial approach, makes assumption(s) in response to underspecification
3. **... (possible intervening turns)**
4. **Turn N User:** Introduces a new constraint that subtly invalidates the assistant's earlier assumption and requires a fundamentally different approach (no small patch suffices)
5. **Turn N Assistant:** Attempts a patch fix on the existing solution instead of rethinking

### Key criteria

- Easy to understand for a broad audience
- Abbreviable to 2-3 turns (~4-6 messages), with ellipsis for skipped turns if needed
- The error must be clearly caused by **context history** (anchoring on old approach), not by lack of model capability. The same model given the full spec in one shot would get it right.
- Must NOT read as: (a) instruction-following failure (model ignoring the user), (b) knowledge error (model doesn't understand the concept), or (c) user's fault for being unclear.

---

## Candidate 1: Build steps - Sorting vs. dependency ordering (CODE) **[STRONG]**

### Setup
User needs to order build steps. Initially just wants alphabetical, then reveals dependency constraints.

### Conversation

**User:** I have a list of build steps, each with a name. Can you write a function that returns them in a readable order?

**Assistant:**
```python
def order_steps(steps):
    return sorted(steps, key=lambda s: s['name'])
```

**...** *(possible intervening turns clarifying format, etc.)*

**User:** Oh, I should mention - each step can depend on other steps that must run first. E.g. `{'name': 'test', 'needs': ['compile']}`. The ordering has to respect that.

**Assistant:**
```python
def order_steps(steps):
    result = sorted(steps, key=lambda s: s['name'])
    for i, step in enumerate(result):
        for dep in step.get('needs', []):
            j = next(k for k, s in enumerate(result)
                     if s['name'] == dep)
            if j > i:
                result.insert(i, result.pop(j))
    return result
```

### Why it works as an illustration

- **Assumption made:** "This is a sorting problem" (alphabetical ordering)
- **What invalidates it:** Dependencies make this a **graph problem** (topological sort), not a sorting problem
- **How the model patches:** Keeps `sorted()` as the backbone, swaps items to fix violations. Breaks for transitive chains (A needs B needs C), diamond dependencies, cycles.
- **Why context causes this:** Given the full spec in one shot ("order build steps respecting dependencies"), any model immediately reaches for topological sort. The incremental reveal traps it in the sorting frame.

### Possible annotations
- Arrow on A1: "Commits to sorting-based approach"
- Arrow on A2: "Patches sorted list with swaps instead of switching to topological sort. Breaks for transitive dependencies."

---

## Candidate 2: Pizza problem - Per-group vs. combined total (MATH)

*Based on real gpt-5.2 failure: LazyGSM8K/1066*

### Setup
User asks how many pizzas are left. Info about two groups arrives incrementally.

### Conversation

**User:** How many pizzas are still left?

**Assistant:** I need more information. How many pizzas were there, and how many were eaten?

**User:** The glee club ordered 20 pizzas and ate 70% of them.

**Assistant:** 70% of 20 = 14 eaten. 20 - 14 = **6 pizzas are left.**

**...** *(assistant has committed to "6" as the answer)*

**User:** The football team also ordered twice as many pizzas and ate 80% of theirs.

**Assistant:** Football team ordered 2 x 20 = 40 pizzas. They ate 80% = 32. So the football team has **8 pizzas left.**

### Why it works as an illustration

- **Assumption made:** The question is about one group's pizzas. Model gives a complete answer (6) at turn 2.
- **What invalidates it:** A second group exists. "How many pizzas are left" means the *combined* total across all groups.
- **How the model patches:** Computes the new group in isolation (8) without revisiting the total. Reports 8 instead of 6+8=14.
- **Why context causes this:** The model already answered "6 pizzas are left" as a complete answer. The new info gets processed as a parallel sub-problem rather than triggering a revision of the original answer.

### Concerns
- Could read as "forgetting to combine" rather than "approach invalidation." The structural issue is subtle: the model frames it as two independent questions rather than one combined question.
- A reader might think "the user should have said everything upfront" (blaming the user).

### Possible improvements
- Reframe so the combined total is more clearly what was asked for. E.g., "How many pizzas are left *for the after-party*?" makes combination obviously required.
- Make the second group's info change the *computation* for the first group (not just add a parallel group).

---

## Candidate 3: Tomato growing - Individual vs. household demand (MATH)

*Based on real gpt-5.2 failure: LazyGSM8K/234*

### Setup
User asks how many tomato vines to plant. Initially seems like just one person's needs, then a second person's consumption is revealed.

### Conversation

**User:** How many vines does Steve need to grow his cherry tomatoes?

**Assistant:** I need to know how much he eats and how much each vine produces.

**User:** He eats 6 tomatoes a day. Each vine produces 3 tomatoes per week.

**Assistant:** 6/day x 7 = 42/week. 42 / 3 = **14 vines.**

**...** *(model has locked in 14 as the answer)*

**User:** Oh, and Steve eats twice as many tomatoes as his girlfriend.

**Assistant:** So his girlfriend eats 6 / 2 = 3 tomatoes per day. That's consistent with Steve eating twice as much.

### Why it works as an illustration

- **Assumption made:** "Steve's demand = total demand." Model computes 14 vines and treats the problem as solved.
- **What invalidates it:** The girlfriend also eats tomatoes from the same garden. Total demand is 6+3=9/day = 63/week. Need 63/3 = **21 vines.**
- **How the model patches:** Absorbs the girlfriend info as a *derived fact* ("she eats 3/day, consistent!") without recognizing it changes the total. The 14-vine answer is never revisited.
- **Why context causes this:** The model's "14 vines" answer is sitting in context as a completed solution. New info gets interpreted through the lens of "what does this add to what I already know" rather than "does this change my answer."

### Concerns
- Similar to pizza: could read as "forgetting to include" rather than approach invalidation.
- The girlfriend reveal is natural but the model's failure to add her demand feels like it should be obvious.

### Possible improvements
- Make the second person's consumption not simply additive but structurally change the computation. E.g., "they take turns eating from the garden on alternating weeks" or some constraint that changes how you calculate vine yield.

---

## Candidate 4: Direct lookup vs. graph search (CODE)

### Setup
User needs to check relationships between users. Initially direct, then transitive.

### Conversation

**User:** Write a function that checks if two users are friends.

**Assistant:**
```python
def are_connected(user_a, user_b, friends):
    return user_b in friends.get(user_a, [])
```

**...** *(possible clarifying turns)*

**User:** I need to know if they're connected through any chain of mutual friends, not just directly.

**Assistant:**
```python
def are_connected(user_a, user_b, friends):
    if user_b in friends.get(user_a, []):
        return True
    for friend in friends.get(user_a, []):
        if user_b in friends.get(friend, []):
            return True
    return False
```

### Why it works as an illustration

- **Assumption made:** "This is a lookup problem" (O(1) set membership)
- **What invalidates it:** Transitive connectivity requires **graph traversal** (BFS/DFS with visited set), a fundamentally different algorithm
- **How the model patches:** Extends the lookup one hop deeper (friends-of-friends) instead of switching to graph search. Misses paths of length 3+.
- **Why context causes this:** The "check membership in a list" pattern is anchored. Model extends it rather than replacing it.

### Concerns
- Requires some CS knowledge to appreciate (graph traversal vs. lookup).
- The friends-of-friends patch is a reasonable intermediate step; reader might think "just add more hops" rather than seeing the structural issue.

---

## Candidate 5: Flat rate vs. progressive brackets (MATH/CODE)

### Setup
User asks about tax calculation. Initially flat rate, then progressive.

### Conversation

**User:** Write a function that calculates income tax. The rate is 25%.

**Assistant:**
```python
def calc_tax(income):
    return income * 0.25
```

**User:** Sorry, it's actually a progressive tax: 10% on the first $50K, 25% on $50K-$100K, and 35% above $100K.

**Assistant:**
```python
def calc_tax(income):
    if income <= 50000:
        rate = 0.10
    elif income <= 100000:
        rate = 0.25
    else:
        rate = 0.35
    return income * rate
```

### Why it works as an illustration

- **Assumption made:** Tax is `income * rate` (one multiplication)
- **What invalidates it:** Progressive brackets require summing marginal contributions per bracket
- **How the model patches:** Selects the correct rate for the bracket but applies it to the *entire* income. For $120K: gives $42,000 instead of correct $24,500.
- **`income * rate` framework survives** when it should be replaced by bracket iteration.

### Concerns
- **Could read as a knowledge error** ("model doesn't understand progressive tax") rather than a context-anchoring error. This is the main weakness. A reader's takeaway might be about model capability, not conversation dynamics.

---

## Rankings and Notes

| # | Domain | Structural change | Context-caused? | Accessible? | Compact? |
|---|--------|-------------------|-----------------|-------------|----------|
| 1 | Code | Sort → topological sort | Very clear | CS audience yes | Yes (4 msgs) |
| 2 | Math | Per-group → combined | Moderate | Universal | Yes (6 msgs) |
| 3 | Math | Individual → household | Moderate | Universal | Needs trimming |
| 4 | Code | Lookup → graph BFS | Clear | CS audience | Yes (4 msgs) |
| 5 | Code/Math | Flat → progressive | Clear | Universal | Yes (4 msgs) |

**Current recommendation:** Candidate 1 (build steps) is the strongest overall. Clean structural invalidation, clearly context-caused, compact. If the audience skews less CS, Candidate 2 (pizza, improved version) is the most universally accessible.

**Open question:** Should we try to construct more candidates that blend math accessibility with code-level structural change? E.g., a word problem where the model sets up an equation structure that becomes fundamentally wrong.
