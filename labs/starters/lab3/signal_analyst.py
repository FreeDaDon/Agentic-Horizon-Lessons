import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query

OPTIONS = ClaudeAgentOptions(model="sonnet", permission_mode="bypassPermissions")


async def main():
    async for message in query(prompt="Look at SPY and tell me whether to buy.", options=OPTIONS):
        print(message)


asyncio.run(main())
