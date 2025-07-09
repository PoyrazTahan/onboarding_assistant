import asyncio
import sys
import os
import warnings

# Suppress Google AI SDK enum warnings for Gemini 2.5-flash compatibility
warnings.filterwarnings('ignore', message='Unrecognized FinishReason enum value')

# Add project root to path
project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

from agents.health_agent import HealthAgent
from ui.chat_ui import (
    print_welcome, print_user_message, print_agent_message,
    print_system_message, print_update_message, get_user_input,
    clear_screen
)

async def main():
    """Main entry point for the health assistant"""
    agent = HealthAgent()
    
    try:
        # Initialize agent
        await agent.initialize()
        
        # Clear screen and show welcome
        clear_screen()
        print_welcome()
        
        # Assistant starts the conversation
        print_system_message("Asistan konuşmayı başlatıyor...")
        initial_response = await agent.chat("Merhaba", "")
        print_agent_message(initial_response)
        
        while True:
            try:
                # Get user input
                user_input = get_user_input()
                
                if user_input.lower() in ['quit', 'exit', 'çıkış']:
                    print_system_message("👋 Görüşürüz!")
                    break
                
                # Show user message
                print_user_message(user_input)
                
                # Get agent response
                response = await agent.chat(user_input, "")
                
                # Show agent response
                print_agent_message(response)
                
            except KeyboardInterrupt:
                print_system_message("👋 Görüşürüz!")
                break
            except Exception as e:
                print_system_message(f"❌ Hata: {e}")
                break
        
        # Print session info and conversation history
        print()
        session_info = agent.conversation_manager.get_current_session_info()
        print_system_message(f"📞 Oturum Bilgisi: {session_info['session_id']} ({session_info['message_count']} mesaj)")
        conversation_export = agent.conversation_manager.export_conversation()
        print(conversation_export)
        
        # Print usage summary
        print()
        agent.print_summary()
        
    except Exception as e:
        print_system_message(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())