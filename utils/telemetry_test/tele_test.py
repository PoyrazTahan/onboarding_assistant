#!/usr/bin/env python3
"""
Simple telemetry test for Semantic Kernel
Goal: Test logging, metrics, and tracing capabilities
"""

import os
import json
import asyncio
import logging
import sys
import html
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions import kernel_function

# Set up comprehensive logging for maximum debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('telemetry_test.log')
    ]
)

# Configure all SK loggers for maximum verbosity
sk_loggers = [
    "semantic_kernel",
    "semantic_kernel.kernel", 
    "semantic_kernel.functions",
    "semantic_kernel.connectors",
    "semantic_kernel.connectors.ai.open_ai",
    "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion",
    "semantic_kernel.functions.kernel_function"
]

for logger_name in sk_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

# Main logger
sk_logger = logging.getLogger("semantic_kernel")

# Load environment
load_dotenv()

class SimpleTestPlugin:
    """Simple plugin with a few functions for testing telemetry"""
    
    @kernel_function(
        description="Add two numbers together",
        name="add_numbers"
    )
    def add_numbers(self, a: int, b: int) -> str:
        """Add two numbers and return the result"""
        print(f"\n🔢 FUNCTION START: add_numbers(a={a}, b={b})")
        result = a + b
        response = f"The sum of {a} and {b} is {result}"
        print(f"🔢 FUNCTION RESULT: {response}")
        
        # Log function execution details
        sk_logger.debug(f"Function add_numbers executed: {a} + {b} = {result}")
        
        return response
    
    @kernel_function(
        description="Get user information and store it",
        name="store_user_info"
    )
    def store_user_info(self, name: str, age: int) -> str:
        """Store user information"""
        print(f"\n👤 FUNCTION START: store_user_info(name='{name}', age={age})")
        
        # Simple storage to file
        user_data = {"name": name, "age": age}
        with open("user_data.json", "w") as f:
            json.dump(user_data, f)
        
        response = f"Successfully stored information for {name} (age {age})"
        print(f"👤 FUNCTION RESULT: {response}")
        
        # Log function execution details  
        sk_logger.debug(f"Function store_user_info executed: stored {user_data}")
        
        return response
    
    @kernel_function(
        description="Retrieve stored user information",
        name="get_user_info"
    )
    def get_user_info(self) -> str:
        """Get stored user information"""
        print(f"\n📋 FUNCTION START: get_user_info()")
        
        if os.path.exists("user_data.json"):
            with open("user_data.json", "r") as f:
                data = json.load(f)
            response = f"Found user: {data['name']}, Age: {data['age']}"
        else:
            response = "No user data found in storage"
        
        print(f"📋 FUNCTION RESULT: {response}")
        
        # Log function execution details
        sk_logger.debug(f"Function get_user_info executed: {response}")
        
        return response

async def main():
    """Main function to test telemetry"""
    
    print("🔍 Testing Semantic Kernel Telemetry...")
    print("=" * 50)
    
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
    
    # Add our test plugin
    test_plugin = kernel.add_plugin(
        plugin=SimpleTestPlugin(),
        plugin_name="test_plugin"
    )
    
    # Configure settings for auto function calling with debug info
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        temperature=0.7,
        max_tokens=1000  # Increased to capture more model thinking
    )
    
    print(f"✅ Added plugin with functions: {[f.name for f in test_plugin.functions.values()]}")
    
    # Simple prompt template
    prompt = """
You are a helpful assistant that can perform calculations and manage user data.
You have access to functions for:
- Adding numbers
- Storing user information 
- Retrieving user information

Be conversational and use the functions when appropriate.

User: {{$user_input}}
Assistant: """
    
    # Create chat function
    chat_function = kernel.add_function(
        function_name="telemetry_chat",
        plugin_name="chat_plugin", 
        prompt=prompt
    )
    
    # Test conversations that will trigger different functions
    test_inputs = [
        "Hi! Can you add 15 and 27 for me?",
        "My name is Alice and I am 30 years old. Can you store that?",  # Changed I'm to I am
        "What information do you have about me?",
        "Can you add 100 and 200, then tell me my info again?"
    ]
    
    for i, user_input in enumerate(test_inputs):
        print(f"\n{'='*20} CONVERSATION {i+1} {'='*20}")
        
        # Decode HTML entities to fix corrupted characters
        clean_input = html.unescape(user_input)
        print(f"👤 User: {clean_input}")
        
        # Log the interaction start with full context
        sk_logger.info(f"=== STARTING CONVERSATION {i+1} ===")
        sk_logger.info(f"User input: {clean_input}")
        sk_logger.debug(f"Available functions: {[f.name for f in test_plugin.functions.values()]}")
        
        arguments = KernelArguments(
            user_input=clean_input,
            settings=settings
        )
        
        print(f"\n🧠 MODEL PROCESSING...")
        
        # Invoke the kernel function
        response = await kernel.invoke(chat_function, arguments)
        
        # Extract detailed response information
        if hasattr(response, 'value') and response.value:
            # Get the chat message with all metadata
            chat_message = response.value[0] if isinstance(response.value, list) else response.value
            
            # Print model's final response
            response_text = str(chat_message.content if hasattr(chat_message, 'content') else chat_message)
            print(f"🤖 Assistant: {response_text}")
            
            # Debug: Print all metadata if available
            if hasattr(chat_message, 'metadata') and chat_message.metadata:
                print(f"\n📊 DEBUG METADATA:")
                for key, value in chat_message.metadata.items():
                    print(f"   {key}: {value}")
            
            # Log token usage if available
            if hasattr(chat_message, 'metadata') and 'usage' in chat_message.metadata:
                usage = chat_message.metadata['usage']
                print(f"\n💰 TOKEN USAGE: Input={usage.prompt_tokens} | Output={usage.completion_tokens} | Total={usage.prompt_tokens + usage.completion_tokens}")
                sk_logger.info(f"Token usage - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}")
        else:
            response_text = str(response.value)
            print(f"🤖 Assistant: {response_text}")
        
        # Log the interaction completion
        sk_logger.info(f"Assistant response: {response_text}")
        sk_logger.info(f"=== COMPLETED CONVERSATION {i+1} ===")
        
        print(f"{'='*60}")
    
    print(f"\n🎉 Telemetry test complete!")
    print(f"📋 Check 'telemetry_test.log' for detailed logs")
    print(f"💾 User data stored in 'user_data.json'")

if __name__ == "__main__":
    asyncio.run(main())