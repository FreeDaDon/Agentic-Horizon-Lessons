#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Spend caps above the single call: a hierarchical budget ledger and a circuit breaker.

The SDK caps one call (`max_turns`, `max_budget_usd`). This module caps everything above it.

Scopes. A scope path is a tuple of segments from widest to narrowest, such as
("org", "day:2026-11-12", "adw:123", "step:build"). A charge counts against every prefix
of the path. A limit key is either an exact segment ("adw:123") or a segment kind ("adw",
the text before the colon). The exact segment wins. A prefix with no matching key is
unlimited. So {"org": 200, "adw": 5, "step": 2} caps the org at $200, every ADW at $5 and
every step of every ADW at $2.

Limits are inclusive. Spending exactly the limit is allowed; one cent more is refused.

Two kinds of charge:
  charge(path, usd)                     money about to be spent (a reservation or an
                                        estimate). Refused, and not recorded, if any scope
                                        would go over its limit.
  charge(path, usd, already_spent=True) money already gone (a finished call's real cost).
                                        Always recorded, because the ledger must match
                                        reality. Raises afterwards if a scope is now over,
                                        which closes that scope to further work.

All state sits behind one lock and no method awaits, so one ledger and one breaker can be
shared by threads and by asyncio tasks.
"""

from __future__ import annotations

import enum
import threading
import time
from collections import defaultdict, deque
from decimal import Decimal
from typing import Any, Callable

ScopePath = tuple[str, ...]


def usd(amount: float | int | str | Decimal) -> Decimal:
    # Through str so 0.1 + 0.2 lands on 0.3 and the inclusive boundary is exact.
    return amount if isinstance(amount, Decimal) else Decimal(str(amount))


class BudgetExceeded(Exception):
    def __init__(self, scope: ScopePath, spent: float, limit: float):
        super().__init__(f"budget for {'/'.join(scope)} exceeded: ${spent:.4f} of ${limit:.4f}")
        self.scope = scope
        self.spent = spent
        self.limit = limit


class BudgetLedger:
    def __init__(self, limits: dict[str, float]):
        self._limits = {key: usd(value) for key, value in limits.items()}
        self._spent: defaultdict[ScopePath, Decimal] = defaultdict(Decimal)
        self._lock = threading.Lock()

    def limit(self, scope: ScopePath) -> Decimal | None:
        segment = scope[-1]
        return self._limits.get(segment, self._limits.get(segment.partition(":")[0]))

    def spent(self, scope_path: ScopePath) -> float:
        with self._lock:
            return float(self._spent[tuple(scope_path)])

    @staticmethod
    def _prefixes(scope_path: ScopePath) -> list[ScopePath]:
        if not scope_path:
            raise ValueError("scope path must have at least one segment")
        return [tuple(scope_path[: i + 1]) for i in range(len(scope_path))]

    def _first_over(self, scope_path: ScopePath, amount: Decimal) -> tuple[ScopePath, Decimal, Decimal] | None:
        for scope in self._prefixes(scope_path):
            limit = self.limit(scope)
            total = self._spent[scope] + amount
            if limit is not None and total > limit:
                return scope, total, limit
        return None

    def charge(self, scope_path: ScopePath, amount: float, *, already_spent: bool = False) -> None:
        amount = usd(amount)
        if amount < 0:
            raise ValueError("charges must be non-negative")
        with self._lock:
            over = self._first_over(scope_path, amount)
            if over is None or already_spent:
                for scope in self._prefixes(scope_path):
                    self._spent[scope] += amount
        if over is not None:
            scope, total, limit = over
            raise BudgetExceeded(scope, float(total), float(limit))

    def would_exceed(self, scope_path: ScopePath, estimate: float) -> bool:
        with self._lock:
            return self._first_over(scope_path, usd(estimate)) is not None

    def remaining(self, scope_path: ScopePath) -> float:
        """Headroom of the tightest scope on the path. `inf` when nothing on it has a limit."""
        with self._lock:
            headroom = [
                limit - self._spent[scope]
                for scope in self._prefixes(scope_path)
                if (limit := self.limit(scope)) is not None
            ]
        return float(max(Decimal(0), min(headroom))) if headroom else float("inf")


class BreakerState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Stops new work after N consecutive failures or when spend in the last minute passes a rate.

    closed     every call allowed.
    open       nothing allowed until `cooldown_seconds` pass.
    half_open  exactly one trial call allowed. Success closes the breaker; failure reopens it.
    """

    WINDOW_SECONDS = 60.0

    def __init__(self, max_consecutive_failures: int, max_spend_per_minute: float,
                 clock: Callable[[], float] = time.monotonic, cooldown_seconds: float = 60.0):
        self.max_consecutive_failures = max_consecutive_failures
        self.max_spend_per_minute = usd(max_spend_per_minute)
        self.cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._recent: deque[tuple[float, Decimal]] = deque()
        self._failures = 0
        self._state = BreakerState.CLOSED
        self._opened_at = 0.0
        self._trial_in_flight = False
        self.reason: str | None = None

    @property
    def state(self) -> BreakerState:
        with self._lock:
            self._maybe_half_open(self._clock())
            return self._state

    def _maybe_half_open(self, now: float) -> None:
        if self._state is BreakerState.OPEN and now - self._opened_at >= self.cooldown_seconds:
            self._state = BreakerState.HALF_OPEN
            self._trial_in_flight = False

    def _trip(self, now: float, reason: str) -> None:
        self._state = BreakerState.OPEN
        self._opened_at = now
        self.reason = reason

    def allow(self) -> bool:
        with self._lock:
            self._maybe_half_open(self._clock())
            if self._state is BreakerState.CLOSED:
                return True
            if self._state is BreakerState.HALF_OPEN and not self._trial_in_flight:
                self._trial_in_flight = True
                return True
            return False

    def spend_last_minute(self) -> float:
        with self._lock:
            self._prune(self._clock())
            return float(sum(amount for _, amount in self._recent))

    def _prune(self, now: float) -> None:
        while self._recent and now - self._recent[0][0] >= self.WINDOW_SECONDS:
            self._recent.popleft()

    def record(self, success: bool, usd_spent: float = 0.0) -> None:
        with self._lock:
            now = self._clock()
            self._recent.append((now, usd(usd_spent)))
            self._prune(now)
            self._failures = 0 if success else self._failures + 1
            rate = sum(amount for _, amount in self._recent)

            if rate > self.max_spend_per_minute:
                self._trip(now, f"spent ${rate} in the last minute (limit ${self.max_spend_per_minute})")
            elif self._failures >= self.max_consecutive_failures:
                self._trip(now, f"{self._failures} consecutive failures")
            elif self._state is BreakerState.HALF_OPEN:
                if success:
                    self._state = BreakerState.CLOSED
                    self.reason = None
                else:
                    self._trip(now, "trial call failed")
            self._trial_in_flight = False


def options_with_caps(max_turns: int, max_budget_usd: float, **kw: Any) -> dict[str, Any]:
    """Keyword arguments for `ClaudeAgentOptions(**...)` with both per-call caps set."""
    if max_turns < 1:
        raise ValueError("max_turns must be at least 1")
    if max_budget_usd <= 0:
        raise ValueError("max_budget_usd must be positive")
    return {**kw, "max_turns": max_turns, "max_budget_usd": float(max_budget_usd)}


def charge_result(ledger: BudgetLedger, scope_path: ScopePath, result_message: Any) -> float | None:
    """Record a finished call's real cost from anything with `total_cost_usd` (an SDK ResultMessage).

    Returns the amount charged, or None when the result carried no cost. Raises BudgetExceeded
    after recording when the cost pushed a scope over its limit.
    """
    cost = getattr(result_message, "total_cost_usd", None)
    if cost is None:
        return None
    ledger.charge(scope_path, cost, already_spent=True)
    return float(cost)
