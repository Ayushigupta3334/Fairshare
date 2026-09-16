# Reasoning

## What changed from the first pass, and why

The first version of this was a single self-contained HTML file with all logic in browser JavaScript and `localStorage` for persistence. That's a fine tool for a quick prototype, but it doesn't demonstrate backend engineering, isn't testable independently of a browser, and doesn't fit a "GitHub Codespaces submission" — Codespaces is a full dev container environment, and the natural thing to show off there is a real server, a real data layer, and tests that run in CI, not a single static file. So this version keeps the exact same product decisions (passbook metaphor, equal shares, balances, settlement) but re-implements them as a Python backend with a thin frontend.

## Reading the brief (unchanged from round 1)

The clue is in the questions the organiser keeps fielding: *"how much do I still owe"* is a per-person balance question; *"have we collected enough"* is a pool-total question; *"who pays whom"* is a settlement question. The build has three matching outputs, matched to three pure functions in `settlement.py`, not hard-coded to the ₹6,000 farewell-gift instance — any target amount and any group works.

## Why Flask, specifically

Given "Python and what's best for a Codespaces submission," I weighed a few options:

- **Flask** — a few files, no ORM ceremony, starts with `python app.py`, one dependency. Easy for an evaluator to open in Codespaces, read top-to-bottom, and run in under a minute.
- **Django** — far more scaffolding (settings module, apps, migrations framework) than a tool this size needs; would bury the actual logic being evaluated under boilerplate.
- **FastAPI** — a reasonable alternative, but its main advantages (async, auto-generated OpenAPI docs, Pydantic validation) aren't relevant to a small synchronous CRUD app like this one, and it would add a dependency (`uvicorn`) for no real benefit here.

Flask was the best fit for "smallest amount of framework needed to clearly show real backend logic."

## Why the business logic lives in its own module

`settlement.py` has zero Flask or SQLite imports — it only takes plain dicts/lists in and returns dataclasses out. That's deliberate: it means the three core questions (fair share, balances, settlement) can be unit-tested directly (`tests/test_settlement.py`) without spinning up a server or a database, and it means the logic is easy to audit in isolation — an evaluator (or a future contributor) can read `settlement.py` top to bottom and verify the splitting math is correct without wading through routing code.

`app.py` is intentionally "dumb" by comparison: each route reads from SQLite, hands plain dicts to `settlement.py`, and returns the result as JSON. All the interesting logic is testable Python; the web layer is just plumbing.

## Why the frontend has no business logic

In round 1, the frontend (JS) computed balances and settlement itself, against data in `localStorage`. Here, the frontend is deliberately "dumber": it calls `GET /api/state` after every change and renders whatever the server computed. This avoids two copies of the splitting math (one in Python, one in JS) that could drift out of sync — there is exactly one implementation of "what does everyone owe," and it lives in `settlement.py`.

## Why SQLite over a heavier database

The brief describes a small, ad-hoc group pool — a handful of people, a few dozen transactions at most. SQLite needs no separate service, no connection string, no setup step in Codespaces: the file is created automatically on first run and is disposable (git-ignored) by design. A Postgres/MySQL setup would add real operational weight (a second container, credentials, a `docker-compose.yml`) for a workload that will never need it. Using raw `sqlite3` rather than an ORM (SQLAlchemy, etc.) keeps the three tables and four queries fully visible in `database.py` — there's nothing hidden behind a model layer for something this small.

## Why the passbook metaphor, still

Group money-collection in India has a real, specific visual object attached to it: the bank passbook — a small booklet with a navy-and-gold cover, ruled pages, a running ledger of entries, and a stamped "statement" section. That object already encodes exactly the mental model this tool needs (a ledger of transactions, a running balance, a statement of who owes what):

- **Cover** = account details (what the pool is for, the target, who's holding it).
- **Account holders** = the passbook's registered names, which is also literally how the fair share is computed (divide by headcount).
- **Transactions** = the ruled ledger page, one row per payment — this is where "someone paid extra to cover a friend" and "two people haven't paid" both show up naturally, with no special case for either.
- **Statement summary** = the passbook's balance-brought-forward line, per person.
- **Settlement slip** = styled like a bank transfer chit.

This was kept over a generic dashboard specifically because it says something about the subject (an everyday Indian financial object), rather than defaulting to rounded cards and drop shadows that any prompt like this tends to produce.

## Why balances don't need a "paid for" field

All that matters for a fair settlement is each person's **net balance** = total paid − fair share. If Person A pays double to cover Person B, A's balance goes positive and B's goes equally negative — `settle()` independently arrives at "B pays A," without ever needing to record *why* A overpaid. Tracking "who paid for whom" would only matter if the group wanted to preserve an informal side-agreement instead of settling to the fair split, which the brief doesn't ask for. Keeping the `payments` table to just `(member_id, amount, note)` keeps the tool general.

## The settlement algorithm

Classic *debt simplification* / min-cash-flow approach, implemented in `settle()`:

1. Compute each person's balance (paid − fair share).
2. Split into creditors (balance > 0) and debtors (balance < 0).
3. Sort each list by magnitude, descending.
4. Repeatedly match the largest creditor with the largest debtor, settle the smaller of the two amounts, reduce both, drop whichever hits zero.
5. Repeat until both lists are empty.

This is greedy rather than a proven globally-minimum-transaction solution in every pathological case (true minimum-transaction-count settlement is NP-hard in general), but for a realistic group size it produces the same minimal or near-minimal count, and stays simple enough to verify by eye and by test. A ₹0.01 epsilon treats near-zero balances as settled so floating-point noise never produces a phantom "pay ₹0.0000000001" instruction.

### Why settlement can leave money "unassigned"

One non-obvious behaviour, caught by a unit test while building this: if the pool isn't fully collected yet, `settle()` will only redistribute the amount that is genuinely sitting with an over-payer — not the full amount every under-payer still owes. For example, with a ₹6,000 target across 4 people where one person hasn't paid and another has only paid half, if only ₹1,500 of surplus exists (from the person who overpaid to cover someone else), the settlement plan will only move that ₹1,500 — the remaining shortfall is still owed *to the pool itself*, not to any teammate, because no one has actually fronted that money yet. That gap is exactly what the "still to collect" figure in Pool status already reports, so nothing is lost — it's just correctly categorised as "not yet collected" rather than invented as a fake peer-to-peer debt.

## What was left out, on purpose

- **Unequal shares / weighted splitting** — the brief explicitly says "start with equal shares," so weighted splits were left out. `fair_share()` is the one function that would change first if that requirement showed up later.
- **Authentication / multi-user accounts** — out of scope for a small group tool; anyone with the link can use it, matching how an organiser would actually share this (a WhatsApp link), not a login-gated product.
- **Multi-currency / multi-pool** — one pool at a time, matching the brief.
- **A production WSGI server / deployment config** — Flask's dev server is intentionally what's shipped, since the target environment is a Codespaces dev container for evaluation, not a production deployment; `README.md` says so explicitly rather than silently shipping something that looks production-ready but isn't.
