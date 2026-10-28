# Synthetic cloud operations dataset

Dataset name: `synthetic-cloud-ops-v1`.

All documents are wholly fictional and authored for this repository. They are
not copied internal runbooks and describe no real customers, people, incidents,
provider accounts, credentials, or deployed infrastructure. Service names and
operational details are invented. These examples are evaluation material, not
instructions for operating a real cloud environment.

`data/documents.json` contains fourteen documents in stable fixture order. Each
record has a stable `doc-NNN` ID, a title, a prose body, and a list of topic tags.
Keep existing IDs attached to their original subjects when editing the corpus;
do not regenerate or renumber IDs between runs.

| IDs | Subject |
| --- | --- |
| doc-001, doc-002 | Nimbus Queue backlog and retry amplification |
| doc-003, doc-004 | Atlas Ledger backup retention and restore rehearsal |
| doc-005, doc-006 | Service permissions and temporary emergency access |
| doc-007, doc-008 | Private routing and stale DNS resolution |
| doc-009, doc-010 | Transfer cost and idle compute cost anomalies |
| doc-011 | Application log retention |
| doc-012 | Cold-cache recovery |
| doc-013 | Replica lag response |
| doc-014 | Gateway packet queue saturation |

The fictional environment connects Prism API, Atlas Ledger, Nimbus Queue,
Helix Cache, Zephyr Gateway, Cinder Archive, and Orchid Compute. Shared service
names create context overlap without making every document relevant to every
question about that service.

Intentional distractors include **queue** (jobs versus packets), **retention**
(backups versus logs), **cache** (DNS versus application reads), and **cost**
(cross-zone transfers versus idle workers). Restore traffic also connects backup
rehearsals with transfer costs and gateway congestion. Different documents can
share vocabulary while prescribing different actions for different symptoms.

## Independent relevance judgments

`data/evaluation_queries.json` contains twelve authored questions with stable
`q-NNN` IDs and nonempty lists of relevant document IDs. These labels were
chosen by reading the corpus and reasoning about the requested information,
without executing retrieval or consulting ranked outputs. No ranking algorithm
was used to generate the gold sets. External operator review of these authored
judgments remains pending before publishing benchmark scores.

A document is relevant when it supplies substantive guidance requested by the
question. Shared keywords, service mentions, or a referral to another document
alone do not qualify. Gold lists are sets of relevance targets, not a desired
ranking order. The two compound questions deliberately require guidance from
multiple documents.

| Query | Relevant documents | Authored rationale and distractor distinction |
| --- | --- | --- |
| q-001 | doc-001, doc-002 | The backlog runbook explains arrival/completion rates and heartbeats; the retry incident explains backoff, attempt limits, and deduplication. Both parts are requested. doc-014 concerns packet queues rather than job processing. |
| q-002 | doc-003, doc-004 | The policy supplies daily/weekly snapshot retention; the rehearsal runbook supplies isolation, manifest comparisons, and cleanup. doc-011 governs logs, and doc-009 addresses restore transfer cost rather than verification. |
| q-003 | doc-005 | The identity guidance defines summary-only access, separation of release privileges, and denied-action/resource inspection. doc-006 handles temporary operator access. doc-012 only refers authorization failures elsewhere. |
| q-004 | doc-006 | The temporary role procedure covers approval, purpose, expiration, early revocation, audit, and review. Routine Prism API permissions in doc-005 do not supply that emergency lifecycle. |
| q-005 | doc-007 | The route runbook supplies forward/return-path and firewall checks after name resolution succeeds. doc-008 instead addresses stale DNS, while doc-014 addresses demonstrated packet congestion. |
| q-006 | doc-008 | The resolver incident supplies pool comparison, cache expiration correction, and targeted refresh. Helix application cache guidance in doc-012 addresses read load, not expired DNS answers. |
| q-007 | doc-009 | The cost anomaly explains repeated cross-zone copies, reader placement, scratch-copy reuse, and preserving retention. doc-010 concerns idle compute; doc-004 explains restore integrity rather than transfer cost reduction. |
| q-008 | doc-010 | The compute runbook identifies minimum-capacity overrides and compares allocated/busy hours with schedules, with a backlog guard before reducing capacity. doc-009 concerns transfer fees. |
| q-009 | doc-011 | The log policy states seven-day retention and excludes request bodies and access tokens. Snapshot retention in doc-003 is a different policy for different data. |
| q-010 | doc-012 | The cold-cache runbook prescribes warming frequent summary keys and capping concurrent misses. doc-008 concerns resolver caches, and doc-013 concerns replica apply throughput. |
| q-011 | doc-013 | The lag runbook compares write/apply throughput, checks storage pressure, and moves freshness-sensitive reads to the primary. doc-001 measures job backlog rather than replica lag. |
| q-012 | doc-014 | The gateway incident prescribes limiting archive copy concurrency and moving bulk rehearsals outside request peaks. doc-007 diagnoses routes, doc-001 handles jobs, and doc-009 targets transfer charges rather than packet drops. |

Fixture tests check structure, references, and stable identity; they make no
claim about BM25 ranking quality. No benchmark scores are supplied. JSON
parsing, dataset review, and all execution-based checks remain unperformed at
authoring time.
