# AI Work Scheduler

<p align="center">
  <img src="docs/assets/app-icon.png" alt="AI Work Scheduler icon" width="160">
</p>

A review-first workflow core that turns messages into **candidate tasks, events, and follow-ups** without letting the AI silently commit actions on your behalf.

[한국어 README](README_KO.md)

## Why

Messages often contain several different kinds of work at once: something to do, a meeting to attend, and something to check again later. A useful AI scheduler needs more than extraction — it needs boundaries.

AI Work Scheduler keeps those boundaries explicit:

- Message and Action are separate objects
- one Message can create multiple Actions (`1:N`)
- AI output is always a **candidate** first
- missing dates remain `null`; the AI must not invent deadlines
- original date/time wording is preserved for review
- duplicate processing is blocked with stable idempotency keys
- execution requires explicit approval
- mail/calendar/task providers are adapters, not hard-coded assumptions

This public version contains no company, customer, private endpoint, credential, or production message data.

## Windows installer

[Download Cloud PC Outlook Scheduler v2.2.2](releases/CloudPCScheduler_Setup_v2.2.2.exe)

- Requires Windows and desktop Outlook.
- Configure your own AI endpoint, model, and API key after installation.
- Contains no company name, private URL, corporate email, or meeting-room booking/check-in/cancellation feature.
- SHA-256: `A615F0DBC15E8ECBFF34D4A6CBA45D25B568453A9B220C5E36718EE19485DDF3`

## Workflow

```text
Message
  -> preprocessing
  -> AI / rule extraction
  -> Candidate Action 1:N
  -> SQLite + idempotency
  -> human review
  -> approved action
  -> optional execution adapter
```

The public v0.1 implements the reusable middle of that pipeline. It does **not** auto-send mail or modify a calendar.

## Quick start

Python 3.10+; runtime uses only the standard library.

```bash
python -m ai_work_scheduler --db demo.db prompt examples/message.json
```

That prints a structured extraction payload you can pass to an AI model.

For the included synthetic example, a model-like JSON response is already provided:

```bash
python -m ai_work_scheduler --db demo.db ingest \
  examples/message.json examples/model_output.json

python -m ai_work_scheduler --db demo.db list
```

Approve a candidate:

```bash
python -m ai_work_scheduler --db demo.db approve 1
```

Only an approved action can later be marked executed:

```bash
python -m ai_work_scheduler --db demo.db execute 1
```

## Action model

| Type | Meaning |
| --- | --- |
| `task` | Work the user should perform now |
| `event` | A scheduled calendar event |
| `follow_up` | A later check after waiting for another person/system |
| `ignore` | No actionable work |

A single source message may produce any number of candidates.

## AI contract

The prompt builder instructs the extractor to:

- return JSON
- preserve source date/time wording
- use `null` when no date exists
- never treat extraction as approval/execution
- prefer `task` when the user must act now
- use `follow_up` when the user is waiting on someone/something else
- merge sequential/conditional steps that serve one objective

The core parser validates the returned action types and de-duplicates exact semantic repeats.

## Reprocessing safety

Messages use a stable `source_id`. Candidate actions derive an idempotency key from:

```text
source_id + type + normalized title + date_text + start_text
```

Re-ingesting the same candidate does not create another row.

## Reply history

A conservative preprocessing helper can split a newest message from common quoted reply headers. If the newest text is very short, one previous message can be included as context.

This is intentionally a heuristic, not a claim that every mail client/locale is fully supported.

## Repository structure

```text
ai_work_scheduler/   core models, extraction contract, SQLite state, CLI
examples/            synthetic message + synthetic AI output
tests/               regression tests
docs/                architecture and sanitized background
.github/workflows/   CI across Python 3.10-3.13
```

## Test

```bash
python -m unittest discover -s tests -v
```

CI also verifies the module CLI and the installed `ai-work-scheduler` command.

## Scope

### Included in v0.1

- provider-neutral Message model
- Task / Event / Follow-up / Ignore candidates
- `Message : Action = 1:N`
- extraction prompt/JSON contract
- date-text preservation rule
- conservative reply-history preprocessing
- SQLite persistence
- idempotent re-ingestion
- Candidate -> Approved/Rejected/Held -> Executed state control
- CLI and synthetic examples

### Not yet included

- Outlook / Gmail collectors
- Calendar provider adapters
- task-system adapters
- reply-draft adapters
- direct LLM API adapter
- GUI approval inbox
- automatic date normalization
- background polling

Those are extension points, not claims about the current public implementation.

## Design principle

**AI proposes. The system remembers. The human approves. Adapters execute.**

See [Architecture](docs/ARCHITECTURE.md) and [Background](docs/BACKGROUND.md).
