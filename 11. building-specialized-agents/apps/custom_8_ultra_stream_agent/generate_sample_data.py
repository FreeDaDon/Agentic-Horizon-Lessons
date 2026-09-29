#!/usr/bin/env python3
"""
Generate sample JSONL data for Ultra Stream Agent testing
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_sample_logs(num_logs=1000):
    """Generate sample log entries"""

    logs = []
    start_time = datetime.now() - timedelta(hours=24)

    # Sample data
    users = [f"user{i:03d}" for i in range(1, 51)]
    services = ["auth", "payment", "api", "database", "cache", "queue", "storage", "email"]
    actions = ["login", "logout", "purchase", "query", "update", "delete", "upload", "download"]

    error_messages = [
        "Connection timeout",
        "Authentication failed",
        "Database connection lost",
        "Payment processing failed",
        "Rate limit exceeded",
        "Invalid request format",
        "Service unavailable",
        "Memory limit exceeded",
        "Disk space low",
        "Network unreachable"
    ]

    warning_messages = [
        "Slow query detected",
        "High memory usage",
        "Deprecated API call",
        "Cache miss rate high",
        "Connection pool near limit",
        "Retry attempt",
        "Partial data retrieved",
        "Session expiring soon"
    ]

    info_messages = [
        "Request processed successfully",
        "User session started",
        "Data synchronized",
        "Cache updated",
        "Backup completed",
        "Configuration reloaded",
        "Service started",
        "Health check passed"
    ]

    for i in range(num_logs):
        timestamp = start_time + timedelta(seconds=i * 86.4)  # Spread over 24 hours

        # Determine log type with weighted probability
        log_type_rand = random.random()
        if log_type_rand < 0.05:  # 5% high severity
            severity = "error"
            message = random.choice(error_messages)
            level = "ERROR"
            status_code = random.choice([500, 502, 503, 504])
        elif log_type_rand < 0.20:  # 15% medium severity
            severity = "warning"
            message = random.choice(warning_messages)
            level = "WARN"
            status_code = random.choice([400, 401, 403, 429])
        else:  # 80% low severity
            severity = "info"
            message = random.choice(info_messages)
            level = "INFO"
            status_code = 200

        # Sometimes include user ID
        user_id = random.choice(users) if random.random() < 0.7 else None

        # Create log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "service": random.choice(services),
            "action": random.choice(actions),
            "message": message,
            "status_code": status_code,
            "response_time_ms": random.randint(10, 5000) if severity != "error" else None,
            "request_id": f"req_{i:06d}",
            "session_id": f"sess_{random.randint(1000, 9999)}"
        }

        if user_id:
            log_entry["user_id"] = user_id

        # Add additional context for some logs
        if random.random() < 0.3:
            log_entry["metadata"] = {
                "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "user_agent": random.choice(["Chrome/120", "Firefox/121", "Safari/17", "Mobile/iOS"]),
                "endpoint": f"/api/v1/{random.choice(actions)}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"])
            }

        # Add error details for errors
        if severity == "error":
            log_entry["error"] = {
                "type": random.choice(["RuntimeError", "ConnectionError", "ValidationError", "TimeoutError"]),
                "message": message,
                "stack_trace": f"at function_{random.randint(1, 10)}() line {random.randint(1, 500)}"
            }

        # Simulate related logs (e.g., multiple errors for same user)
        if i > 50 and random.random() < 0.1:  # 10% chance of related log
            prev_log = logs[i - random.randint(1, 10)]
            if "user_id" in prev_log:
                log_entry["user_id"] = prev_log["user_id"]
                log_entry["related_request"] = prev_log.get("request_id")

        logs.append(log_entry)

    # Add some critical error clusters
    for i in range(3):  # 3 error clusters
        cluster_start = random.randint(100, num_logs - 20)
        cluster_user = random.choice(users)

        for j in range(5):  # 5 errors in quick succession
            if cluster_start + j < len(logs):
                logs[cluster_start + j]["level"] = "ERROR"
                logs[cluster_start + j]["user_id"] = cluster_user
                logs[cluster_start + j]["message"] = "Critical: Database connection failed"
                logs[cluster_start + j]["error"] = {
                    "type": "DatabaseError",
                    "message": "Connection pool exhausted",
                    "retry_count": j
                }

    return logs


def write_jsonl_file(logs, filepath):
    """Write logs to JSONL file"""

    with open(filepath, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')


def main():
    """Generate sample JSONL data file"""

    # Create data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate logs
    print("🔄 Generating sample logs...")
    logs = generate_sample_logs(1000)

    # Write to file
    filepath = data_dir / "ultra_stream_agent.jsonl"
    write_jsonl_file(logs, filepath)

    print(f"✅ Generated {len(logs)} sample logs")
    print(f"📁 Saved to: {filepath}")

    # Print statistics
    error_count = sum(1 for log in logs if log.get("level") == "ERROR")
    warn_count = sum(1 for log in logs if log.get("level") == "WARN")
    info_count = sum(1 for log in logs if log.get("level") == "INFO")

    print("\n📊 Log Statistics:")
    print(f"  - Errors: {error_count}")
    print(f"  - Warnings: {warn_count}")
    print(f"  - Info: {info_count}")

    users_with_logs = len(set(log.get("user_id") for log in logs if log.get("user_id")))
    print(f"  - Users: {users_with_logs}")


if __name__ == "__main__":
    main()