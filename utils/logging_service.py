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
        self.__dict__['session'] = None
        self.__dict__['current_block_id'] = None
    
    async def get_chat_message_contents(self, *args, **kwargs):
        # Simple API call indicator without detailed debug info
        if not DEBUG_MODE:
            print(f"\n🔄 API CALL")
        
        # Make the actual API call
        result = await super().get_chat_message_contents(*args, **kwargs)
        
        # Track function calls in session
        if self.__dict__.get('session') and self.__dict__.get('current_block_id') and result:
            messages = result if isinstance(result, list) else []
            for msg in messages:
                if hasattr(msg, 'items'):
                    for item in msg.items:
                        if hasattr(item, 'function_call_result'):
                            r = item.function_call_result
                            
                            # Only print function calls if not in debug mode
                            if not DEBUG_MODE:
                                print(f"   🔧 {r.function_name} → {r.result}")
                            
                            # Try to extract arguments from the function call
                            args = {}
                            if hasattr(item, 'function_call') and hasattr(item.function_call, 'arguments'):
                                try:
                                    import json
                                    args = json.loads(item.function_call.arguments)
                                except:
                                    pass
                            
                            # Add action to current block
                            self.__dict__['session'].add_action_to_block(
                                self.__dict__['current_block_id'],
                                r.function_name,
                                args,
                                r.result
                            )
        
        # Simple completion indicator
        if not DEBUG_MODE:
            print("✅ COMPLETE")
        return result