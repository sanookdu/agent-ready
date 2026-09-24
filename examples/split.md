# Two approved outcomes (synthetic)

Implement two separately approved changes in the community library service:
1. Replace password login with the approved passkey-only architecture. The owner
   has approved invalidating password sessions at cutover; the compatibility policy,
   enrollment/recovery design and authentication acceptance suite are frozen.
2. Add an opt-in reading-statistics report. Its consent policy, aggregates, report
   design and reporting acceptance suite are separately approved and frozen.

Both environments, datasets and authority are available. Neither result depends on
the other: the report uses an existing stable account-ID API. Reviewers may accept
passkey login and reject the report, or vice versa, without invalidating either
product decision. Delivering these in one work unit couples unrelated verdicts.
