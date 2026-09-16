"""
Core pool-splitting logic, kept free of Flask/SQLite so it can be
unit-tested and reasoned about on its own (see tests/test_settlement.py).

Three questions in, three functions out:
    - how much do I still owe?   -> compute_balances()
    - have we collected enough?  -> pool_status()
    - who pays whom?             -> settle()
"""

from dataclasses import dataclass, field

EPSILON = 0.01  # ₹0.01 — balances closer than this to zero count as settled


@dataclass
class Balance:
    member_id: int
    name: str
    fair_share: float
    paid: float
    balance: float  # paid - fair_share. positive = owed money, negative = owes money


@dataclass
class Transaction:
    from_name: str
    to_name: str
    amount: float


def fair_share(target: float, member_count: int) -> float:
    """Equal split of the target across everyone who's chipping in."""
    if member_count <= 0:
        return 0.0
    return target / member_count


def compute_balances(members: list[dict], payments: list[dict], target: float) -> list[Balance]:
    """
    members:  [{id, name}, ...]
    payments: [{member_id, amount}, ...]  (amount already paid, any number of
               entries per member — partial payments are just more entries)

    Each person's balance is net of everything they've paid so far against
    their fair share. Deliberately does NOT track "who paid on whose behalf" —
    if A overpays to cover B, A's balance goes positive and B's goes equally
    negative, and settle() below arrives at the same fair outcome regardless
    of the reason for the overpayment.
    """
    share = fair_share(target, len(members))
    paid_by_member = {m["id"]: 0.0 for m in members}
    for p in payments:
        if p["member_id"] in paid_by_member:
            paid_by_member[p["member_id"]] += p["amount"]

    return [
        Balance(
            member_id=m["id"],
            name=m["name"],
            fair_share=share,
            paid=paid_by_member[m["id"]],
            balance=round(paid_by_member[m["id"]] - share, 2),
        )
        for m in members
    ]


def pool_status(balances: list[Balance], target: float) -> dict:
    collected = round(sum(b.paid for b in balances), 2)
    remaining = round(max(0.0, target - collected), 2)
    surplus = round(max(0.0, collected - target), 2)
    pct = 0.0 if target <= 0 else min(100.0, (collected / target) * 100)
    return {
        "collected": collected,
        "target": target,
        "remaining": remaining,
        "surplus": surplus,
        "percent": round(pct, 1),
    }


def settle(balances: list[Balance]) -> list[Transaction]:
    """
    Greedy debt simplification: repeatedly match the largest creditor with
    the largest debtor until every balance is within EPSILON of zero.

    Not guaranteed to be the mathematically optimal minimum-transaction-count
    settlement in every possible case (that's NP-hard in general), but for a
    realistic group size it produces the same minimal or near-minimal count,
    and stays simple enough to verify by eye.
    """
    creditors = sorted(
        (Balance(**vars(b)) for b in balances if b.balance > EPSILON),
        key=lambda b: b.balance,
        reverse=True,
    )
    debtors = sorted(
        (Balance(**{**vars(b), "balance": -b.balance}) for b in balances if b.balance < -EPSILON),
        key=lambda b: b.balance,
        reverse=True,
    )

    txns: list[Transaction] = []
    ci = di = 0
    while ci < len(creditors) and di < len(debtors):
        c, d = creditors[ci], debtors[di]
        amount = round(min(c.balance, d.balance), 2)
        if amount > EPSILON:
            txns.append(Transaction(from_name=d.name, to_name=c.name, amount=amount))
        c.balance -= amount
        d.balance -= amount
        if c.balance <= EPSILON:
            ci += 1
        if d.balance <= EPSILON:
            di += 1

    return txns
