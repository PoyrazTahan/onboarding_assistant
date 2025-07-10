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
from utils.session_manager import Session
from utils.logging_service import LoggingService
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
    
    # Initialize session
    session = Session()
    print(f"📝 Started session: {session.id}")
    
    # Initialize data manager first
    data_manager = DataManager()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add OpenAI service with logging
    chat_service = LoggingService(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Connect chat service to session
    chat_service.__dict__['session'] = session
    
    # Add data plugin
    data_plugin = kernel.add_plugin(
        plugin=data_manager,
        plugin_name="data_plugin"
    )
    
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    # Load base prompt from file
    with open("prompts/prompt.txt", 'r') as f:
        base_prompt = f.read()
    
    # Initial setup - check if greeting is needed
    data = data_manager.load_data()
    has_data = any(value is not None for value in data.values())
    
    if has_data:
        initial_greeting = "Can I ask you a few more questions to understand you better?"
    else:
        initial_greeting = "Hey there! I am Nora do you have couple of minutes for me to ask you couple of questions?"
    
    # Check if this is first interaction (no blocks yet)
    if not session.blocks:
        # Add programmatic greeting block
        session.add_programmatic_block(initial_greeting, block_type="greeting")
        print(f"\n🤖 Assistant: {initial_greeting}")

    if DEBUG_MODE:
        debug_function_registration(settings, data_plugin, kernel)
    
    # Conversation loop - support multiple interactions
    test_inputs = ["Hello, I need help filling out my data.", "I'm 25 years old", "I weigh 70kg"]
    
    for i, user_input in enumerate(test_inputs):
        print(f"\n👤 User: {user_input}")
        
        # Reload data to get latest state
        data = data_manager.load_data()
        current_status = data_manager.get_data_status()
        
        # Update session's data state
        session.data_state = data.copy()
        
        # Get updated conversation history
        conversation_history = session.get_conversation_history()
        
        # Build prompt with current state
        prompt = f"{base_prompt}\n\nCONVERSATION HISTORY:\n{conversation_history}\n\nCURRENT DATA STATUS:\n{current_status}\n\nUser: {{{{$user_input}}}}\nAssistant: "
        
        if DEBUG_MODE:
            print(f"\n📝 PROMPT LENGTH: {len(prompt)} characters")
            print(f"📊 DATA STATUS: {len([k for k, v in data.items() if v is not None])}/3 fields filled")
        
        # Create chat function with updated prompt
        chat_function = kernel.add_function(
            function_name=f"data_chat_{i}",  # Make function name unique for each iteration
            plugin_name="chat_plugin",
            prompt=prompt
        )
        
        # Process user input
        # Get available functions for context
        available_functions = []
        for plugin_name, plugin in kernel.plugins.items():
            if plugin_name != 'chat_plugin':
                available_functions.extend(list(plugin.functions.keys()))
        
        # Start AI block with full context
        block_id = session.start_ai_block(
            user_input=user_input,
            full_prompt=prompt.replace("{{$user_input}}", user_input),
            functions_available=available_functions,
            data_snapshot=data.copy()
        )
        
        # Update data manager and chat service with current block
        data_manager.session = session
        data_manager.current_block_id = block_id
        chat_service.__dict__['current_block_id'] = block_id
        
        if DEBUG_MODE:
            print(f"\n\nFULL PROMPT:\n======================")
            print(prompt)
            print("======================\n")
        
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
            continue
        
        # Get the actual response content
        chat_message = response.value[0]  # First (and only) message
        clean_response = chat_message.content
        
        # Complete the AI block
        session.complete_ai_block(block_id, str(response.value), clean_response)
        
        # Print assistant response
        print(f"🤖 Assistant: {clean_response}")
        
        if DEBUG_MODE:
            # Extract token usage from metadata
            usage = chat_message.metadata.get('usage')
            print(f"\n📊 TOKEN USAGE:")
            print(f"   INPUT: {usage.prompt_tokens} | OUTPUT: {usage.completion_tokens} | TOTAL: {usage.prompt_tokens + usage.completion_tokens}")
        
        # Stop if all data is collected
        data = data_manager.load_data()
        if all(value is not None for value in data.values()):
            print("\n✅ All data collected! Conversation complete.")
            break
        
    
    # Print final session flow
    session.print_session_flow()
    
    # Save session for debugging
    os.makedirs("data/sessions", exist_ok=True)
    session.save_to_file()
    print(f"\n💾 Session saved to: data/sessions/{session.id}.json")

    
#%%
if __name__ == "__main__":
    asyncio.run(main())

# %%
