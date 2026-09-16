ROUND 2  ·  BUILD ROUND
Chipping in for the farewell gift
The team is buying a farewell gift for their manager — budget ₹6,000. Everyone agreed to chip in equally, but in practice it’s chaos: some have paid their full share, a few paid only part, one generous soul paid extra to cover a friend, and two people haven’t paid at all. The organiser is constantly asked ‘how much do I still owe?’ and ‘have we collected enough yet?’ At the end the organiser just wants the simplest list of who should pay whom so everyone lands on their fair share.
Build something so the organiser can track the pool and settle up fairly.
(The questions the organiser keeps fielding are your clues — and build for any pool and organiser, not just this one. The easier you make it to see shares, balances and what’s left to collect, the better. Start with equal shares and simple balances, then settlements.)

this is one of the assignment i have given that you have to make think uniquely and creatively with these rules are given below with the idea of creating a simple ui that is easy to use and understand. And all the mention point must be come within.
The final solution must be a public GitHub repository, and its root folder must contain the following three files, which are required for evaluation:
- README.md — instructions for project setup, running, and debugging.
- REASONING.md — an explanation of the thought process behind the solution.
- AI_LOGS.md — a complete copy of the candidate's conversation with the AI tool (Copilot or any other). This log must be pasted as-is and not modified in any way; any alteration will lead to a deduction of marks

Perfect — that works just as well. Now let's get it running.

Step 1: Double-check the upload went cleanly
On your repo's GitHub page, confirm you see this exact structure (click into folders to check they're not empty):

.devcontainer/
  devcontainer.json
static/
  app.js
  style.css
templates/
  index.html
tests/
  test_settlement.py
.gitignore
AI_LOGS.md
README.md
REASONING.md
app.py
database.py
requirements.txt
settlement.py
If .devcontainer, static, templates, or tests are missing, or show up empty — go back and upload just that folder's contents again (drag the folder in, GitHub will recreate it). This matters: without .devcontainer/devcontainer.json, Codespaces won't auto-install dependencies, and without templates/+static/, the app has no page to show.

Step 2: Launch Codespaces
On the repo's main page → green Code button → Codespaces tab → Create codespace on main

Wait for it to finish building (you'll see a terminal open at the bottom, and setup logs scroll by — this takes 30–90 seconds the first time).

Step 3: Confirm dependencies installed
In the terminal that opens automatically:

bash
flask --version
Prints a version number → good, continue to Step 4.
Error → run pip install -r requirements.txt manually, then retry.
Step 4: Run the app
bash
python app.py
You should see Running on http://127.0.0.1:5000.

Step 5: Open it
A popup should appear in the bottom-right saying a port was forwarded — click Open in Browser.
If no popup appears: click the Ports tab (next to the Terminal tab) → find row 5000 → click the little globe/browser icon next to it.

Try it and tell me what you see at each step — especially Step 1, since that's the one most likely to have gone sideways with a manual upload.

okay ya so it is running now i want you to change some ui of it make it more flexible to the user and some images point i will give you images and the name will be fairshare i want

Ran a command
Let's start with the rename since that's unambiguous, and I'll ask about a couple of things before touching the UI further.

By "more flexible for the user," what matters most to you?
Better mobile/responsive layout & editing
Ran a command
Renaming to FairShare and improving mobile responsiveness + inline editing now. I'll also add a spot for your images once you upload them — go ahead and attach them whenever ready and I'll drop them in (logo/cover image, icons, etc.).

Ran a command
Good, still here. Let's make the changes: rename to FairShare, add inline editing (no more delete-and-retype for a payment or a name), and a proper mobile card layout for the ledger.

1. Database — add update queries for members/payments
Edited 7 files, ran 7 commands, shared files

Fairshare
ZIP 

App
PY 

App
JS 

Style
Code·CSS 

Index
Code·HTML 

Test settlement
PY 
