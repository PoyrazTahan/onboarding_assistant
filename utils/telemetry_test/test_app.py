#!/usr/bin/env python3
"""
Telemetry test using structured event collection
Separates telemetry collection from the test application
"""

import os
import json
import asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions import kernel_function

# Import the telemetry collector
from telemetry_collector import telemetry

load_dotenv()


class TestPlugin:
    """Test plugin with telemetry integration"""
    
    @kernel_function(
        description="Add two numbers together",
        name="add_numbers"
    )
    def add_numbers(self, a: int, b: int) -> str:
        # Track function execution
        telemetry.function_call_start("add_numbers", {"a": a, "b": b})
        
        result = a + b
        response = f"The sum of {a} and {b} is {result}"
        
        telemetry.function_call_end("add_numbers", response)
        return response
    
    @kernel_function(
        description="Store user information",
        name="store_user_info"
    )
    def store_user_info(self, name: str, age: int) -> str:
        telemetry.function_call_start("store_user_info", {"name": name, "age": age})
        
        user_data = {"name": name, "age": age}
        with open("test_user_data.json", "w") as f:
            json.dump(user_data, f)
        
        response = f"Successfully stored information for {name} (age {age})"
        
        telemetry.function_call_end("store_user_info", response)
        return response
    
    @kernel_function(
        description="Get stored user information",
        name="get_user_info"
    )
    def get_user_info(self) -> str:
        telemetry.function_call_start("get_user_info", {})
        
        if os.path.exists("test_user_data.json"):
            with open("test_user_data.json", "r") as f:
                data = json.load(f)
            response = f"Found user: {data['name']}, Age: {data['age']}"
        else:
            response = "No user data found in storage"
        
        telemetry.function_call_end("get_user_info", response)
        return response


class TelemetryAwareKernel:
    """Wrapper around SK kernel to capture AI interactions"""
    
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def invoke(self, function, arguments):
        # Extract user input for telemetry
        user_input = arguments.get("user_input", "")
        
        # Track AI request
        prompt = f"Processing: {user_input}"
        telemetry.ai_request(prompt, "gpt-4o-mini")
        
        # Call actual kernel
        response = await self.kernel.invoke(function, arguments)
        
        # Track AI response and token usage
        if hasattr(response, 'value') and response.value:
            chat_message = response.value[0] if isinstance(response.value, list) else response.value
            response_text = str(chat_message.content if hasattr(chat_message, 'content') else chat_message)
            
            telemetry.ai_response(response_text, "gpt-4o-mini")
            
            # Track token usage if available
            if hasattr(chat_message, 'metadata') and 'usage' in chat_message.metadata:
                usage = chat_message.metadata['usage']
                telemetry.token_usage(usage.prompt_tokens, usage.completion_tokens, 
                                    usage.prompt_tokens + usage.completion_tokens)
        
        return response


async def main():
    """Test telemetry collection"""
    
    # Clear any previous telemetry data
    telemetry.clear_events()
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add OpenAI service
    api_key = os.getenv("OPENAI_API_KEY")
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Add test plugin
    test_plugin = kernel.add_plugin(
        plugin=TestPlugin(),
        plugin_name="test_plugin"
    )
    
    # Wrap kernel for telemetry
    telemetry_kernel = TelemetryAwareKernel(kernel)
    
    # Configure settings
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create chat function
    prompt = """
You are a helpful assistant that can perform calculations and manage user data.
You have access to functions for:
- Adding numbers
- Storing user information 
- Retrieving user information

Be conversational and use the functions when appropriate.

User: {{$user_input}}
Assistant: """
    
    chat_function = kernel.add_function(
        function_name="telemetry_chat",
        plugin_name="chat_plugin", 
        prompt=prompt
    )
    
    # Test conversations
    test_inputs = [
        "Hi! Can you add 15 and 27 for me?",
        "My name is Alice and I am 30 years old. Can you store that?",
        "What information do you have about me?",
        "Can you add 100 and 200, then tell me my info again?"
    ]
    
    for i, user_input in enumerate(test_inputs):
        conversation_id = f"conv_{i+1}"
        
        # Start conversation tracking
        telemetry.conversation_start(conversation_id, user_input)
        
        arguments = KernelArguments(
            user_input=user_input,
            settings=settings
        )
        
        # Process through telemetry-aware kernel
        response = await telemetry_kernel.invoke(chat_function, arguments)
        
        # Get response text
        if hasattr(response, 'value') and response.value:
            chat_message = response.value[0] if isinstance(response.value, list) else response.value
            response_text = str(chat_message.content if hasattr(chat_message, 'content') else chat_message)
        else:
            response_text = str(response.value)
        
        # End conversation tracking
        telemetry.conversation_end(conversation_id, response_text)
    
    # Save telemetry data
    telemetry.to_log_file("telemetry_structured.log")
    telemetry.to_json_file("telemetry_data.json")
    
    print(f"Telemetry collection complete!")
    print(f"📄 Human-readable log: telemetry_structured.log")
    print(f"📊 Structured data: telemetry_data.json")
    print(f"📈 Total events collected: {len(telemetry.get_events())}")


if __name__ == "__main__":
    asyncio.run(main())