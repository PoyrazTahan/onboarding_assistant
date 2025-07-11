#!/usr/bin/env python3
"""
CLI Application - Simple interface for the data collection agent
Handles command line arguments, user input/output, and debug setup
"""
#%%
import nest_asyncio
nest_asyncio.apply()

#%%
import os
import asyncio
import sys

# Check for debug and test flags FIRST
DEBUG_MODE = "--debug" in sys.argv
TEST_MODE = "--test" in sys.argv

# Import telemetry BEFORE any SK imports to capture everything
from monitoring.telemetry import telemetry

# Enable telemetry logging immediately if in debug mode
if DEBUG_MODE:
    telemetry.enable_logging()
    print("📊 Telemetry logging enabled - capturing all SK operations")

# Now import agent and conversation handler
from core.agent import Agent
from ui.chat_ui import ConversationHandler


async def main():
    """Main CLI application function"""
    
    print("🧪 Testing Simple Data Collection Agent...")
    
    # Initialize agent
    agent = Agent(debug_mode=DEBUG_MODE)
    await agent.initialize()
    
    # Start session
    session = agent.start_session()
    
    # Create conversation handler
    conversation_handler = ConversationHandler(agent)
    
    # Setup test inputs if in test mode
    test_inputs = ["Hello, I need help filling out my data.", "I'm 25 years old", "I weigh 70kg"] if TEST_MODE else None
    
    # Run conversation
    await conversation_handler.run_conversation(test_mode=TEST_MODE, test_inputs=test_inputs)
    
    # Print final session flow
    session.print_session_flow()
    
    # Update session end state before saving
    final_data = agent.data_manager.load_data()
    session.update_session_end_state(final_data)
    
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