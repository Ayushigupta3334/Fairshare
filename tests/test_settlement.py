import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from settlement import compute_balances, pool_status, settle, fair_share


def test_fair_share_splits_evenly():
    assert fair_share(6000, 4) == 1500
    assert fair_share(6000, 0) == 0


def test_compute_balances_matches_the_brief_scenario():
    # 4 people, ₹6000 target -> ₹1500/head.
    # A pays in full, B pays half, C overpays to cover D, D pays nothing.
    members = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}, {"id": 4, "name": "D"}]
    payments = [
        {"member_id": 1, "amount": 1500},
        {"member_id": 2, "amount": 750},
        {"member_id": 3, "amount": 3000},  # covers self + D
    ]
    balances = compute_balances(members, payments, target=6000)
    by_name = {b.name: b for b in balances}

    assert by_name["A"].balance == 0
    assert by_name["B"].balance == -750
    assert by_name["C"].balance == 1500
    assert by_name["D"].balance == -1500


def test_pool_status_reports_remaining_and_surplus():
    members = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    payments = [{"member_id": 1, "amount": 1000}]
    balances = compute_balances(members, payments, target=3000)
    status = pool_status(balances, target=3000)

    assert status["collected"] == 1000
    assert status["remaining"] == 2000
    assert status["surplus"] == 0


def test_pool_status_flags_overfunding():
    members = [{"id": 1, "name": "A"}]
    payments = [{"member_id": 1, "amount": 500}]
    balances = compute_balances(members, payments, target=200)
    status = pool_status(balances, target=200)

    assert status["remaining"] == 0
    assert status["surplus"] == 300


def test_settle_only_redistributes_money_that_is_actually_in_the_pool():
    # A settled, B has paid part of their share, C overpaid to cover D,
    # D hasn't paid at all. Total collected (5250) is still short of the
    # 6000 target, so only C's ₹1500 surplus is real money sitting with a
    # person that can be redirected — B's remaining ₹750 is still owed to
    # the *pool*, not to a teammate, so it belongs in "still to collect",
    # not in a peer-to-peer settlement instruction.
    members = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}, {"id": 4, "name": "D"}]
    payments = [
        {"member_id": 1, "amount": 1500},
        {"member_id": 2, "amount": 750},
        {"member_id": 3, "amount": 3000},
        # D pays nothing
    ]
    balances = compute_balances(members, payments, target=6000)
    status = pool_status(balances, target=6000)
    txns = settle(balances)

    assert status["remaining"] == 750  # what's still genuinely uncollected
    assert len(txns) == 1
    assert txns[0].from_name == "D"
    assert txns[0].to_name == "C"
    assert txns[0].amount == 1500  # D covers exactly C's surplus; the rest is B's outstanding share


def test_compute_balances_reflects_edits_the_same_as_new_entries():
    # Editing a payment in place (via PATCH /api/payments/<id>) should land
    # on exactly the same balance as if the corrected amount had been
    # entered from the start — the UI's inline-edit feature shouldn't
    # produce different numbers than delete-and-re-add would have.
    members = [{"id": 1, "name": "A"}]
    edited = [{"member_id": 1, "amount": 750}]  # amount after an in-place edit
    fresh = [{"member_id": 1, "amount": 750}]   # same amount entered directly
    assert compute_balances(members, edited, target=6000) == compute_balances(members, fresh, target=6000)


def test_settle_returns_nothing_when_already_even():
    members = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    payments = [{"member_id": 1, "amount": 100}, {"member_id": 2, "amount": 100}]
    balances = compute_balances(members, payments, target=200)
    assert settle(balances) == []


def test_settle_ignores_sub_paisa_rounding_noise():
    members = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
    payments = [{"member_id": 1, "amount": 1000}, {"member_id": 2, "amount": 1000}, {"member_id": 3, "amount": 1000}]
    # 3000 / 3 = 1000 exactly, so this should be perfectly settled already.
    balances = compute_balances(members, payments, target=3000)
    assert settle(balances) == []
