#!/usr/bin/env bun

import { parseArgs } from "util";
import { adhoc_prompt, reusable_prompt, register_prompt, list_commands } from "./core";
import type { ClaudeSettings, ReusablePromptConfig } from "./types";

// Register built-in commands
register_prompt("/analyze", {
  name: "analyze",
  description: "Analyze code or system performance",
  systemPrompt: "You are a senior engineer analyzing code quality and performance",
  defaultSettings: {
    maxTurns: 10,
    allowedTools: ["Read", "Grep", "Bash"]
  },
  promptTemplate: "Analyze the following: {USER_PROMPT}"
});

register_prompt("/refactor", {
  name: "refactor",
  description: "Refactor code for better maintainability",
  systemPrompt: "You are an expert at code refactoring and clean architecture",
  defaultSettings: {
    maxTurns: 15,
    allowedTools: ["Read", "Write", "Edit", "MultiEdit"]
  },
  promptTemplate: "Refactor the following code: {USER_PROMPT}"
});

// Only the flags that were given: a key set to undefined would overwrite the defaults when merged
export function settingsFromFlags(values: Record<string, unknown>): ClaudeSettings {
  const settings: ClaudeSettings = {};
  if (values["max-turns"]) settings.maxTurns = parseInt(values["max-turns"] as string);
  if (typeof values["system-prompt"] === "string") settings.systemPrompt = values["system-prompt"];
  if (typeof values.tools === "string") settings.allowedTools = values.tools.split(",");
  return settings;
}

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      command: { type: "string", short: "c" },
      prompt: { type: "string", short: "p" },
      "max-turns": { type: "string" },
      "system-prompt": { type: "string" },
      tools: { type: "string" },
      list: { type: "boolean", short: "l" },
      help: { type: "boolean", short: "h" },
    },
    strict: false,
    allowPositionals: true,
  });

  if (values.help) {
    console.log(`
Claude Code TypeScript Wrapper

Usage:
  bun run cli.ts [options] [prompt]
  bun run cli.ts --command <slash-command> [prompt]

Options:
  -c, --command       Use a registered slash command
  -p, --prompt        Provide prompt directly
  --max-turns         Maximum conversation turns
  --system-prompt     Custom system prompt
  --tools            Comma-separated list of allowed tools
  -l, --list         List available commands
  -h, --help         Show this help message

Examples:
  bun run cli.ts "Analyze the current directory"
  bun run cli.ts -c /analyze "Check for memory leaks"
  bun run cli.ts --max-turns 3 "Quick code review"
    `);
    process.exit(0);
  }

  if (values.list) {
    console.log("\nAvailable Commands:");
    for (const cmd of list_commands()) {
      console.log(`  /${cmd.name} - ${cmd.description}`);
    }
    process.exit(0);
  }

  const prompt = (typeof values.prompt === "string" ? values.prompt : "") || positionals.join(" ");
  
  if (!prompt && !values.command) {
    console.error("Error: No prompt provided");
    process.exit(1);
  }

  const settings = settingsFromFlags(values);

  let result;
  
  if (values.command && typeof values.command === "string") {
    result = await reusable_prompt(values.command, prompt, settings);
  } else {
    result = await adhoc_prompt(prompt, settings);
  }

  if (result.success) {
    for (const message of result.messages) {
      console.log(message);
    }
    if (result.sessionId) {
      console.log(`\nSession ID: ${result.sessionId}`);
    }
  } else {
    console.error(`Error: ${result.error?.message}`);
    process.exit(1);
  }
}

// Export for programmatic use
export { adhoc_prompt, reusable_prompt, register_prompt };

// Run CLI if executed directly
if (import.meta.main) {
  main().catch(console.error);
}