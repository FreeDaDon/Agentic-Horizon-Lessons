import { beforeEach, expect, mock, test } from "bun:test";

// Record the options each run would send to the SDK instead of starting an agent
const sent: Record<string, unknown>[] = [];
mock.module("@anthropic-ai/claude-agent-sdk", () => ({
  query: ({ options }: { options: Record<string, unknown> }) => {
    sent.push(options);
    return (async function* () {})();
  },
}));

const { settingsFromFlags } = await import("./cli");
const { adhoc_prompt, reusable_prompt } = await import("./core");
const { DEFAULT_SETTINGS } = await import("./types");

beforeEach(() => {
  sent.length = 0;
});

test("no flags gives no settings, so nothing overrides the defaults", () => {
  expect(settingsFromFlags({})).toEqual({});
});

test("given flags become settings", () => {
  expect(settingsFromFlags({ "max-turns": "3", "system-prompt": "Be brief.", tools: "Read,Grep" })).toEqual({
    maxTurns: 3,
    systemPrompt: "Be brief.",
    allowedTools: ["Read", "Grep"],
  });
});

test("an adhoc prompt without flags keeps the default turn cap and tools", async () => {
  await adhoc_prompt("hi", settingsFromFlags({}));
  expect(sent[0].maxTurns).toBe(DEFAULT_SETTINGS.maxTurns);
  expect(sent[0].allowedTools).toEqual(DEFAULT_SETTINGS.allowedTools);
});

test("a registered command without flags keeps its own turn cap, tools and system prompt", async () => {
  await reusable_prompt("/analyze", "the cache layer", settingsFromFlags({}));
  expect(sent[0].maxTurns).toBe(10);
  expect(sent[0].allowedTools).toEqual(["Read", "Grep", "Bash"]);
  expect(sent[0].systemPrompt).toBe("You are a senior engineer analyzing code quality and performance");
});

test("flags still override", async () => {
  await reusable_prompt("/analyze", "x", settingsFromFlags({ "max-turns": "2", tools: "Read" }));
  expect(sent[0].maxTurns).toBe(2);
  expect(sent[0].allowedTools).toEqual(["Read"]);
});
