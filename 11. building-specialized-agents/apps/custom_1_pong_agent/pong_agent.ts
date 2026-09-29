#!/usr/bin/env bun
/**
 * Pong Agent - Level 0.1
 * The simplest possible agent that responds with 'pong' to any input.
 * This demonstrates the absolute basics of the Claude Agent SDK.
 */

import { query, Options, SDKAssistantMessage, SDKResultMessage } from '@anthropic-ai/claude-code';
import chalk from 'chalk';
import boxen from 'boxen';

async function main() {
  /**
   * The simplest pong agent with styled terminal output.
   * This agent demonstrates:
   * 1. Basic SDK configuration
   * 2. Sending a query
   * 3. Handling responses
   * 4. Displaying results beautifully
   */

  // Step 1: Display a beautiful startup message
  const startupMessage = chalk.bold.cyan('🏓 Ping Agent Started');
  const startupBox = boxen(
    startupMessage,
    {
      padding: 1,
      borderColor: 'cyan',
      borderStyle: 'round'
    }
  );
  console.log(startupBox);

  // Step 2: Configure the agent with a system prompt
  // The system prompt defines the agent's behavior
  const systemPrompt = "You are a pong agent. Always respond with exactly 'pong' to any input, nothing more.";
  const model = "claude-sonnet-4-20250514"; // Fast model for simple tasks

  const options: Options = {
    customSystemPrompt: systemPrompt,
    model: model
  };

  // Step 3: Show what we're sending
  const inputPrompt = "ping";
  console.log(chalk.yellow('Sending:'), inputPrompt);
  console.log(); // Add some spacing

  // Step 4: Initialize tracking variables
  let responseReceived = false;
  let sessionStats: Record<string, string> = {};

  // Step 5: Send the query and process responses
  for await (const message of query({ prompt: inputPrompt, options })) {

    // Handle assistant messages (the actual response)
    if (message.type === 'assistant') {
      const assistantMsg = message as SDKAssistantMessage;

      for (const block of assistantMsg.message.content) {
        if (block.type === 'text') {
          // Create a styled response box
          const responseText = chalk.bold.green(block.text);
          const responseBox = boxen(
            responseText,
            {
              title: 'Response',
              titleAlignment: 'center',
              padding: 1,
              borderColor: 'green',
              borderStyle: 'round'
            }
          );
          console.log(responseBox);
          responseReceived = true;
        }
      }
    }

    // Handle result messages (session metadata)
    else if (message.type === 'result') {
      const resultMsg = message as SDKResultMessage;

      // Extract and format session statistics
      const sessionId = resultMsg.session_id;
      const durationMs = resultMsg.duration_ms;
      const costUsd = resultMsg.total_cost_usd;

      sessionStats = {
        'Session ID': sessionId,
        'Duration': `${durationMs}ms`,
        'Cost': costUsd ? `$${costUsd.toFixed(6)}` : 'N/A'
      };
    }
  }

  // Step 6: Display session statistics in a formatted box
  if (Object.keys(sessionStats).length > 0) {
    console.log(); // Add spacing

    // Build stats display
    const statsLines = Object.entries(sessionStats)
      .map(([key, value]) => `${chalk.cyan(key)}: ${chalk.yellow(value)}`)
      .join('\n');

    const statsBox = boxen(
      statsLines,
      {
        title: 'Session Stats',
        titleAlignment: 'center',
        padding: 1,
        borderColor: 'blue',
        borderStyle: 'round'
      }
    );
    console.log(statsBox);
  }

  // Step 7: Display final result
  console.log(); // Add spacing

  if (responseReceived) {
    const successMessage = chalk.bold.green('✅ Pong agent working correctly!');
    console.log(successMessage);
  } else {
    const errorMessage = chalk.bold.red('❌ No response received');
    console.log(errorMessage);
  }
}

// Run the agent
main().catch(console.error);