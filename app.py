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
CORE_AGENT_MODE = "--core-agent" in sys.argv

# Import telemetry BEFORE any SK imports to capture everything
from monitoring.telemetry import telemetry

# Enable telemetry logging immediately if in debug mode
if DEBUG_MODE:
    telemetry.enable_logging()
    print("📊 Telemetry logging enabled - capturing all SK operations")

# Now import agent and UI functions
from core.agent import Agent
from core.turkish_persona_agent import TurkishPersonaAgent
from ui.chat_ui import (print_system_message, print_agent_message, print_user_message, 
                       print_welcome, get_user_input, print_thinking_indicator, 
                       clear_thinking_indicator)
import json
import re


class ConversationHandler:
    """Handles conversation flow and test automation"""
    
    def __init__(self, agent):
        self.agent = agent
        self.turkish_agent = None  # Lazy load
        self._process_input = agent.process_user_input
        self._is_complete = agent.is_conversation_complete
        self._get_greeting = agent.handle_initial_greeting
    
    async def _display_agent_message(self, english_response):
        """Route through Turkish agent or show raw response based on flags"""
        if not english_response or not english_response.strip():
            return
        
        # Core agent mode - bypass Turkish agent for debugging
        if CORE_AGENT_MODE:
            print_agent_message(english_response)
            return
        
        # Lazy load Turkish agent
        if self.turkish_agent is None:
            self.turkish_agent = TurkishPersonaAgent()
            await self.turkish_agent.initialize()
        
        # Get session context
        session = self.agent.get_session()
        
        # Process with context and get multiple messages
        turkish_messages = await self.turkish_agent.translate_to_persona(english_response, session)
        
        # Display each message separately (simulating WhatsApp conversation)
        for message in turkish_messages:
            print_agent_message(message)
    
    def _execute_widget_and_get_user_input(self, widget_info):
        """Execute widget and return what should be the next user input"""
        try:
            # Initialize widget handler
            from ui.widget_handler import WidgetHandler
            widget_handler = WidgetHandler()
            
            # Execute widget and get selection
            selected_value = widget_handler.show_widget_interface(widget_info["question_structure"])
            
            if selected_value:
                # Auto-call update_data with selected value
                update_result = self.agent.data_manager.update_data(widget_info["field"], selected_value)
                print(f"    ✅ WIDGET: Auto-updated {widget_info['field']} = {selected_value}")
                
                # Store completion info for hidden LLM context injection
                widget_completion = {
                    "field": widget_info["field"],
                    "selected_value": selected_value,
                    "update_result": update_result
                }
                
                # Store in session for next LLM call context injection
                session = self.agent.get_session()
                session.stage_manager.widget_completion = widget_completion
                
                # Return the value as user input for the next block
                return selected_value
            else:
                # Widget cancelled - continue with fallback
                return None
                
        except Exception as e:
            error_msg = f"Widget execution error: {e}"
            print(f"    ❌ WIDGET ERROR: {error_msg}")
            return None

    async def _process_pending_widgets(self, turn_number):
        """Process any pending widgets using tail recursion (no loops)"""
        session = self.agent.get_session()
        widget_info = session.stage_manager.get_pending_widget()
        
        if not widget_info:
            return turn_number
            
        selected_value = self._execute_widget_and_get_user_input(widget_info)
        
        if not selected_value:
            return turn_number
            
        # Process widget selection
        print_user_message(selected_value)
        print_thinking_indicator()
        response = await self._process_input(selected_value, turn_number=turn_number+1)
        clear_thinking_indicator()
        await self._display_agent_message(response)
        
        # Tail recursion: check for more widgets
        return await self._process_pending_widgets(turn_number + 1)

    
    async def run_test_mode(self):
        """Run conversation with stage manager real-time detection"""
        print_system_message("🧪 Running in TEST MODE with stage manager")
        
        # Enable test mode on session's stage manager
        session = self.agent.get_session()
        session.stage_manager.enable_test_mode()
        
        # Handle initial greeting
        greeting = self._get_greeting()
        if greeting:
            await self._display_agent_message(greeting)
        
        # Start with initial greeting response
        user_input = "Hello, I need help filling out my data."
        turn_number = 0
        
        while not self._is_complete() and turn_number < 10:  # Safety limit
            print_user_message(user_input)
            
            # Process input through agent (function call hooks trigger during this)
            response = await self._process_input(user_input, turn_number=turn_number)
            # print(f"🔍 DEBUG: Full AI response: '{response}'")
            await self._display_agent_message(response)
            
            # Check if conversation is complete
            if self._is_complete():
                print_system_message("✅ All data collected! Conversation complete.")
                break
            
            # Check for pending widget first (highest priority)
            widget_info = session.stage_manager.get_pending_widget()
            if widget_info:
                # Execute widget after LLM response is shown
                selected_value = self._execute_widget_and_get_user_input(widget_info)
                if selected_value:
                    user_input = selected_value
                    print(f"    🎛️ WIDGET: Selected '{selected_value}', using as next user input")
                else:
                    user_input = "Please continue"
            else:
                # Check for test mode automation  
                test_response = session.stage_manager.get_pending_test_response()
                
                if test_response:
                    print(f"    🎯 TEST MODE: Detected question, next input will be: '{test_response}'")
                    user_input = test_response
                else:
                    # Only use fallback if we genuinely have no test response
                    print(f"    🤖 TEST MODE: No question detected, continuing conversation")
                    user_input = "Please continue, try to use available functions_calls correctly."
            
            turn_number += 1
    
    async def run_interactive_mode(self):
        """Run interactive conversation with user input"""
        print_welcome()
        
        # Handle initial greeting
        greeting = self._get_greeting()
        if greeting:
            await self._display_agent_message(greeting)
        
        turn_number = 0
        while not self._is_complete():
            try:
                # Get user input
                user_input = get_user_input()
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'çıkış']:
                    print_system_message("👋 Görüşürüz!")
                    break
                
                # Skip empty inputs
                if not user_input.strip():
                    continue
                
                # Display user message
                print_user_message(user_input)
                
                # Show thinking indicator
                print_thinking_indicator()
                
                # Process input through agent
                response = await self._process_input(user_input, turn_number=turn_number)
                
                # Clear thinking indicator and show response
                clear_thinking_indicator()
                await self._display_agent_message(response)
                
                # Check for pending widget after LLM response
                session = self.agent.get_session()
                widget_info = session.stage_manager.get_pending_widget()
                if widget_info:
                    # Execute widget after LLM response is shown
                    selected_value = self._execute_widget_and_get_user_input(widget_info)
                    
                    if selected_value:
                        # Continue with next turn automatically using widget selection
                        print_user_message(selected_value)
                        print_thinking_indicator()
                        
                        # Process widget selection as user input in next block
                        next_response = await self._process_input(selected_value, turn_number=turn_number+1)
                        clear_thinking_indicator()
                        await self._display_agent_message(next_response)
                        
                        # Check for additional widgets after processing widget selection
                        turn_number = await self._process_pending_widgets(turn_number + 1)
                        
                        turn_number += 1  # Extra increment for widget turn
                
                turn_number += 1
                
            except KeyboardInterrupt:
                print_system_message("\n👋 Görüşürüz!")
                break
            except Exception as e:
                print_system_message(f"❌ Hata: {e}")
                continue
        
        # Final completion message if conversation finished naturally
        if self._is_complete():
            print_system_message("✅ Tüm bilgiler toplandı! Konuşma tamamlandı.")
    
    async def run_conversation(self):
        """Main conversation orchestrator"""
        if TEST_MODE:
            await self.run_test_mode()
        else:
            await self.run_interactive_mode()


async def main():
    """Main CLI application function"""
    
    # Show mode indicators
    mode_flags = []
    if TEST_MODE: mode_flags.append("TEST")
    if DEBUG_MODE: mode_flags.append("DEBUG") 
    if CORE_AGENT_MODE: mode_flags.append("CORE-AGENT")
    
    mode_str = f" ({' + '.join(mode_flags)})" if mode_flags else ""
    print(f"🧪 Data Collection Agent{mode_str}")
    
    if CORE_AGENT_MODE:
        print("⚙️ Core Agent Mode: Raw English responses with function calls")
    elif not TEST_MODE:
        print("🇹🇷 Turkish Persona Mode: Empathetic Turkish responses")
    
    # Initialize agent
    agent = Agent(debug_mode=DEBUG_MODE)
    await agent.initialize()
    
    # Start session
    session = agent.start_session()
    
    # Create conversation handler
    conversation_handler = ConversationHandler(agent)
    
    # Run conversation
    await conversation_handler.run_conversation()
    
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