# Retrieval metrics

The implementation compares ordered retrieved document IDs with independently
authored gold document IDs. It never infers relevance from shared words, BM25
scores, or predictions. The gold set must be nonempty and unique. Retrieved IDs
must also be unique, including beyond the cutoff; invalid duplicates are rejected
rather than silently changing denominators. k must be a positive integer,
excluding booleans; the application retrieval/evaluation interfaces limit k to 20.

Let G be the gold set, R the ranked list, and H the count of unique members of G
among the first k entries of R. Rank positions start at 1.

| Metric | Definition | Short or no-hit rankings |
| --- | --- | --- |
| Precision@K | H / k | Denominator remains k even when fewer results exist. No hits gives 0.0. |
| Recall@K | H / size(G) | Gold documents not returned remain in the denominator. No hits gives 0.0. |
| RR@K | 1 / first relevant rank within the first k results | Returns 0.0 if no relevant document is found within the cutoff. |

For a hand-worked illustration, let G={a,b}, R=[x,a], and k=3. Precision is
1/3, recall is 1/2, and reciprocal rank is 1/2. These are arithmetic examples,
not observed scores for the repository dataset. A relevant document at rank 4
does not count when k=3. Retrieval does not pad missing results with zero-score
documents.

## Batch aggregation

Macro Precision@K and macro Recall@K are arithmetic means of the corresponding
per-query values over **all** evaluation queries. MRR@K is the arithmetic mean
of RR@K over those same queries. Zero-hit queries contribute zeros and remain in
every mean. Each query has equal weight, including queries with larger gold sets;
these are not pooled hit-count ratios or averages over successful queries only.
An empty evaluation set is rejected. Retrieval errors abort evaluation rather
than silently becoming artificial no-hit rows.

Reports retain raw finite floats and contain no timestamps or inferred relevance
labels. BM25 uses k1=1.5 and b=0.75, positive smoothed IDF, equally weighted title
and body terms, unique query terms, and document-ID ordering for exact ties.
ASCII tokens are extracted with `[a-z0-9]+` after Python lowercasing; this is not
multilingual segmentation. Scores are not calibrated confidence values.

## Limits of interpretation

The [dataset](DATASET.md) is small and wholly fictional. Its independent labels
are explicit authored judgments, not universal relevance truth. Review their
suitability for your evaluation; overlapping vocabulary can produce plausible
distractors.
Binary relevance metrics do not measure answer accuracy, grounding, completeness,
operational safety, or resistance to arbitrary prompt injection. The application
does not call a model or generate answers.

Metric formulas, aggregation, and CLI/API output parity have passed verification.
Report dataset metric values from actual evaluation output with the evaluated
version and configuration. Passing implementation checks and toy arithmetic
examples do not establish real-world retrieval quality. See
[validation](VALIDATION.md) to reproduce the checks.
