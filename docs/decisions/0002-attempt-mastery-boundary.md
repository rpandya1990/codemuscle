# 0002: Keep initial attempt mastery separate from interval scheduling

## Status

Accepted

## Decision

Milestone 4 records attempts atomically and applies a small deterministic mastery policy based on
outcome and successful streak. It assigns a one-day follow-up so every attempt retains the audit
fields required by the existing schema.

The configurable interval selection, bounded modifiers, manual overrides, and detailed scheduling
explanations remain the responsibility of the Milestone 5 scheduling service. The attempt service
will delegate to that service when it is introduced.

## Consequences

- Attempt history and summary counters are usable before the full scheduler exists.
- No scheduling policy is duplicated in UI or API routes.
- The temporary one-day follow-up is explicit in the stored explanation and can be replaced behind
  the application-service boundary in Milestone 5.
