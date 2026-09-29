#!/usr/bin/env python3
"""
Test script to verify inline hooks functionality
"""

import asyncio
from qa_agent import block_env_files, log_tool_usage, HookContext


async def test_hooks():
    """Test the inline hook functions."""

    print("Testing inline hooks...")
    print("-" * 50)

    # Create a mock context
    context = HookContext()

    # Test 1: Block .env file
    print("\n1. Testing .env file blocking:")
    result = await block_env_files(
        input_data={
            'tool_name': 'Read',
            'tool_input': {'file_path': '/path/to/.env'}
        },
        tool_use_id='test-id-1',
        context=context
    )
    print(f"   Result: {result}")
    print(f"   Should block: {'deny' in str(result)}")

    # Test 2: Allow normal file
    print("\n2. Testing normal file access:")
    result = await block_env_files(
        input_data={
            'tool_name': 'Read',
            'tool_input': {'file_path': '/path/to/normal.py'}
        },
        tool_use_id='test-id-2',
        context=context
    )
    print(f"   Result: {result}")
    print(f"   Should allow: {result == {}}")

    # Test 3: Test logging
    print("\n3. Testing tool usage logging:")
    result = await log_tool_usage(
        input_data={
            'tool_name': 'Read',
            'tool_input': {'file_path': '/path/to/file.txt'}
        },
        tool_use_id='test-id-3',
        context=context
    )
    print(f"   Result: {result}")
    print(f"   Should return empty: {result == {}}")

    print("\n" + "-" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_hooks())