#!/usr/bin/env python3
"""
LoggingChatService - Enhanced OpenAI chat service with detailed logging
Provides clean output in normal mode, detailed debugging with --debug flag
"""

import sys
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

# Check for debug flag
DEBUG_MODE = "--debug" in sys.argv

class LoggingChatService(OpenAIChatCompletion):
    """Enhanced OpenAI chat service with function call tracking and clean logging"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use __dict__ to bypass Pydantic validation
        self.__dict__['conversation_manager'] = None
    
    def set_conversation_manager(self, conv_manager):
        self.__dict__['conversation_manager'] = conv_manager
    
    async def get_chat_message_contents(self, *args, **kwargs):
        print(f"\n🔄 API CALL INITIATED")
        
        # Extract essential request info
        settings = kwargs.get('settings', {})
        function_behavior = getattr(settings, 'function_choice_behavior', None)
        
        # Check available functions
        available_functions = []
        if 'kernel' in kwargs:
            kernel = kwargs['kernel']
            if hasattr(kernel, 'plugins'):
                for plugin_name, plugin in kernel.plugins.items():
                    if plugin_name != 'chat_plugin':  # Skip chat function
                        available_functions.extend(plugin.functions.keys())
        
        print(f"📋 SETUP: Functions={len(available_functions)} | Behavior={function_behavior.type_.value if function_behavior else 'none'}")
        print(f"🔧 AVAILABLE: {available_functions}")
        
        if DEBUG_MODE:
            print(f"\n=== DEBUG: API CALL HIGHLIGHTS ===")
            if settings and hasattr(settings, 'function_choice_behavior'):
                behavior = settings.function_choice_behavior
                print(f"Function Choice: {behavior.type_.value} (max attempts: {behavior.maximum_auto_invoke_attempts})")
            
            if 'kernel' in kwargs:
                kernel = kwargs['kernel']
                if hasattr(kernel, 'plugins'):
                    data_funcs = []
                    for plugin_name, plugin in kernel.plugins.items():
                        if plugin_name == 'data_plugin':
                            data_funcs = list(plugin.functions.keys())
                    print(f"Available Functions: {data_funcs}")
            
            print(f"Request Type: {list(kwargs.keys())}")
        
        print("=" * 50)
        
        result = await super().get_chat_message_contents(*args, **kwargs)
        
        # Extract essential response info  
        chat_messages = result if isinstance(result, list) else (result.value if hasattr(result, 'value') else [])
        
        functions_executed = []
        response_content = ""
        
        for chat_msg in chat_messages:
            if hasattr(chat_msg, 'content'):
                response_content = chat_msg.content
            
            # Check for function executions in items
            if hasattr(chat_msg, 'items') and chat_msg.items:
                for item in chat_msg.items:
                    if hasattr(item, 'function_call_result'):
                        func_result = item.function_call_result
                        functions_executed.append({
                            'name': func_result.function_name,
                            'result': func_result.result
                        })
                        
                        if self.__dict__.get('conversation_manager'):
                            self.__dict__['conversation_manager'].add_tool_call_manually(
                                function_name=func_result.function_name,
                                arguments={},
                                result=func_result.result,
                                success=True
                            )
        
        print(f"✅ API RESPONSE: {len(functions_executed)} functions executed")
        for func in functions_executed:
            print(f"   🔧 {func['name']} → {func['result']}")
        print(f"💬 CONTENT: {response_content}")
        print("=" * 50)
        
        return result