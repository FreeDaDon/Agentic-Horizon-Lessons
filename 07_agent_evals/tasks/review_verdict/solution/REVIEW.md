# Review of change.diff

## Blockers

- The free-shipping check changes from `>=` to `>`. An order of exactly $100.00 now pays $5.00. SPEC.md says $100.00 or more ships free.
- The negative-total guard is deleted. `shipping_cost(-1)` now returns $5.00 instead of raising ValueError, which SPEC.md requires.

## Summary

The diff is described as a simplification but changes behavior in two places the spec covers.

VERDICT: FAIL
