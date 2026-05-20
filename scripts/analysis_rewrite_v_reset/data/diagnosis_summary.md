# Rewrite vs Reset — diagnosed failure attribution

**Sample**: 48 pairs, balanced across tasks.

## Spec-divergence distribution (Rewrite vs Reset)

| Kind | n |
|---|---|
| phantom_added | 20 |
| phantom_dropped | 17 |
| equivalent | 8 |
| vaguer | 2 |
| more_specific | 1 |

## Spec-divergence by task

| Task | vaguer | more_specific | phantom_added | phantom_dropped | format_lost | equivalent |
|---|---|---|---|---|---|---|
| actions | 1 | 0 | 1 | 8 | 0 | 2 |
| code | 0 | 0 | 7 | 4 | 0 | 1 |
| database | 0 | 0 | 8 | 1 | 0 | 3 |
| math | 1 | 1 | 4 | 4 | 0 | 2 |

## Work-so-far divergence flags

| Task | inlines_verbatim_code | inlines_numerical_speculation | omits_important_caveat |
|---|---|---|---|
| actions | 4 | 0 | 9 |
| code | 9 | 0 | 8 |
| database | 7 | 0 | 2 |
| math | 1 | 3 | 9 |

## Primary failure cause

| Cause | n |
|---|---|
| spec_divergence | 28 |
| work_so_far_divergence | 18 |
| other | 2 |

## Primary cause by task

| Task | spec_divergence | work_so_far_divergence | both | other |
|---|---|---|---|---|
| actions | 5 | 7 | 0 | 0 |
| code | 8 | 4 | 0 | 0 |
| database | 7 | 3 | 0 | 2 |
| math | 8 | 4 | 0 | 0 |

## Rewrite-input attribution (which input to the rewrite operation drove the error)

| Attribution | n |
|---|---|
| rewriter_hallucination | 30 |
| analyzer_output | 13 |
| rewrite_prompt | 3 |
| conversation | 2 |

Mean labeler confidence: 0.95, min 0.85, max 1.00
