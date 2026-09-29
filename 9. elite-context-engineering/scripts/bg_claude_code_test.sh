#!/bin/bash

bg() {
    USER_PROMPT=$1
    MODEL=${2:-sonnet}
    REPORT_FILE=${2:-agents/background/background-report-$(date +%Y%m%d_%H%M%S).md}
    
    echo "Kicking off background Claude Code instance with:
    USER_PROMPT: ${USER_PROMPT}
    MODEL: ${MODEL}
    REPORT_FILE: ${REPORT_FILE}"
    
    claude --print \
        --model "${MODEL}" \
        --output-format text \
        --dangerously-skip-permissions \
        --mcp-config .mcp.json \
        --append-system-prompt "You are running as a background agent. Document your progress continuously in ${REPORT_FILE}. When starting, create the report file and write your understanding of the task. Update it as you work through the task. Include any findings, blockers, or important information. When complete, rename the file to ${REPORT_FILE}.complete.md. If you fail or cannot complete the task, rename it to ${REPORT_FILE}.failed.md." \
        "${USER_PROMPT}"
}

bg "respond with 'hello world'"