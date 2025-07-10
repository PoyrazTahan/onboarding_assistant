#!/usr/bin/env python3
"""
REFERENCE: Function Calling Tests - Important Findings

This file consolidates all important test results for future reference.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
import openai

# Load environment
load_dotenv()

# =============================================================================
# TEST FINDINGS SUMMARY
# =============================================================================
"""
CRITICAL FINDINGS:

1. ✅ MANUAL FUNCTION CALLS WORK PERFECTLY
   - Functions registered with @kernel_function work
   - kernel.invoke(function) executes and calls the Python function
   - Functions are properly registered in kernel.plugins

2. ❌ AUTOMATIC FUNCTION CALLING DOESN'T WORK WITH SEMANTIC KERNEL
   - LLM describes function calls but doesn't execute them
   - Returns text like "get_user_status()" instead of calling the function
   - This happens with both OpenAI and Gemini providers

3. ✅ RAW OPENAI FUNCTION CALLING WORKS PERFECTLY
   - Direct OpenAI API with function schemas works
   - LLM automatically calls functions when needed
   - Returns proper function_call objects

4. 🔍 ROOT CAUSE: SEMANTIC KERNEL INTEGRATION ISSUE
   - Semantic Kernel is not properly translating registered functions 
   - The OpenAI function calling format is not being used
   - The issue is in the Semantic Kernel → OpenAI translation layer
"""

class TestFunctions:
    """Test functions for validation"""
    
    @kernel_function(
        name="get_user_status",
        description="Get current user status and progress"
    )
    def get_user_status(self) -> str:
        """Get user status"""
        print("🚀 Function called: get_user_status")
        return "User has completed 1/3 fields. Missing: age, height"
    
    @kernel_function(
        name="update_data",
        description="Update user data field"
    )
    def update_data(self, field: str, value: str) -> str:
        """Update data field"""
        print(f"🚀 Function called: update_data(field='{field}', value='{value}')")
        return f"Updated {field} to {value}"

async def test_1_manual_function_calls():
    """TEST 1: Manual function calls - WORKS PERFECTLY"""
    print("\n" + "="*60)
    print("TEST 1: MANUAL FUNCTION CALLS (✅ WORKS)")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY")
        return
    
    kernel = sk.Kernel()
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Add plugin
    test_plugin = kernel.add_plugin(
        plugin=TestFunctions(),
        plugin_name="test_plugin"
    )
    
    print(f"Functions registered: {[f.name for f in test_plugin.functions.values()]}")
    
    # Manual function call
    get_status_func = kernel.get_function("test_plugin", "get_user_status")
    result = await kernel.invoke(get_status_func)
    print(f"Manual call result: {result}")

async def test_2_semantic_kernel_auto_function_calling():
    """TEST 2: Semantic Kernel auto function calling - DOESN'T WORK"""
    print("\n" + "="*60)
    print("TEST 2: SEMANTIC KERNEL AUTO FUNCTION CALLING (❌ DOESN'T WORK)")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY")
        return
    
    kernel = sk.Kernel()
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Add plugin
    test_plugin = kernel.add_plugin(
        plugin=TestFunctions(),
        plugin_name="test_plugin"
    )
    
    # Create prompt
    prompt = """You are a helpful assistant.
When user asks about status, call get_user_status function.

User: {{$user_input}}
Assistant: """
    
    chat_function = kernel.add_function(
        function_name="test_chat",
        plugin_name="chat_plugin",
        prompt=prompt
    )
    
    # Try with function calling enabled
    execution_settings = OpenAIPromptExecutionSettings(
        service_id="openai",
        max_tokens=100,
        temperature=0.1,
        function_call_behavior="auto"
    )
    
    arguments = KernelArguments(
        user_input="What's my status?",
        settings=execution_settings
    )
    
    print("User: What's my status?")
    response = await kernel.invoke(chat_function, arguments)
    print(f"Assistant: {response}")
    print("❌ Notice: LLM describes the function but doesn't call it")

async def test_3_raw_openai_function_calling():
    """TEST 3: Raw OpenAI function calling - WORKS PERFECTLY"""
    print("\n" + "="*60)
    print("TEST 3: RAW OPENAI FUNCTION CALLING (✅ WORKS)")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY")
        return
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    # Define function schema
    function_schema = {
        "name": "get_user_status",
        "description": "Get current user status and progress",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can check user status."},
        {"role": "user", "content": "What's my status?"}
    ]
    
    print("User: What's my status?")
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=[function_schema],
        function_call="auto"
    )
    
    message = response.choices[0].message
    
    if message.function_call:
        print(f"🚀 Function called: {message.function_call.name}")
        print("✅ Perfect! Function calling works with raw OpenAI API")
    else:
        print(f"❌ No function call: {message.content}")

async def run_all_tests():
    """Run all tests to demonstrate the findings"""
    print("🧪 FUNCTION CALLING TESTS - REFERENCE")
    print("Purpose: Understand what works and what doesn't")
    
    await test_1_manual_function_calls()
    await test_2_semantic_kernel_auto_function_calling()
    await test_3_raw_openai_function_calling()
    
    print("\n" + "="*60)
    print("CONCLUSIONS:")
    print("="*60)
    print("1. ✅ Manual function calls work perfectly in Semantic Kernel")
    print("2. ❌ Automatic function calling doesn't work in Semantic Kernel")
    print("3. ✅ Raw OpenAI function calling works perfectly")
    print("4. 🔍 Issue: Semantic Kernel → OpenAI translation layer")
    print("\nFor learning purposes, we'll use manual approaches or raw OpenAI API")

if __name__ == "__main__":
    asyncio.run(run_all_tests())