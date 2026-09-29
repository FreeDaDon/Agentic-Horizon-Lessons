# Lesson 10 — Agentic Prompt Engineering: The 7 Levels (transcript summary)

> **Source:** [`10. seven-levels-agentic-prompt-formats-v1 mp4.txt`](../10.%20seven-levels-agentic-prompt-formats-v1%20mp4.txt) (~58 min) · code: [`10. agentic-prompt-engineering/`](../10.%20agentic-prompt-engineering/README.md) · pillar: [02](../02_agentic_prompt_engineering/README.md)

## BLUF
*"The prompt is now the fundamental unit of engineering."* Write for the **stakeholder trifecta** (you, your team, your agents), using **consistent formats** built from **composable, swappable sections**. Seven prompt levels stack capabilities. Levels 1–4 cover 80–90% of prompts, the **Workflow** section is S-tier, and the **template meta prompt** (level 6) is where your speed goes up the most. System prompts are rules for *every* conversation, so mistakes there scale to everything.

## Timeline

| Time | Segment | Key points |
|---|---|---|
| 0:10 | Framing | One good prompt → hundreds of hours of work; one bad prompt compounds failure. The trifecta; a library of reusable prompts; in-loop → out-of-loop → ZTE (zero-touch engineering) |
| 3:18 | **L1 High-level** | Title, high-level prompt, purpose. `all_tools`, `start`. *"Great place to start, terrible place to end."* Three repetitions mark a pattern |
| 6:31 | **L2 Workflow** | Metadata, Workflow (S usefulness / C skill), Report, Variables (A/B; static vs dynamic), Instructions, Codebase Structure (context map, C tier). `prime`, `build`, `quick-plan`, `prime_tier_list`. **Input → Workflow → Output** |
| 20:38 | **L3 Control flow** | `If no PATH_TO_PLAN… STOP`; `<image-loop>` in `create_image`. A/B. Only add sections you need (`edit_image` has no report) |
| 26:21 | **L4 Delegate** | `parallel_subagents`, `load_ai_docs`, `background`. The primary agent becomes a prompt engineer for its sub-agents. S/A. *"Consistency is the greatest weapon against confusion."* |
| 34:58 | **L5 Higher-order** | A prompt that accepts a prompt or plan: `/build <spec>`. B/A |
| 36:45 | **L6 Template meta prompt** | `t_metaprompt_workflow`: Documentation context map + **Specified Format** template; `plan_vite_vue` plan template. The prompt that builds prompts |
| 42:12 | **L7 Self-improving** | A dynamic `## Expertise` section updated by agents (the expert pattern). A usefulness; A–S skill |
| 44:30 | Remaining sections | Examples (A useful, low skill); Relevant Files (C/C). Push your own skill to at least B tier |
| 46:36 | System vs user prompts | The system prompt is the rule book for every conversation, 1–3 orders of magnitude more impact. Key sections: Purpose, Instructions, Examples, loose Workflow. *"Workflows reduce agency to increase determinism."* |
| 53:33 | Close | Two ideas: communicate extraordinarily well, and use consistent formats so you can CRUD prompts fast |

## Quotable
- *"If I handed this to a coworker, could they complete this work top to bottom?"*
- *"Great prompting is great communicating."*
- *"Consistency beats complexity."*
- *"Once you can create the prompt that helps you create prompts, you start moving much faster than other engineers."*
