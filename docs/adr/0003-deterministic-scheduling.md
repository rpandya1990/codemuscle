# ADR 0003: Centralized deterministic spaced-repetition scheduling

## Status

Accepted

## Context

Users need explainable revision dates and mastery transitions. Outcomes, hint use, streak, difficulty,
confidence, priority, and manual overrides affect scheduling. Rules must be testable without AI or a DB.

## Decision

Put all scheduling logic in a pure policy receiving an explicit attempt date, current summary, problem
attributes, and configured successful intervals. Return a typed result with effective calculation date,
mastery, streak, factors, and explanation. Default intervals are `3,10,30,90,180,365` days.

Attempt creation stores the result and atomically updates the problem. A new attempt clears an older
manual date override. Manual overrides alter only the effective date and retain the latest calculated
date for audit and restoration.

## Alternatives considered

- **SM-2/Anki-compatible implementation:** established, but introduces ease-factor semantics and tuning
  not present in the product requirements.
- **AI-selected dates:** non-deterministic, difficult to test/explain, and violates offline core goals.
- **Rules in routes/components:** expedient initially but duplicates behavior and makes contracts drift.
- **Database triggers:** atomic but harder to test, version, explain, and reuse in simulations.

## Consequences

- Identical inputs yield identical results and property-based tests can assert invariants.
- Policy changes are explicit product changes and may alter future schedules, not historical attempts.
- Current modifiers only shorten intervals within documented bounds.
- Configuration is stored as validated user preferences and can later receive a settings UI.
