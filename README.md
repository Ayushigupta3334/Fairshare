# FairShare

A tool for tracking a group gift pool: equal fair shares, live balances, and a minimal settle-up plan — styled like a bank passbook ledger. Python (Flask) backend, SQLite storage, plain HTML/CSS/JS frontend.

It answers the three questions an organiser always gets asked:
- **How much do I still owe?** → Statement summary, per person.
- **Have we collected enough yet?** → Pool status strip (collected / target / remaining).
- **Who pays whom?** → Settlement slip, fewest possible transactions.

## Tech stack

- **Backend:** Python 3 + Flask, exposing a small JSON API
- **Storage:** SQLite (`chipin.db`, created automatically — no setup step)
- **Business logic:** pure Python in `settlement.py`, deliberately kept separate from Flask/SQLite so it's unit-testable in isolation
- **Frontend:** plain HTML/CSS/JS, no build step, no framework — it just calls the API and renders the response
- **Tests:** pytest, covering the fair-share, balance, and settlement math

## Project structure

```
.
├── app.py                    # Flask routes / JSON API
├── database.py                # SQLite schema + connection helpers
├── settlement.py               # fair share, balances, settlement algorithm (pure functions)
├── templates/
│   └── index.html             # page structure
├── static/
│   ├── style.css               # passbook/ledger styling
│   └── app.js                  # fetches the API, renders the passbook
├── tests/
│   └── test_settlement.py     # pytest unit tests for settlement.py
├── .devcontainer/
│   └── devcontainer.json      # GitHub Codespaces config
├── requirements.txt
├── .gitignore
├── README.md
├── REASONING.md
└── AI_LOGS.md
```

## Running it in GitHub Codespaces

1. Push this repo to GitHub.
2. Click **Code → Codespaces → Create codespace on main**.
3. The devcontainer installs `requirements.txt` automatically on first build (`postCreateCommand`). Wait for that to finish (check the terminal).
4. Run the app:
   ```bash
   python app.py
   ```
5. Codespaces will pop up a "port forwarded" notification for port 5000 (it's also configured to auto-open a preview) — open it, or use the **Ports** tab.

## Running it locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Then open **http://localhost:5000**.

## Running the tests

```bash
pip install -r requirements.txt   # includes pytest
pytest -v
```
`tests/test_settlement.py` exercises the fair-share, balance, and settlement math directly — including the exact "one person overpays to cover another, two people haven't paid" scenario from the brief — with no server or database needed.

## Using it

1. **Cover** — name the gift, set the target amount (defaults to ₹6,000), note who's holding the pool. Saved automatically as you type.
2. **Account holders** — add everyone chipping in. The fair share (target ÷ headcount) updates live.
3. **Transactions** — record each payment: who paid, how much, optional note (e.g. "covering for Riya too"). Partial payments are just smaller entries; add as many as you like per person.
4. **Pool status** — total collected, how much is still needed, current per-head fair share.
5. **Statement summary** — each person's fair share, what they've actually paid, and their balance (owes / settled / is owed).
6. **Settlement slip** — the smallest set of "A pays B ₹X" instructions so everyone ends up even. All the splitting math runs server-side in `settlement.py`; the frontend just displays it.

**Editing in place:** click any name to rename it, or click any transaction amount to correct it (amount and note) without deleting and re-adding — useful for fixing a typo without losing the entry's position in the ledger. Remove a person or a transaction with the `×` next to it. "Reset all data" in the footer wipes the database back to empty (with a confirmation prompt).

**On mobile:** inputs are sized to avoid iOS auto-zoom on focus, and the transaction/summary tables switch to a stacked card layout below 600px so nothing gets cramped into unreadable columns.

**Adding a logo:** drop an image at `static/images/logo.png` and it appears automatically at the top of the cover — no code change needed. If the file isn't there, the app just runs without one.

## API reference

| Method | Endpoint | Body | Purpose |
|---|---|---|---|
| GET | `/api/state` | — | Everything: settings, members, payments, computed balances, pool status, settlement plan |
| POST | `/api/settings` | `{pool_name, target, organiser}` | Update the pool's name/target/organiser |
| POST | `/api/members` | `{name}` | Add a person |
| PATCH | `/api/members/<id>` | `{name}` | Rename a person |
| DELETE | `/api/members/<id>` | — | Remove a person (and their payments) |
| POST | `/api/payments` | `{member_id, amount, note?}` | Record a payment |
| PATCH | `/api/payments/<id>` | `{amount, note?}` | Correct a payment in place |
| DELETE | `/api/payments/<id>` | — | Remove a payment entry |
| POST | `/api/reset` | — | Wipe all data |

## Debugging

- **`ModuleNotFoundError: No module named 'flask'`** → you haven't installed `requirements.txt` in this environment yet (see "Running it locally"/"in Codespaces" above).
- **Port 5000 already in use** → another process is bound to it; either stop it or run `flask run --port 5050` / edit the port in `app.py`'s `app.run(...)` call.
- **Changes to `.py` files don't show up** → Flask's debug reloader (`debug=True` in `app.py`) watches files and restarts automatically; check the terminal for a "Restarting with watchdog" line. If it's stuck, stop (`Ctrl+C`) and rerun `python app.py`.
- **Changes to `static/` files don't show up** → hard-refresh the browser (`Ctrl/Cmd+Shift+R`); static files are cached by the browser, not by Flask.
- **Data looks wrong / want a clean slate** → either click "reset all data" in the app, or stop the server and delete `chipin.db` (it's recreated empty on next run — it's git-ignored on purpose, so it never gets committed).
- **Want to inspect the database directly** → `sqlite3 chipin.db` then `.tables`, `SELECT * FROM payments;`, etc.
- **Settlement numbers look surprising** → see the "Why settlement can leave money 'unassigned'" note in `REASONING.md`: if the pool isn't fully collected yet, part of what someone owes is owed *to the pool*, not to a teammate, and correctly won't appear as a peer-to-peer instruction — it shows up in "still to collect" instead.

## Design notes

The visual language is a bank passbook / ledger register rather than a generic dashboard — ruled paper, a navy-and-gold cover, monospace figures for alignment — because the subject (an informal Indian group collection) is close to that everyday object. Full reasoning, including why the backend is split the way it is, is in `REASONING.md`.
