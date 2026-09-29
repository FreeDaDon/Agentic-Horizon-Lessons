# Level 1 — High-Level Prompt Template

> Reusable, ad hoc, static. One to three sections: Title, High-level prompt (required), Purpose. Save as `.claude/commands/<name>.md` after the third time you type the same request.

```md
# <Title: verb + object>

<Purpose: one direct sentence addressed to the agent — what this prompt accomplishes.>

<High-level prompt: the request itself, a few lines at most. Commands or URLs inline.>
```

## Example (from `10. agentic-prompt-engineering/.claude/commands/start.md`)

```md
# Start Prompt Tier List App

Start the Agentic Prompt Tier List application for development.

1. Navigate to the application directory: `cd apps/prompt_tier_list`
2. Install dependencies (if needed): `bun install`
3. Start the development server in the background: `bun run dev`
4. Open your browser to: http://localhost:5173/
```

**Promote to Level 2** when you need inputs (variables), a fixed output (report), or more than ~5 steps.
