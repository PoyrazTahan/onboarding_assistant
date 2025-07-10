#!/usr/bin/env python3
"""
Simple agent for learning Semantic Kernel basics
Goal: Update data.json through conversation until all fields are filled
"""
#%%
import nest_asyncio
nest_asyncio.apply()

#%%
import os
import json
import asyncio
import sys
from dotenv import load_dotenv
import semantic_kernel as sk

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Import our utilities
from utils.conversation_manager import ConversationManager
from utils.logging_chat_service import LoggingChatService
from utils.data_manager import DataManager

# Check for debug flag
DEBUG_MODE = "--debug" in sys.argv

# Load environment
load_dotenv()

def debug_function_registration(settings, data_plugin, kernel):
    print(f"\n📋 SETTINGS: Function={settings.function_choice_behavior.type_.value.upper()}(max:{settings.function_choice_behavior.maximum_auto_invoke_attempts}) | Temp={settings.temperature or 'def'} | MaxTok={settings.max_tokens or '∞'} | Stream={settings.stream}")
    print(f"✅ Plugin added with functions: {[f.name for f in data_plugin.functions.values()]}")
    
    # Debug function registration details
    print(f"\n🔧 FUNCTION REGISTRATION:")
    for func_name, func in data_plugin.functions.items():
        print(f"   {func_name}: {func.description} | Params: {[p.name for p in func.parameters]}")
    print("\n=== ENHANCED PARAMETER DEBUG ===")
    for func_name, func in data_plugin.functions.items():
        print(f"Function: {func_name}")
        print(f"  - Return type: {func.return_parameter}")
        for param in func.parameters:
            print(f"  Parameter: {param.name}")
            print(f"    - Direct description: {param.description}")
            if hasattr(param, 'default_value') and param.default_value:
                if hasattr(param.default_value, 'description'):
                    print(f"    - InputVariable description: {param.default_value.description}")
    
    
    print("\n=== SK KERNEL INSPECTION ===")
    print(f"Kernel plugins: {list(kernel.plugins.keys())}")
    print(f"Kernel services: {list(kernel.services.keys())}")
    
    # Show registered functions
    print(f"Registered functions:")
    for plugin_name, plugin in kernel.plugins.items():
        funcs = list(plugin.functions.keys())
        print(f"  {plugin_name}: {funcs}")

async def main():
    """Main function to test our simple agent"""
    
    print("🧪 Testing Simple Data Collection Agent...")
    
    # Initialize conversation manager
    conv_manager = ConversationManager()
    print(f"📝 Started conversation session: {conv_manager.session_id}")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add OpenAI service with logging
    chat_service = LoggingChatService(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Connect chat service to conversation manager
    chat_service.set_conversation_manager(conv_manager)
    
    # Add data manager plugin with conversation manager
    data_manager = DataManager(conversation_manager=conv_manager)
    data_plugin = kernel.add_plugin(
        plugin=data_manager,
        plugin_name="data_plugin"
    )
    
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    # Load prompt from file and add current data status
    with open("prompts/prompt.txt", 'r') as f:
        base_prompt = f.read()
    
    # Get current data status and add to prompt
    current_status = data_manager.get_data_status()
    prompt = f"{base_prompt}\n\nCURRENT DATA STATUS:\n{current_status}\n\nUser: {{{{$user_input}}}}\nAssistant: "
    
    print(f"📝 PROMPT LENGTH: {len(prompt)} characters")
    print(f"📊 DATA STATUS: {len([k for k, v in data_manager.load_data().items() if v is not None])}/3 fields filled")
     
    # Create chat function
    chat_function = kernel.add_function(
        function_name="data_chat",
        plugin_name="chat_plugin",
        prompt=prompt
    )

    if DEBUG_MODE:
        debug_function_registration(settings, data_plugin, kernel)
    
    for user_input in ["I am 85"]:
        # Track user message
        conv_manager.add_user_message(user_input)

        print("Testing direct invoke...")
        # Try using KernelArguments to pass settings
        arguments = KernelArguments(
            user_input=user_input,
            settings=settings
        )
        try:
            response = await kernel.invoke(
                chat_function,
                arguments
            )   
        except Exception as e:
            print(f"❌ Invoke Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Get the actual response content
        chat_message = response.value[0]  # First (and only) message
        clean_response = chat_message.content
        
        # Track assistant message with SK response for tool extraction
        conv_manager.add_assistant_message(
            content=clean_response,
            sk_response=response,
            metadata={
                'model': 'gpt-4o-mini',
                'function_choice_behavior': str(settings.function_choice_behavior.type_.value)
            }
        )
        
        # Extract clean response and metrics
        print(f"\n=== API CALL SUMMARY ===")
        # Extract token usage from metadata
        usage = chat_message.metadata.get('usage')
        print(f"📊 TOKEN USAGE:")
        print(f"   INPUT  - Prompt tokens: {usage.prompt_tokens}")
        print(f"   OUTPUT - Completion tokens: {usage.completion_tokens}")
        print(f"          - Reasoning tokens: {usage.completion_tokens_details.reasoning_tokens}")
        print(f"          - Accepted prediction tokens: {usage.completion_tokens_details.accepted_prediction_tokens}")
        
        # Print conversation summary
        summary = conv_manager.get_conversation_summary()
        print(f"\n=== CONVERSATION TRACKING ===")
        print(f"Messages: {summary['user_messages']} user, {summary['assistant_messages']} assistant")
        print(f"Tool calls: {summary['tool_calls']}")
        print(f"Functions used: {summary['functions_used']}")
        
        # Print detailed conversation in turns
        conv_manager.print_conversation_turns()

    
#%%
if __name__ == "__main__":
    asyncio.run(main())

# %%
