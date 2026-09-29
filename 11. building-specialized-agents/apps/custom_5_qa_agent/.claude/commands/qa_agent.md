---
allowed-tools: Read, WebSearch, WebFetch, Bash, Task
description: Answer questions about the codebase using parallel search
---

# Codebase Q&A Request

Answer the following question about the codebase: $1

## Instructions

1. **Efficiency First**: For simple, specific file requests, use Read tool directly
2. **Parallel Search**: For complex queries, deploy multiple Task subagents in parallel
3. **Security**: Never attempt to read .env files - they are blocked by hooks
4. **Comprehensive**: Include specific file references with line numbers
5. **Code Examples**: Show relevant code snippets where helpful

## Response Format

- Start with a direct answer to the question
- Provide file paths with line numbers (e.g., `src/utils.py:42`)
- Include code snippets for clarity
- Explain relationships between components
- End with related areas to explore

If this is not a codebase-related question, respond: "I'm specialized for codebase Q&A. Please use WebSearch for general questions."