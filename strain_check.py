"""Prints the ML model's strain level for demo scenarios, so you know what to expect on stage.
Run with the Docker stack up:   python3 strain_check.py
"""
import json, urllib.request

ML_URL = "http://localhost:8001/ml/predict"

def feats(attempts, wrong, streak, hints, rereads, latencies):
    mean = sum(latencies) / len(latencies) if latencies else 0
    last = latencies[-1] if latencies else 0
    first = latencies[0] if latencies else 0
    return {
        "latency_delta": last or mean,
        "error_rate": wrong / attempts if attempts else 0,
        "attempt_burst": 1 if streak >= 3 else 0,
        "attention_drop": 1 if mean >= 5000 else 0,
        "hint_reliance": hints / attempts if attempts else (1 if hints else 0),
        "cold_start_latency": first,
        "exit_flag_ratio": 0,
        "reread_normalized": rereads / attempts if attempts else (1 if rereads else 0),
        "wrong_streak": streak, "total_attempts": attempts, "hints_used": hints,
        "rereads": rereads, "avg_response_time": mean,
    }

SCENARIOS = [
    # (name, attempts, wrong, streak, hints, rereads, latencies_ms)
    ("1. Calm: 1 Pass",                         1, 0, 0, 0, 0, [3000]),
    ("2. Two Passes in a row",                  2, 0, 0, 0, 0, [3000, 2500]),
    ("3. One Fail",                             1, 1, 1, 0, 0, [2500]),
    ("4. Two Fails in a row",                   2, 2, 2, 0, 0, [2500, 2000]),
    ("5. Three Fails in a row",                 3, 3, 3, 0, 0, [2500, 2000, 1800]),
    ("6. Two Fails + 2 hints",                  2, 2, 2, 2, 0, [2500, 2000]),
    ("7. Three Fails + hint + reread",          3, 3, 3, 1, 1, [2500, 2000, 1800]),
    ("8. Slow & hesitant: 2 Fails, ~9 s each",  2, 2, 2, 0, 0, [9000, 9500]),
    ("9. Recovery: 3 Fails then 2 Passes",      5, 3, 0, 1, 0, [2500, 2000, 1800, 3000, 2800]),
]

for name, *a in SCENARIOS:
    body = json.dumps({"student_id": "demo", "content_id": "demo-page", "features": feats(*a)}).encode()
    req = urllib.request.Request(ML_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=10))
        print(f"{name:<42} -> {r['strain_level']:<9} {round(r['confidence']*100):>3}%   nudge={r['trigger_adaptation']}")
    except Exception as e:
        print(f"{name:<42} -> ERROR {e}")
        break