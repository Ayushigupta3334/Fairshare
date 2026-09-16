from flask import Flask, jsonify, request, render_template

import database as db
from settlement import compute_balances, pool_status, settle

app = Flask(__name__)


def row_to_dict(row):
    return dict(row) if row is not None else None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    """
    Single endpoint the frontend polls after every change: settings, the raw
    member/payment lists (for rendering the ledger and forms), plus the
    computed balances / pool status / settlement — so the frontend never has
    to duplicate the splitting logic in JavaScript.
    """
    conn = db.get_connection()
    try:
        settings = row_to_dict(conn.execute("SELECT * FROM settings WHERE id = 1").fetchone())
        members = [row_to_dict(r) for r in conn.execute("SELECT id, name FROM members ORDER BY id").fetchall()]
        payments = [
            row_to_dict(r)
            for r in conn.execute(
                "SELECT id, member_id, amount, note, created_at FROM payments ORDER BY id"
            ).fetchall()
        ]
    finally:
        conn.close()

    target = settings["target"]
    balances = compute_balances(members, payments, target)
    status = pool_status(balances, target)
    txns = settle(balances)

    return jsonify(
        {
            "settings": settings,
            "members": members,
            "payments": payments,
            "balances": [vars(b) for b in balances],
            "status": status,
            "settlement": [vars(t) for t in txns],
        }
    )


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json(force=True) or {}
    pool_name = str(data.get("pool_name", "")).strip()
    organiser = str(data.get("organiser", "")).strip()
    try:
        target = float(data.get("target", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "target must be a number"}), 400
    if target < 0:
        return jsonify({"error": "target can't be negative"}), 400

    conn = db.get_connection()
    try:
        conn.execute(
            "UPDATE settings SET pool_name = ?, target = ?, organiser = ? WHERE id = 1",
            (pool_name, target, organiser),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@app.route("/api/members", methods=["POST"])
def add_member():
    data = request.get_json(force=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = db.get_connection()
    try:
        cur = conn.execute("INSERT INTO members (name) VALUES (?)", (name,))
        conn.commit()
        member_id = cur.lastrowid
    finally:
        conn.close()
    return jsonify({"id": member_id, "name": name}), 201


@app.route("/api/members/<int:member_id>", methods=["PATCH"])
def rename_member(member_id):
    data = request.get_json(force=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = db.get_connection()
    try:
        exists = conn.execute("SELECT 1 FROM members WHERE id = ?", (member_id,)).fetchone()
        if not exists:
            return jsonify({"error": "unknown member_id"}), 404
    finally:
        conn.close()

    db.update_member_name(member_id, name)
    return jsonify({"ok": True})


@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@app.route("/api/payments", methods=["POST"])
def add_payment():
    data = request.get_json(force=True) or {}
    try:
        member_id = int(data.get("member_id"))
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "member_id and amount are required"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400
    note = str(data.get("note", "")).strip()

    conn = db.get_connection()
    try:
        exists = conn.execute("SELECT 1 FROM members WHERE id = ?", (member_id,)).fetchone()
        if not exists:
            return jsonify({"error": "unknown member_id"}), 400
        cur = conn.execute(
            "INSERT INTO payments (member_id, amount, note) VALUES (?, ?, ?)",
            (member_id, amount, note),
        )
        conn.commit()
        payment_id = cur.lastrowid
    finally:
        conn.close()
    return jsonify({"id": payment_id}), 201


@app.route("/api/payments/<int:payment_id>", methods=["PATCH"])
def edit_payment(payment_id):
    data = request.get_json(force=True) or {}
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "amount is required"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400
    note = str(data.get("note", "")).strip()

    conn = db.get_connection()
    try:
        exists = conn.execute("SELECT 1 FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not exists:
            return jsonify({"error": "unknown payment_id"}), 404
    finally:
        conn.close()

    db.update_payment(payment_id, amount, note)
    return jsonify({"ok": True})


@app.route("/api/payments/<int:payment_id>", methods=["DELETE"])
def delete_payment(payment_id):
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@app.route("/api/reset", methods=["POST"])
def reset():
    db.reset_db()
    return jsonify({"ok": True})


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
else:
    db.init_db()
