"""
ADW Review Module - Read the PASS/FAIL verdict from a /review agent's final message.

Usage:
    from adw_modules.adw_review import parse_verdict

    verdict = parse_verdict(result.result)  # "PASS", "FAIL", or None
"""

from __future__ import annotations

import re

_FAIL = re.compile(r"\bFAIL")  # FAIL, FAILED, FAILURE
_PASS = re.compile(r"\bPASS(ED)?\b")  # not PASSWORD, not BYPASS


def parse_verdict(text: str | None) -> str | None:
    """Return "FAIL", "PASS", or None when the text states neither.

    FAIL wins over PASS. Callers must treat None as "not passed": an unclear
    review is not a clean one.
    """
    if not text:
        return None
    upper = text.upper()
    if _FAIL.search(upper):
        return "FAIL"
    if _PASS.search(upper):
        return "PASS"
    return None


__all__ = ["parse_verdict"]
