#!/usr/bin/env python3
"""
Agent - Core agent logic for conversation management
Handles conversation flow, initial greetings, and agent reasoning
"""

import hashlib
import json
from semantic_kernel.functions.kernel_arguments import KernelArguments
from memory.session_manager import Session
from core.tool_registry import setup_kernel, get_available_functions
from monitoring.telemetry import telemetry
from prompts.prompt_manager import PromptManager


class Agent:
    """Core agent that handles conversation flow and reasoning"""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.kernel = None
        self.data_manager = None
        self.settings = None
        self.prompt_manager = PromptManager()
        self.session = None
        
    async def initialize(self):
        """Initialize the agent with kernel and components"""
        # Setup kernel and components
        self.kernel, self.data_manager, self.settings = setup_kernel(debug_mode=self.debug_mode)
        
        # Prompt manager is already initialized in constructor
        if self.debug_mode:
            debug_info = self.prompt_manager.get_debug_info()
            print(f"📋 Prompt Manager initialized with {len(debug_info['loaded_templates'])} templates")
    
    def start_session(self):
        """Start a new conversation session"""
        self.session = Session()
        if self.debug_mode:
            print(f"📝 Started session: {self.session.id}")
        return self.session
    
    def handle_initial_greeting(self):
        """Handle initial greeting based on current data state"""
        # Check if greeting is needed
        if self.session.blocks:
            return None  # Already has blocks, no greeting needed
            
        # Get current data state and generate appropriate greeting
        data = self.data_manager.load_data()
        greeting = self.prompt_manager.get_greeting(data)
        
        # Add programmatic greeting block
        self.session.add_programmatic_block(greeting, block_type="greeting")
        
        return greeting
    
    async def process_user_input(self, user_input, turn_number=0):
        """Process a single user input and return agent response"""
        
        # Start conversation tracking in telemetry
        if self.debug_mode:
            telemetry.conversation_start(f"turn_{turn_number+1}", user_input)
        
        # Reload data to get latest state
        data = self.data_manager.load_data()
        current_status = self.data_manager.get_data_status()
        
        # Update session's data state
        self.session.data_state = data.copy()
        
        # Get updated conversation history
        conversation_history = self.session.get_conversation_history()
        
        # Build prompt with current state using Prompt Manager
        prompt = self.prompt_manager.build_conversation_prompt(
            conversation_history=conversation_history,
            current_status=current_status,
            user_input_placeholder="{{$user_input}}"
        )
        
        if self.debug_mode:
            # Track prompt in telemetry (initial or evolved)
            system_prompt = self.prompt_manager.get_system_prompt()
            if turn_number == 0:
                telemetry.prompt_initial(prompt, hashlib.md5(prompt.encode()).hexdigest()[:8])
            else:
                telemetry.prompt_evolved(
                    original_hash=hashlib.md5(system_prompt.encode()).hexdigest()[:8],
                    evolved_messages=prompt,
                    additions=f"conversation_turn_{turn_number+1}",
                    message_count=turn_number+1
                )
        
        # Create chat function with updated prompt
        chat_function = self.kernel.add_function(
            function_name=f"data_chat_{turn_number}",  # Make function name unique for each iteration
            plugin_name="chat_plugin",
            prompt=prompt
        )
        
        # Get available functions for context
        available_functions = get_available_functions(self.kernel)
        
        # Start AI block with full context
        block_id = self.session.start_ai_block(
            user_input=user_input,
            full_prompt=prompt.replace("{{$user_input}}", user_input),
            functions_available=available_functions,
            data_snapshot=data.copy()
        )
        
        # Update data manager with current block
        self.data_manager.session = self.session
        self.data_manager.current_block_id = block_id
        
        # Try using KernelArguments to pass settings
        arguments = KernelArguments(
            user_input=user_input,
            settings=self.settings
        )
        
        try:
            response = await self.kernel.invoke(chat_function, arguments)
        except Exception as e:
            error_msg = f"❌ Invoke Error: {e}"
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return error_msg
        
        # Get the actual response content
        chat_message = response.value[0]  # First (and only) message
        clean_response = chat_message.content
        
        # Complete the AI block
        self.session.complete_ai_block(block_id, str(response.value), clean_response)
        
        # Extract function calls from response and add to session
        if hasattr(response, 'value'):
            messages = response.value if isinstance(response.value, list) else [response.value]
            for message in messages:
                if hasattr(message, 'items'):
                    for item in message.items:
                        if hasattr(item, 'function_call_result'):
                            result = item.function_call_result
                            
                            # Extract arguments if available
                            args = {}
                            if hasattr(item, 'function_call') and hasattr(item.function_call, 'arguments'):
                                try:
                                    args = json.loads(item.function_call.arguments)
                                except:
                                    pass
                            
                            # Add to session block
                            self.session.add_action_to_block(
                                block_id,
                                result.function_name,
                                args,
                                result.result
                            )
        
        # Process response in telemetry if debug mode
        if self.debug_mode:
            telemetry.process_kernel_response(response, user_input, {
                "model": "gpt-4o-mini",
                "conversation_turn": turn_number + 1,
                "data_state": data.copy(),
                "prompt_length": len(prompt)
            })
            
            # Extract token usage from metadata and add to session
            usage = chat_message.metadata.get('usage')
            if usage:
                self.session.add_token_usage(block_id, usage.prompt_tokens, usage.completion_tokens)
            
            # End conversation in telemetry
            telemetry.conversation_end(f"turn_{turn_number+1}", clean_response)
        
        return clean_response
    
    def is_conversation_complete(self):
        """Check if conversation is complete (all data collected)"""
        data = self.data_manager.load_data()
        return all(value is not None for value in data.values())
    
    def get_session(self):
        """Get current session"""
        return self.session