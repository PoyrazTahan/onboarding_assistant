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
import hashlib

# Check for debug and test flags FIRST
DEBUG_MODE = "--debug" in sys.argv
TEST_MODE = "--test" in sys.argv

# Import telemetry BEFORE any SK imports to capture everything
from utils.telemetry_collector import telemetry

# Enable telemetry logging immediately if in debug mode
if DEBUG_MODE:
    telemetry.enable_logging()
    print("📊 Telemetry logging enabled - capturing all SK operations")

# Now import SK-related modules
from semantic_kernel.functions.kernel_arguments import KernelArguments
from utils.session_manager import Session
from kernel_setup import setup_kernel, get_available_functions

async def main():
    """Main function to test our simple agent"""
    
    print("🧪 Testing Simple Data Collection Agent...")
    
    # Initialize session
    session = Session()
    print(f"📝 Started session: {session.id}")
    
    # Setup kernel and components (telemetry already enabled if needed)
    kernel, data_manager, settings = setup_kernel(debug_mode=DEBUG_MODE)
    
    # Load base prompt from file - using reasoning-based prompt
    try:
        with open("prompts/reasoning_prompt.txt", 'r') as f:
            base_prompt = f.read()
    except FileNotFoundError:
        # Fallback to original prompt if new one doesn't exist
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

    # Conversation loop - support multiple interactions
    if TEST_MODE:
        inputs = ["Hello, I need help filling out my data.", "I'm 25 years old", "I weigh 70kg"]
        print("🧪 Running in TEST MODE with predefined inputs")
    else:
        inputs = []  # Will be populated by interactive input later
        print("💬 Running in INTERACTIVE MODE")
    
    for i, user_input in enumerate(inputs):
        print(f"\n👤 User: {user_input}")
        
        # Start conversation tracking in telemetry
        if DEBUG_MODE:
            telemetry.conversation_start(f"turn_{i+1}", user_input)
        
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
            # Track prompt in telemetry (initial or evolved)
            if i == 0:
                telemetry.prompt_initial(prompt, hashlib.md5(prompt.encode()).hexdigest()[:8])
            else:
                telemetry.prompt_evolved(
                    original_hash=hashlib.md5(base_prompt.encode()).hexdigest()[:8],
                    evolved_messages=prompt,
                    additions=f"conversation_turn_{i+1}",
                    message_count=i+1
                )
        
        # Create chat function with updated prompt
        chat_function = kernel.add_function(
            function_name=f"data_chat_{i}",  # Make function name unique for each iteration
            plugin_name="chat_plugin",
            prompt=prompt
        )
        
        # Process user input
        # Get available functions for context
        available_functions = get_available_functions(kernel)
        
        # Start AI block with full context
        block_id = session.start_ai_block(
            user_input=user_input,
            full_prompt=prompt.replace("{{$user_input}}", user_input),
            functions_available=available_functions,
            data_snapshot=data.copy()
        )
        
        # Update data manager with current block
        data_manager.session = session
        data_manager.current_block_id = block_id
        
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
        
        # Extract function calls from response and add to session
        if hasattr(response, 'value'):
            messages = response.value if isinstance(response.value, list) else [response.value]
            for message in messages:
                if hasattr(message, 'items'):
                    for item in message.items:
                        if hasattr(item, 'function_call_result'):
                            result = item.function_call_result
                            
                            # Extract arguments if available
                            args = {}
                            if hasattr(item, 'function_call') and hasattr(item.function_call, 'arguments'):
                                try:
                                    import json
                                    args = json.loads(item.function_call.arguments)
                                except:
                                    pass
                            
                            # Add to session block
                            session.add_action_to_block(
                                block_id,
                                result.function_name,
                                args,
                                result.result
                            )
        
        # Process response in telemetry if debug mode
        if DEBUG_MODE:
            telemetry.process_kernel_response(response, user_input, {
                "model": "gpt-4o-mini",
                "conversation_turn": i + 1,
                "data_state": data.copy(),
                "prompt_length": len(prompt)
            })
            
            # Extract token usage from metadata and add to session
            usage = chat_message.metadata.get('usage')
            if usage:
                session.add_token_usage(block_id, usage.prompt_tokens, usage.completion_tokens)
            
            # End conversation in telemetry
            telemetry.conversation_end(f"turn_{i+1}", clean_response)
        
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
    
    # Save telemetry if enabled
    if DEBUG_MODE:
        os.makedirs("data/telemetry", exist_ok=True)
        
        # Print prompt evolution (as requested to keep)
        print("\n🔄 PROMPT EVOLUTION")
        print("=" * 60)
        
        prompt_events = [e for e in telemetry.get_events() if e['type'] in ['PROMPT_INITIAL', 'PROMPT_EVOLVED']]
        for i, event in enumerate(prompt_events):
            timestamp = event['timestamp'].split('T')[1][:8]
            if event['type'] == 'PROMPT_INITIAL':
                print(f"\n{i+1}. [{timestamp}] INITIAL (hash: {event['data']['prompt_hash']})")
                print(f"   Length: {event['data']['prompt_length'] if 'prompt_length' in event['data'] else len(event['data']['full_messages'])} chars")
                # Show preview of initial prompt
                preview = event['data']['user_content'][:200] + "..." if len(event['data']['user_content']) > 200 else event['data']['user_content']
                print(f"   Preview: {preview}")
            else:
                print(f"\n{i+1}. [{timestamp}] EVOLVED (hash: {event['data']['evolved_hash']})")
                print(f"   Length: {len(event['data']['evolved_messages'])} chars")
                print(f"   Changes: {event['data']['additions']}")
        
        # Save telemetry outputs
        telemetry.to_timestamped_log("data/telemetry/telemetry")
        telemetry.to_json_file("data/telemetry/telemetry_data.json")
        
        # Get traditional log filename
        traditional_log = telemetry.get_traditional_log_filename()
        
        print("\n\n📊 TELEMETRY SAVED")
        print("=" * 40)
        print(f"📄 Structured log: data/telemetry/telemetry_structured_*.log")
        print(f"📊 Structured data: data/telemetry/telemetry_data.json")
        print(f"🔍 Traditional SK dump: {traditional_log}")
        print(f"📈 Total events collected: {len(telemetry.get_events())}")

    
#%%
if __name__ == "__main__":
    asyncio.run(main())

# %%
