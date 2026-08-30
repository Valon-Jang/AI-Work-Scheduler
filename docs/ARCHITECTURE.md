# Architecture

AI Work Scheduler separates **candidate generation** from **state-changing execution**.

```text
Message Adapter
    -> preprocessing
    -> AI / rule extractor
    -> Candidate Action 1:N
    -> local persistence + idempotency
    -> human review
    -> approved action
    -> optional Calendar / Task / Reply adapter
```

## Core invariants

1. A message and its actions are different objects.
2. One message can create zero, one, or many actions.
3. AI output is a candidate, never an automatic commitment.
4. Missing dates stay missing; the extractor must not invent deadlines.
5. Original date/time wording is preserved in `date_text` / `start_text`.
6. Reprocessing the same source/action should not create duplicates.
7. An action cannot be marked executed before it is approved.
8. Provider integrations are adapters, not part of the decision model.

## Action semantics

- `task`: work the user should perform now.
- `follow_up`: a later check after waiting for another person/system.
- `event`: a scheduled calendar event.
- `ignore`: no action should be created.

## Why SQLite

The public core uses SQLite because it provides a small local transactional store and makes idempotency/status transitions inspectable without a server.

## Provider adapters

The public v0.1 deliberately does **not** include private mail, calendar, or AI credentials and does not assume a specific provider. A provider adapter can be added later for Outlook, Gmail, Google Calendar, local task systems, or an OpenAI-compatible model endpoint.
