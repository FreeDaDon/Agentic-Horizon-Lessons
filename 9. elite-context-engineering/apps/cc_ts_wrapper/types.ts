// AbortController is globally available in modern environments

export interface ClaudeSettings {
  maxTurns?: number;
  systemPrompt?: string;
  allowedTools?: string[];
  continue?: boolean;
  resume?: string;
  abortController?: AbortController;
}

export interface AdhocPromptOptions {
  prompt: string;
  settings?: ClaudeSettings;
}

export interface ReusablePromptConfig {
  name: string;
  description: string;
  systemPrompt?: string;
  defaultSettings?: ClaudeSettings;
  promptTemplate?: string;
}

export interface PromptResult {
  success: boolean;
  messages: string[];
  error?: Error;
  sessionId?: string;
}

export type MessageHandler = (message: any) => void;

export const DEFAULT_SETTINGS: ClaudeSettings = {
  maxTurns: 5,
  allowedTools: ["Bash", "Read", "Write", "Edit", "WebSearch"],
};