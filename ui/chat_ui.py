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

def print_widget_box(question_text, options, selected_option=None):
    """Print entire widget content in a nice box"""
    print()
    print("    ┌─────────────────────────────────────────┐")
    print("    │              🎛️  WIDGET UI               │")
    print("    ├─────────────────────────────────────────┤")
    print(f"    │ 📝 {question_text[:34]:<34}   │")
    print("    │                                         │")
    print("    │ Seçenekler:                             │")
    
    for i, option in enumerate(options, 1):
        if selected_option and option == selected_option:
            print(f"    │ {i:2}) {option:<32} ✅ │")
        else:
            print(f"    │ {i:2}) {option:<34}  │")
    
    print("    │                                         │")
    print("    └─────────────────────────────────────────┘")
    
    if selected_option:
        print(f"    ✅ Seçiminiz: {selected_option}")
        print()

def print_widget_interface():
    """Print widget interface header - kept for compatibility"""
    pass  # This will be replaced by print_widget_box

def print_widget_completed():
    """Print widget completion message"""
    pass  # This will be handled by print_widget_box with selected_option

def print_thinking_indicator():
    """Print thinking indicator for agent processing"""
    print()
    print("🤖 Asistan düşünüyor...")
    
def clear_thinking_indicator():
    """Clear the thinking indicator line"""
    print("\033[F\033[K", end="")  # Move cursor up and clear line



