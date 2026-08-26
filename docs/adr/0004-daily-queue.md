# ADR 0004: Persist explainable, time-bounded daily queues

## Status

Accepted

## Context

A daily revision plan must prioritize risk, fit available time, diversify topics, explain every item,
and support user edits. Recalculating old queues would erase why a recommendation was shown.

## Decision

Use a centralized deterministic scoring policy and greedy time fitter. Score overdue dates, previous
failure, fragile/relearning mastery, due-today status, priority, and neglect. Use explicit duration
defaults by difficulty. Prefer unused topics first, then fill remaining capacity by score without
exceeding the time budget. Overdue and failed problems keep their score bonuses but receive no
special pass that bypasses topic diversity.

Persist queue sessions and item snapshots including duration, score, reasons, position, and status.
Remove/postpone/complete mutate status instead of deleting history. Replacement selects the best
currently non-queued candidate. Postpone creates a visible one-day manual date override.

## Alternatives considered

- **Dynamic queue computed on every view:** always current but destroys historical reasons and user edits.
- **Integer/linear optimization:** can fit time more tightly, but adds dependency and complexity before
  evidence that greedy selection is inadequate.
- **Random diversity:** varied output but violates determinism and reproducibility.
- **AI recommendations:** opaque and unnecessary for measurable factors.

## Consequences

- Queue history remains reviewable even as problem state changes.
- Equal inputs and state produce stable ordering with explicit tie-breakers.
- Some time may remain unused when no candidate fits; the budget is never exceeded.
- Weak-topic scoring can be added after deterministic statistics exist without replacing persistence.
