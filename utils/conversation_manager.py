#!/usr/bin/env python3
"""
Simple conversation manager - just tracks messages and function calls
No complex types, no dataclasses, just functional
"""
import datetime
import json

class ConversationManager:
    def __init__(self):
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.messages = []
        
    def add_message(self, role, content, function_calls=None):
        """Add any message to the conversation"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat(),
            'function_calls': function_calls or []
        }
        self.messages.append(message)
        
    def add_function_call(self, function_name, arguments, result):
        """Track a function call"""
        if self.messages and self.messages[-1]['role'] == 'assistant':
            self.messages[-1]['function_calls'].append({
                'function': function_name,
                'arguments': arguments,
                'result': result,
                'timestamp': datetime.datetime.now().isoformat()
            })
    
    def get_history_for_prompt(self, max_messages=10):
        """Get conversation history in simple format for prompt"""
        if not self.messages:
            return "No previous conversation."
            
        # Take last N messages (excluding most recent if it's a user message)
        history_messages = self.messages[-max_messages:]
        
        lines = []
        for msg in history_messages:
            if msg['role'] == 'user':
                lines.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                lines.append(f"Assistant: {msg['content']}")
                # Add successful function calls
                for call in msg.get('function_calls', []):
                    if call.get('result'):
                        func = call['function']
                        if func == 'update_data':
                            lines.append(f"Actions: updated {call['arguments'].get('field')} = {call['arguments'].get('value')}")
                        elif func == 'ask_question':
                            lines.append(f"Actions: asked about {call['arguments'].get('field')}")
            lines.append("")  # Empty line between messages
            
        return "\n".join(lines).strip()
    
    def print_session_flow(self):
        """Print the conversation flow in a clean format"""
        print(f"\n🔄 CONVERSATION FLOW ({self.session_id})")
        print("=" * 50)
        
        for i, msg in enumerate(self.messages, 1):
            time = msg['timestamp'].split('T')[1][:8]
            
            if msg['role'] == 'assistant' and not any(m['role'] == 'user' for m in self.messages[:i-1]):
                # Assistant message without prior user message (greeting)
                print(f"\n📍 TURN {i}")
                print(f"   🤖 ASSISTANT:")
                print(f"      💬 [{time}] \"{msg['content']}\"")
            elif msg['role'] == 'user':
                print(f"\n📍 TURN {i}")
                print(f"   👤 [{time}] USER: {msg['content']}")
                
                # Find next assistant message
                for j in range(i, len(self.messages)):
                    if self.messages[j]['role'] == 'assistant':
                        assistant_msg = self.messages[j]
                        assist_time = assistant_msg['timestamp'].split('T')[1][:8]
                        print(f"   🤖 ASSISTANT:")
                        
                        # Print function calls first
                        for call in assistant_msg.get('function_calls', []):
                            call_time = call['timestamp'].split('T')[1][:8]
                            args = call['arguments']
                            args_str = ", ".join([f"{k}='{v}'" for k, v in args.items()])
                            print(f"      🔧 [{call_time}] {call['function']}({args_str})")
                            if call.get('result'):
                                print(f"         → {call['result']}")
                        
                        # Print response
                        if assistant_msg['content']:
                            print(f"      💬 [{assist_time}] \"{assistant_msg['content']}\"")
                        break
        
        print("=" * 50)