"""
pytest plugin — captures test results into test_results.json
so generate_report.py can build the custom HTML dashboard.
"""
import json
import time
import pytest

_results = []
_start_times = {}


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.failed):
        parts = report.nodeid.split("::")
        class_name = parts[1] if len(parts) >= 3 else "—"
        test_name  = parts[-1].replace("_", " ").title()

        status = "PASSED" if report.passed else "FAILED"
        error  = ""
        if report.failed and report.longrepr:
            error = str(report.longrepr)[-600:]  # last 600 chars of traceback

        _results.append({
            "name":     test_name,
            "class":    class_name,
            "status":   status,
            "duration": round(report.duration, 3),
            "error":    error,
        })


def pytest_sessionfinish(session, exitstatus):
    with open("test_results.json", "w") as f:
        json.dump(_results, f, indent=2)
