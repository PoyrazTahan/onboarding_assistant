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
from utils.dict_utils import dict_diff


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
        # Set session start state
        self.session.session_start_state = self.data_manager.load_data().copy()
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
        
        # Get updated conversation history
        conversation_history = self.session.get_conversation_history()
        
        # Check for hidden widget completion context
        widget_completion = self.session.stage_manager.get_and_clear_widget_completion()
        hidden_context = ""
        if widget_completion:
            hidden_context = f"\n\nCRITICAL: DO NOT call update_data for {widget_completion['field']} - it was already updated via widget to {widget_completion['selected_value']}. Result: {widget_completion['update_result']}. Just acknowledge the selection and continue to the next missing field."
        
        # Build prompt with current state using Prompt Manager
        prompt = self.prompt_manager.build_conversation_prompt(
            conversation_history=conversation_history,
            current_status=current_status,
            user_input_placeholder="{{$user_input}}"
        )
        
        # Inject hidden widget context if available
        if hidden_context:
            prompt = prompt + hidden_context
        
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
        
        # Track what changed during this block and add to last block
        final_data = self.data_manager.load_data()
        block_start_state = self.session.blocks[-1]['context']['data_state_snapshot']
        changes = dict_diff(block_start_state, final_data)
        self.session.blocks[-1]['response']['data_changes'] = changes
        
        # STAGE 1: Track LLM requests (vs Stage 2 actual execution in kernel_functions)
        # Purpose: Debug LLM behavior, routing issues, compare request vs execution
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
                            
                            # Add to session block (STAGE 1: LLM request tracking)
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