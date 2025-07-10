#!/usr/bin/env python3
"""
Simple logging wrapper for OpenAI chat service
"""
import sys
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

DEBUG_MODE = "--debug" in sys.argv

class LoggingService(OpenAIChatCompletion):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use __dict__ to bypass Pydantic validation
        self.__dict__['conversation_manager'] = None
    
    async def get_chat_message_contents(self, *args, **kwargs):
        print(f"\n🔄 API CALL")
        
        # Get available functions
        functions = []
        if 'kernel' in kwargs and hasattr(kwargs['kernel'], 'plugins'):
            for name, plugin in kwargs['kernel'].plugins.items():
                if name != 'chat_plugin':
                    functions.extend(plugin.functions.keys())
        
        print(f"📋 Functions available: {functions}")
        
        # Make the actual API call
        result = await super().get_chat_message_contents(*args, **kwargs)
        
        # Track function calls
        if self.__dict__.get('conversation_manager') and result:
            messages = result if isinstance(result, list) else []
            for msg in messages:
                if hasattr(msg, 'items'):
                    for item in msg.items:
                        if hasattr(item, 'function_call_result'):
                            r = item.function_call_result
                            print(f"   🔧 {r.function_name} → {r.result}")
                            
                            # Let conversation manager know about the function call
                            self.__dict__['conversation_manager'].add_function_call(
                                r.function_name,
                                {},  # We don't have args here
                                r.result
                            )
        
        print("✅ COMPLETE")
        return result