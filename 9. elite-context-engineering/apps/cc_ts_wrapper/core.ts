import { query } from "@anthropic-ai/claude-code";
import type {
  ClaudeSettings,
  AdhocPromptOptions,
  ReusablePromptConfig,
  PromptResult,
  MessageHandler
} from "./types";
import { DEFAULT_SETTINGS } from "./types";

// Store reusable prompt configurations
const promptRegistry = new Map<string, ReusablePromptConfig>();

export async function adhoc_prompt(
  prompt: string,
  settings?: ClaudeSettings
): Promise<PromptResult> {
  const result: PromptResult = {
    success: false,
    messages: [],
  };

  try {
    const mergedSettings = { ...DEFAULT_SETTINGS, ...settings };
    const abortController = settings?.abortController || new AbortController();

    for await (const message of query({
      prompt,
      options: {
        abortController,
        maxTurns: mergedSettings.maxTurns,
        customSystemPrompt: mergedSettings.systemPrompt,
        allowedTools: mergedSettings.allowedTools,
        continue: mergedSettings.continue,
        resume: mergedSettings.resume,
      }
    })) {
      if (message.type === "result" && message.subtype === "success") {
        result.messages.push(message.result);
      }
      if (message.type === "system") {
        result.sessionId = message.session_id;
      }
    }
    
    result.success = true;
  } catch (error) {
    result.error = error as Error;
  }

  return result;
}

export function register_prompt(
  custom_slash_command: string,
  config: ReusablePromptConfig
): void {
  promptRegistry.set(custom_slash_command, config);
}

export async function reusable_prompt(
  custom_slash_command: string,
  userPrompt?: string,
  settings?: ClaudeSettings
): Promise<PromptResult> {
  const config = promptRegistry.get(custom_slash_command);
  
  if (!config) {
    return {
      success: false,
      messages: [],
      error: new Error(`Unknown command: ${custom_slash_command}`)
    };
  }

  const finalPrompt = config.promptTemplate
    ? config.promptTemplate.replace("{USER_PROMPT}", userPrompt || "")
    : userPrompt || config.description;

  const mergedSettings = {
    ...DEFAULT_SETTINGS,
    ...config.defaultSettings,
    ...settings,
    systemPrompt: settings?.systemPrompt || config.systemPrompt
  };

  return adhoc_prompt(finalPrompt, mergedSettings);
}

export function list_commands(): ReusablePromptConfig[] {
  return Array.from(promptRegistry.values());
}