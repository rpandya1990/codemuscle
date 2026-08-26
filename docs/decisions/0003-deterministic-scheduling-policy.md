# 0003: Centralize deterministic revision scheduling

## Status

Accepted

## Decision

All mastery and revision-date calculations live in a pure scheduling policy. The policy receives
the attempt, current problem summary, and configured successful intervals and returns a typed result
containing the next date, mastery, streak, explanation, and factors.

Successful intervals default to `3, 10, 30, 90, 180, 365` days and are stored in user preferences.
Confidence, hard difficulty, and highest priority may shorten an interval, but never below one day.
Attempt recording applies the result atomically and clears an existing manual date override.

Manual overrides change only the effective next revision date. The latest calculated date remains
stored for auditability and can be restored explicitly.

## Consequences

- API routes and UI components contain no scheduling business logic.
- Identical inputs always produce identical results.
- Policy behavior can be tested without a database or web server.
- Future queue generation can consume the same persisted calculated and effective dates.
