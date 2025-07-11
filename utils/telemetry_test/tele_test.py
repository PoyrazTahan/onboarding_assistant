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
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions import kernel_function

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('telemetry_test.log')
    ]
)

# Get specific loggers
sk_logger = logging.getLogger("semantic_kernel")
root_logger = logging.getLogger()

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
        result = a + b
        print(f"🔢 FUNCTION CALL: add_numbers({a}, {b}) = {result}")
        return f"The sum of {a} and {b} is {result}"
    
    @kernel_function(
        description="Get user information and store it",
        name="store_user_info"
    )
    def store_user_info(self, name: str, age: int) -> str:
        """Store user information"""
        print(f"👤 FUNCTION CALL: store_user_info(name='{name}', age={age})")
        
        # Simple storage to file
        user_data = {"name": name, "age": age}
        with open("user_data.json", "w") as f:
            json.dump(user_data, f)
        
        return f"Stored information: {name}, age {age}"
    
    @kernel_function(
        description="Retrieve stored user information",
        name="get_user_info"
    )
    def get_user_info(self) -> str:
        """Get stored user information"""
        print(f"📋 FUNCTION CALL: get_user_info()")
        
        if os.path.exists("user_data.json"):
            with open("user_data.json", "r") as f:
                data = json.load(f)
            return f"User: {data['name']}, Age: {data['age']}"
        else:
            return "No user data found"

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
    
    # Configure settings for auto function calling
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        temperature=0.7,
        max_tokens=500
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
        "My name is Alice and I'm 30 years old. Can you store that?",
        "What information do you have about me?",
        "Can you add 100 and 200, then tell me my info again?"
    ]
    
    for i, user_input in enumerate(test_inputs):
        print(f"\n{'='*20} CONVERSATION {i+1} {'='*20}")
        print(f"👤 User: {user_input}")
        
        # Log the interaction start
        sk_logger.info(f"Starting conversation {i+1}: {user_input}")
        
        arguments = KernelArguments(
            user_input=user_input,
            settings=settings
        )
        
        # Invoke the kernel function
        response = await kernel.invoke(chat_function, arguments)
        
        # Get response content
        response_text = str(response.value)
        print(f"🤖 Assistant: {response_text}")
        
        # Log the interaction completion
        sk_logger.info(f"Completed conversation {i+1}")
        
        print(f"{'='*60}")
    
    print(f"\n🎉 Telemetry test complete!")
    print(f"📋 Check 'telemetry_test.log' for detailed logs")
    print(f"💾 User data stored in 'user_data.json'")

if __name__ == "__main__":
    asyncio.run(main())