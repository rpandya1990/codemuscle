# ADR 0005: Deterministic weak-area classification

## Status

Accepted

## Context

The dashboard must identify weak and neglected topics without opaque heuristics or AI. Results need
stable explanations and must be reusable by future queue scoring and summaries.

## Decision

Calculate statistics from active problems and immutable attempts in an application service, then pass
rates and dates into a pure classification policy. Classify no-history or 30-day inactivity as
`NEGLECTED`; with at least three attempts classify independent success below 50% or failures at least
35% as `WEAK`; with at least four attempts classify a 20-point recent improvement as `IMPROVING`;
otherwise classify `STABLE`.

Split ordered attempts into older and recent halves for trend comparison. Return classification reasons
with every result. Produce explicit zero-value weekly trend buckets.

## Alternatives considered

- **AI classification:** opaque, non-deterministic, unnecessary, and unavailable offline.
- **Mastery state alone:** loses area-level rates, inactivity, and trend information.
- **SQL views/materialized aggregates:** efficient at scale but complicate iteration and invalidation
  before the local data volume warrants them.
- **Configurable thresholds immediately:** flexible but adds settings/UI complexity without validated
  user demand; central constants/policy keep a future change localized.

## Consequences

- Classifications are reproducible, explainable, and unit-testable.
- Current aggregation runs in application memory and is appropriate for the expected ≤5,000 problems.
- Threshold changes are product behavior changes and require tests and documentation updates.
- Queue scoring may later consume classifications without duplicating threshold logic.
