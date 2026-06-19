"""Audit Ringg call records for lead status issues."""

from collections import Counter


def wants_callback(record):
    """
    Lightweight callback detector used only for auditing.

    Prefer the pipeline's structured callback fields. If they are unavailable,
    fall back to a small transcript heuristic. In production this should be
    replaced by a validated callback-intent classifier.
    """
    final = record.get("final_json") or {}

    if final.get("callback_requested") or final.get("callback_time"):
        return True

    text = (record.get("transcript") or "").lower()

    callback_phrases = (
        "call me tomorrow",
        "call me later",
        "call me in the evening",
        "call me after",
        "call back tomorrow",
        "call back later",
    )

    return any(phrase in text for phrase in callback_phrases)


def audit(records):
    """Print and return the three issue types plus a summary count."""
    counts = Counter()

    for r in records:
        cid = r["call_id"]
        final = r.get("final_json") or {}
        payload = r.get("webhook_payload") or {}
        status = r.get("webhook_status_code")

        delivered_ok = status is not None and 200 <= status < 300

        # 1) Callback requested, but delivered as NOT_INTERESTED
        if (
            delivered_ok
            and wants_callback(r)
            and payload.get("lead_status") == "NOT_INTERESTED"
        ):
            counts["callback_as_not_interested"] += 1
            print(f"[1] {cid}: callback requested but lead_status=NOT_INTERESTED")

        # 2) Webhook delivery failed (non-2xx)
        if not delivered_ok:
            counts["webhook_failed"] += 1
            print(f"[2] {cid}: webhook failed (HTTP {status})")
            continue

        # 3) Delivered, but payload contradicts final JSON
        if payload.get("lead_status") != final.get("disposition"):
            counts["payload_conflict"] += 1
            print(f"[3] {cid}: lead_status != disposition")

        elif (
            (final.get("callback_requested") or final.get("callback_time"))
            and not payload.get("callback_datetime")
        ):
            counts["payload_conflict"] += 1
            print(f"[3] {cid}: callback recorded but callback_datetime is null")

    print("\nSummary:", dict(counts))
    return counts


if __name__ == "__main__":
    records = [
        {
            "call_id": "CALL_001",
            "transcript": "User: I am busy. Yes, call me tomorrow after 5 PM.",
            "final_json": {
                "disposition": "NOT_INTERESTED",
                "callback_requested": False,
                "callback_time": None,
            },
            "webhook_payload": {
                "lead_status": "NOT_INTERESTED",
                "callback_datetime": None,
            },
            "webhook_status_code": 200,
        },
        {
            "call_id": "CALL_002",
            "transcript": "User: Not interested. Please don't call again.",
            "final_json": {
                "disposition": "NOT_INTERESTED",
                "callback_requested": False,
                "callback_time": None,
            },
            "webhook_payload": {
                "lead_status": "NOT_INTERESTED",
                "callback_datetime": None,
            },
            "webhook_status_code": 200,
        },
        {
            "call_id": "CALL_003",
            "transcript": "User: Yes, sounds good. Please tell me more.",
            "final_json": {
                "disposition": "INTERESTED",
                "callback_requested": False,
                "callback_time": None,
            },
            "webhook_payload": {
                "lead_status": "INTERESTED",
                "callback_datetime": None,
            },
            "webhook_status_code": 422,
        },
        {
            "call_id": "CALL_004",
            "transcript": "User: Maybe. I need to check with my brother.",
            "final_json": {
                "disposition": "UNCERTAIN",
                "callback_requested": False,
                "callback_time": None,
            },
            "webhook_payload": {
                "lead_status": "UNCERTAIN",
                "callback_datetime": None,
            },
            "webhook_status_code": 200,
        },
        {
            "call_id": "CALL_005",
            "transcript": "User: I am driving. Call me in the evening.",
            "final_json": {
                "disposition": "NOT_INTERESTED",
                "callback_requested": True,
                "callback_time": "evening",
            },
            "webhook_payload": {
                "lead_status": "NOT_INTERESTED",
                "callback_datetime": None,
            },
            "webhook_status_code": 200,
        },
    ]

    audit(records)
