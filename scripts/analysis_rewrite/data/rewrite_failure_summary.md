# Rewrite failure-mode aggregation

Total labeled cases: 48

## Primary-category distribution

| Task | F1 | F2 | F3 | F4 | F5 | F6 | F7 | ERR | Total |
|---|---|---|---|---|---|---|---|---|---|
| actions | 9 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 12 |
| code | 1 | 1 | 0 | 6 | 4 | 0 | 0 | 0 | 12 |
| database | 0 | 0 | 0 | 10 | 1 | 0 | 1 | 0 | 12 |
| math | 1 | 8 | 0 | 3 | 0 | 0 | 0 | 0 | 12 |
| **All** | 11 | 9 | 0 | 21 | 5 | 0 | 2 | 0 | 48 |

## Secondary-category counts (per failure case can list multiple)

| Code | Count |
|---|---|
| F5 | 13 |
| F1 | 6 |
| F4 | 4 |
| F3 | 3 |

## Top co-occurrences (primary + secondary)

- F4 ⨯ F5: 13
- F1 ⨯ F4: 4
- F1 ⨯ F5: 3
- F2 ⨯ F4: 2
- F2 ⨯ F3: 2
- F1 ⨯ F2: 1
- F3 ⨯ F4: 1

## Illustrative rationales by category

### F1
- [actions / sharded-BFCL/parallel_53] Rewrite's compaction omitted the meta-requirement to re-emit all function calls from the entire conversation, causing the assistant to only return the new Caesar Salad call.
- [actions / sharded-BFCL/parallel_80] The compaction lost the meta-level requirement to re-emit the complete set of function calls for all requests so far, causing the assistant to output only the new call.
- [actions / sharded-BFCL/parallel_80] The compaction lost the meta-requirement to output both GCD calls together, causing the assistant to only return the call for Mary's numbers.

### F2
- [math / sharded-GSM8K/144] The compaction preserved the assistant's erroneous calculation of revenue per client ($30.67) and projected total revenue for 8 clients, which incorrectly assumed all clients pay t
- [math / sharded-GSM8K/1166] The compaction incorrectly computed Year 8 as 800 fruits (1000-200) instead of deriving it from the 10-year-old tree's actual production, and presented this wrong value as establis
- [math / sharded-GSM8K/1066] The compaction preserved the premature calculation that the football team ordered 40 pizzas (2 × 20), but the correct interpretation is that the football team ordered twice as many

### F4
- [code / sharded-livecodebench/2977] Rewrite's compaction incorrectly required a subsequence of words (skipping allowed) instead of matching each word in order without skipping, as the correct solution does.
- [math / sharded-GSM8K/543] Rewrite's compaction added a phantom requirement to output in cents (600) instead of dollars ($6), contradicting the system prompt's instruction to write only the number with no un
- [database / sharded-spider-val-932-medium] Rewrite added extra fields (last_name, email_address, role_code) to the required output that the user never asked for, causing the assistant to include them in the query.

### F5
- [code / sharded-livecodebench/2866] The compaction dropped the requirement to return the subarray itself (not length) and added a phantom threshold parameter, causing the assistant to produce a function that returns 
- [code / sharded-livecodebench/2816] The compaction dropped the requirement to return a tuple (palindrome, changes) and instead the assistant produced only the palindrome string.
- [database / sharded-spider-val-257-hard] The compaction dropped the user's explicit request for airport names, leading the assistant to select all columns instead of just the name.

### F7
- [actions / sharded-BFCL/parallel_199] JSON parse error
- [database / sharded-spider-val-942-medium] JSON parse error
