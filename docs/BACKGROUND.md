# Background

This public project is a clean-room, provider-neutral implementation of a workflow pattern that was first explored in a private Windows work environment.

The original experiments validated the feasibility of:

- reading messages from a desktop mail client,
- extracting multiple `task` / `event` / `follow_up` candidates from one message with an LLM,
- preserving a missing deadline as `null` instead of inventing one,
- storing reply drafts for human review rather than auto-sending,
- creating and tracking calendar/task objects,
- using stable source identifiers to reduce duplicate processing.

No private endpoints, credentials, customer/company names, production data, or message contents are included in this repository.

The public repository focuses on the reusable architecture: **candidate generation -> approval -> execution adapter**.
