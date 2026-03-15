# Migration From `waterfall-gtm`

This repo is being rebuilt from selected reusable parts of `waterfall-gtm`.

Ported into `open-waterfall`:

- models
- provider abstraction
- provider registry and concrete provider ports
- waterfall processor
- config loading
- checkpoint, cost tracking, rate limiting
- scoring and persona classification
- research modules
- messaging/outbound strategies
- CSV sink
- HubSpot sink split into `crm.py`, `dedupe.py`, and `workflow.py`

Kept out or intentionally narrowed:

- private operator notes and campaign artifacts
- company-specific defaults
- downstream private CRM setup details
- personal sender or owner IDs

Design changes from the source repo:

- CLI responsibilities are split into focused commands instead of a single orchestration entrypoint.
- HubSpot is isolated behind optional sink modules and an optional dependency.
- Shared CSV lead hydration is centralized so `score`, `message`, and `sync` operate on the same object model.
