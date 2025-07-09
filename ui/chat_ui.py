import os
import textwrap

def get_terminal_width():
    """Get terminal width, default to 80 if can't detect"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def print_user_message(message):
    """Print user message aligned to the left with fixed width"""
    FIXED_WIDTH = 100  # Fixed terminal width for consistent formatting
    max_width = 50      # Max width for message content
    
    # Wrap text
    wrapped = textwrap.fill(message, width=max_width)
    lines = wrapped.split('\n')
    
    print()
    print("👤 Sen:")
    for line in lines:
        print(f"   {line}")

def print_agent_message(message):
    """Print agent message aligned to the right with fixed width"""
    # Convert message to string if it's not already
    message_str = str(message)
    
    FIXED_WIDTH = 100  # Fixed terminal width for consistent formatting  
    max_width = 50     # Max width for message content
    
    # Wrap text
    wrapped = textwrap.fill(message_str, width=max_width)
    lines = wrapped.split('\n')
    
    print()
    print("🤖 Asistan:".rjust(FIXED_WIDTH - 5))
    for line in lines:
        print(f"{line}".rjust(FIXED_WIDTH - 3))

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
    return input("💬 Mesajınız: ").strip()

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

