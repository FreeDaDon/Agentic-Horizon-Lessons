# Level 3 — Control-Flow Prompt Template

> A Level 2 prompt whose workflow contains **conditions, loops, and early returns**. Use strong keywords (`STOP`, `IMPORTANT`) and XML-style tags around loops.

```md
---
description: <what it does>
argument-hint: [<items source>] [<count>]
allowed-tools: <tools>
---

# <Title>

Follow the `Workflow` to process `<ITEMS>` and `Report` the results.

## Variables

ITEMS: $1
COUNT: $2 or 3 if not provided
OUTPUT_DIR: <dir>/<date_time>/

## Workflow

- If `ITEMS` is not provided, STOP immediately and ask the user to provide it.
- Check your available tools include `<required_tool>`. If not, STOP immediately and tell the user what to enable.
- Get <date_time> with `date +%Y-%m-%d_%H-%M-%S`; create `OUTPUT_DIR`.
- IMPORTANT: Process `COUNT` items following the `item-loop` below.

<item-loop>
  - <action on the current item>
  - If <condition>, skip this item and record why.
  - Save the result to `OUTPUT_DIR/<item_name>.<ext>`
</item-loop>

- After the loop, verify every expected output file exists.

## Report

- Items processed / skipped (with reasons)
- Full path to `OUTPUT_DIR`
```

## Example guard (from `build.md`)

```md
- If no `PATH_TO_PLAN` is provided, STOP immediately and ask the user to provide it.
```

This early return costs almost nothing and prevents the agent from guessing at missing input.
