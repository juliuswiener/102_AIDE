import datetime
import json
import sys
import select

def log_event(event_type, details):
    """Logs an event to aide_log.jsonl."""
    with open("aide_log.jsonl", "a") as f:
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }
        f.write(json.dumps(log_entry, default=str) + "\n")

def check_for_user_input():
    """Check for user input without blocking."""
    return input()
