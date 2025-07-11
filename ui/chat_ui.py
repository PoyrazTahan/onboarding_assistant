import os
import textwrap

def get_terminal_width():
    """Get terminal width, default to 80 if can't detect"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def print_user_message(message):
    """Print user message aligned to the right"""
    terminal_width = get_terminal_width()
    max_width = 50      # Max width for message content
    
    # Wrap text
    wrapped = textwrap.fill(message, width=max_width)
    lines = wrapped.split('\n')
    
    print()
    # Right-align the header
    header = "You:"
    print(f"{header:>{terminal_width}}")
    
    # Right-align each line
    for line in lines:
        print(f"{line:>{terminal_width}}")

def print_agent_message(message):
    """Print agent message aligned to the left with fixed width"""
    # Convert message to string if it's not already
    message_str = str(message)
    
    FIXED_WIDTH = 100  # Fixed terminal width for consistent formatting  
    max_width = 50     # Max width for message content
    
    # Wrap text
    wrapped = textwrap.fill(message_str, width=max_width)
    lines = wrapped.split('\n')
    
    print()
    print("🤖 Asistan:")
    for line in lines:
        print(f"   {line}")

def print_system_message(message):
    """Print system message centered"""
    width = get_terminal_width()
    print()
    print("=" * width)
    print(message.center(width))
    print("=" * width)

def print_update_message(message):
    """Print data update message"""
    print(f"🔄 {message}")

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome():
    """Print welcome message"""
    width = get_terminal_width()
    welcome_text = "🎉 Sağlık Asistanı'na hoş geldiniz!"
    print()
    print("=" * width)
    print(welcome_text.center(width))
    print("Çıkmak için 'quit', 'exit' veya 'çıkış' yazın".center(width))
    print("=" * width)
    print()

def get_user_input():
    """Get user input with nice prompt"""
    print()
    user_input = input("💬 Mesajınız: ").strip()
    # Clear the input line after getting input
    print("\033[F\033[K", end="")  # Move cursor up and clear line
    return user_input

def print_widget_interface():
    """Print centered widget interface separator"""
    width = get_terminal_width()
    separator = "<<<<<< WIDGET >>>>>>"
    print()
    print("=" * width)
    print(separator.center(width))
    print("=" * width)

def print_widget_completed():
    """Print widget completion message"""
    width = get_terminal_width()
    separator = "<<<<<< WIDGET TAMAMLANDI >>>>>>"
    print("=" * width)
    print(separator.center(width))
    print("=" * width)

def print_thinking_indicator():
    """Print thinking indicator for agent processing"""
    print()
    print("🤖 Asistan düşünüyor...")
    
def clear_thinking_indicator():
    """Clear the thinking indicator line"""
    print("\033[F\033[K", end="")  # Move cursor up and clear line


class ConversationHandler:
    """Handles conversation flow with nice UI formatting"""
    
    def __init__(self, agent):
        self.agent = agent
        # Clear contract - only use these specific methods from agent
        self._process_input = agent.process_user_input
        self._is_complete = agent.is_conversation_complete
        self._get_greeting = agent.handle_initial_greeting
        
    async def run_test_mode(self, test_inputs):
        """Run conversation with predefined test inputs"""
        print_system_message("🧪 Running in TEST MODE")
        
        # Handle initial greeting
        greeting = self._get_greeting()
        if greeting:
            print_agent_message(greeting)
        
        # Process each test input
        for i, user_input in enumerate(test_inputs):
            print_user_message(user_input)
            
            # Process input through agent
            response = await self._process_input(user_input, turn_number=i)
            print_agent_message(response)
            
            # Check if conversation is complete
            if self._is_complete():
                print_system_message("✅ All data collected! Conversation complete.")
                break
    
    async def run_interactive_mode(self):
        """Run interactive conversation with user input"""
        print_welcome()
        
        # Handle initial greeting
        greeting = self._get_greeting()
        if greeting:
            print_agent_message(greeting)
        
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
                print_agent_message(response)
                
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
    
    async def run_conversation(self, test_mode=False, test_inputs=None):
        """Main conversation orchestrator"""
        if test_mode and test_inputs:
            await self.run_test_mode(test_inputs)
        else:
            await self.run_interactive_mode()

