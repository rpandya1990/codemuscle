# ADR 0001: Start as a modular monolith

- Status: Accepted
- Date: 2026-07-27

## Context

CodeMuscle needs clear API, application, domain, and infrastructure boundaries without the operational overhead of independently deployed services.

## Decision

Use one repository with a Next.js frontend and FastAPI backend. The backend will keep business rules in domain and application modules, accessed by thin HTTP routes. PostgreSQL is the single durable data store.

## Consequences

The application is straightforward to run locally and can be tested as one system. Internal boundaries must be maintained in code review because deployment boundaries do not enforce them.

