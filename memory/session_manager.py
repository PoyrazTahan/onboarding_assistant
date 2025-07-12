#!/usr/bin/env python3
"""
Session/Block architecture for proper conversation management
Simple, functional approach - no dataclasses, minimal typing
"""
import datetime
import json
import uuid

class Session:
    """Manages the entire conversation lifecycle with block-based structure"""
    
    def __init__(self, session_id=None):
        self.id = session_id or f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.blocks = []
        self.session_start_state = {}
        self.session_end_state = {}
        self.created_at = datetime.datetime.now().isoformat()
        self.stage_manager = ConversationStageManager()
        
    def add_programmatic_block(self, content, block_type="greeting"):
        """Add a programmatic entry (greeting, system message, etc)"""
        block = {
            'id': str(uuid.uuid4())[:8],
            'type': 'programmatic',
            'subtype': block_type,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.blocks.append(block)
        return block
        
    def start_ai_block(self, user_input, full_prompt, functions_available, data_snapshot):
        """Start a new AI interaction block"""
        block = {
            'id': str(uuid.uuid4())[:8],
            'type': 'ai_interaction',
            'user_input': user_input,
            'context': {
                'full_prompt': full_prompt,
                'functions_available': functions_available,
                'data_state_snapshot': data_snapshot,
                'timestamp_start': datetime.datetime.now().isoformat()
            },
            'response': {
                'raw_response': None,
                'actions': [],
                'final_message': None,
                'timestamp_end': None
            }
        }
        self.blocks.append(block)
        return block['id']
        
    def complete_ai_block(self, block_id, raw_response, final_message):
        """Complete an AI block with response data"""
        for block in self.blocks:
            if block.get('id') == block_id and block['type'] == 'ai_interaction':
                block['response']['raw_response'] = raw_response
                block['response']['final_message'] = final_message
                block['response']['timestamp_end'] = datetime.datetime.now().isoformat()
                return True
        return False
        
    def add_action_to_block(self, block_id, function_name, arguments, result):
        """Add a function call to the current AI block"""
        for block in self.blocks:
            if block.get('id') == block_id and block['type'] == 'ai_interaction':
                action = {
                    'function': function_name,
                    'arguments': arguments,
                    'result': result,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                block['response']['actions'].append(action)
                return True
        return False
    
    def add_token_usage(self, block_id, input_tokens, output_tokens):
        """Add token usage information to an AI block"""
        for block in self.blocks:
            if block.get('id') == block_id and block['type'] == 'ai_interaction':
                block['response']['token_usage'] = {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens
                }
                return True
        return False
    
    def update_session_end_state(self, final_data_state):
        """Update session end state with final data"""
        self.session_end_state = final_data_state.copy()
        
    def get_conversation_history(self, max_blocks=10):
        """Get conversation history for prompt inclusion"""
        if not self.blocks:
            return "No previous conversation."
            
        # Get recent blocks
        recent_blocks = self.blocks[-max_blocks:]
        lines = []
        
        for block in recent_blocks:
            if block['type'] == 'programmatic':
                # Include programmatic messages as Assistant messages
                lines.append(f"Assistant: {block['content']}")
            elif block['type'] == 'ai_interaction':
                # User input
                lines.append(f"User: {block['user_input']}")
                
                # Include actions taken inline with response
                if block['response']['actions']:
                    lines.append("Actions taken:")
                    for action in block['response']['actions']:
                        if action['function'] == 'update_data':
                            field = action['arguments'].get('field')
                            value = action['arguments'].get('value')
                            lines.append(f"  - Called update_data(field='{field}', value='{value}') → {action['result']}")
                        elif action['function'] == 'ask_question':
                            field = action['arguments'].get('field')
                            message = action['arguments'].get('message')
                            lines.append(f"  - Called ask_question(field='{field}', message='{message}') → Success")
                
                # Assistant response after actions
                if block['response']['final_message']:
                    lines.append(f"Assistant: {block['response']['final_message']}")
            
        return "\n".join(lines).strip()
        
    def get_current_block_id(self):
        """Get the ID of the most recent AI block that's not completed"""
        for block in reversed(self.blocks):
            if (block['type'] == 'ai_interaction' and 
                block['response']['timestamp_end'] is None):
                return block['id']
        return None
        
    def debug_block(self, block_id=None, show_full_prompt=False):
        """Get detailed debug info for a specific block or the latest"""
        if block_id is None:
            # Get latest AI block
            for block in reversed(self.blocks):
                if block['type'] == 'ai_interaction':
                    block_id = block['id']
                    break
                    
        for block in self.blocks:
            if block.get('id') == block_id:
                debug_info = {
                    'block_id': block['id'],
                    'type': block['type'],
                    'user_input': block.get('user_input', 'N/A'),
                    'prompt_length': len(block['context']['full_prompt']) if block['type'] == 'ai_interaction' else 0,
                    'functions_available': block['context']['functions_available'] if block['type'] == 'ai_interaction' else [],
                    'actions_taken': [a['function'] for a in block['response']['actions']] if block['type'] == 'ai_interaction' else [],
                    'data_snapshot': block['context']['data_state_snapshot'] if block['type'] == 'ai_interaction' else {}
                }
                
                if show_full_prompt and block['type'] == 'ai_interaction':
                    debug_info['full_prompt'] = block['context']['full_prompt']
                    
                return debug_info
        return None
        
    def print_session_flow(self):
        """Print the session flow in a clean, debuggable format"""
        print(f"\n🔄 SESSION FLOW ({self.id})")
        print(f"📅 Started: {self.created_at}")
        print("=" * 60)
        
        for i, block in enumerate(self.blocks, 1):
            if block['type'] == 'programmatic':
                print(f"\n📍 BLOCK {i} - PROGRAMMATIC ({block['subtype']})")
                print(f"   🤖 [{block['timestamp'].split('T')[1][:8]}] \"{block['content']}\"")
                
            elif block['type'] == 'ai_interaction':
                print(f"\n📍 BLOCK {i} - AI INTERACTION")
                print(f"   👤 USER: {block['user_input']}")
                
                # Context info
                ctx = block['context']
                print(f"   📋 CONTEXT:")
                print(f"      - Prompt size: {len(ctx['full_prompt'])} chars")
                print(f"      - Functions: {ctx['functions_available']}")
                print(f"      - Data state: {list(ctx['data_state_snapshot'].keys())}")
                
                # Response info
                resp = block['response']
                if resp['timestamp_end']:
                    print(f"   🤖 RESPONSE:")
                    
                    # Actions
                    for action in resp['actions']:
                        args_str = ", ".join([f"{k}='{v}'" for k, v in action['arguments'].items()])
                        print(f"      🔧 {action['function']}({args_str}) → {action['result']}")
                    
                    # Final message
                    if resp['final_message']:
                        print(f"      💬 \"{resp['final_message']}\"")
                else:
                    print(f"   ⏳ IN PROGRESS...")
                    
        print("=" * 60)
        
    def save_to_file(self, filepath=None):
        """Save session to JSON file"""
        if filepath is None:
            filepath = f"data/sessions/{self.id}.json"
            
        session_data = {
            'id': self.id,
            'created_at': self.created_at,
            'blocks': self.blocks,
            'session_start_state': self.session_start_state,
            'session_end_state': self.session_end_state
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath):
        """Load session from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        session = cls(session_id=data['id'])
        session.created_at = data['created_at']
        session.blocks = data['blocks']
        session.session_start_state = data.get('session_start_state', {})
        session.session_end_state = data.get('session_end_state', {})
        
        return session


class ConversationStageManager:
    """Manages conversation stages with real-time function call tracking"""
    
    def __init__(self):
        # Core stage tracking (always active)
        self.current_stage = "initial"
        self.last_question_field = None
        self.question_history = []
        self.function_call_log = []
        
        # Test automation (only active in test mode)
        self.test_mode = False
        self.test_data = {}
        self.pending_test_response = None
        
    def enable_test_mode(self, test_data_file="data/test.json"):
        """Enable test mode and load test responses"""
        self.test_mode = True
        try:
            with open(test_data_file, 'r') as f:
                self.test_data = json.load(f)
                print(f"    📋 Stage Manager: Loaded test data from {test_data_file}")
        except Exception as e:
            print(f"    ⚠️ Stage Manager: Error loading test data: {e}")
            self.test_mode = False
    
    def on_function_call(self, function_name, arguments, result):
        """Hook called when any kernel function is executed (like telemetry)"""
        # print(f"🔧 STAGE MANAGER HOOK: {function_name} called with {arguments}")
        # Always track function calls for stage management
        call_info = {
            'function': function_name,
            'arguments': arguments,
            'result': result,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.function_call_log.append(call_info)
        
        # Handle ask_question specifically
        if function_name == 'ask_question':
            field = arguments.get('field', '').lower()
            message = arguments.get('message', '')
            
            # Always track the question
            self.last_question_field = field
            self.question_history.append({
                'field': field,
                'message': message,
                'timestamp': call_info['timestamp']
            })
            
            # print(f"    📍 Stage Manager: Question detected for field '{field}'")
            
            # If in test mode, prepare automated response
            if self.test_mode and field in self.test_data:
                test_response = self.test_data[field]
                self.pending_test_response = test_response
                # print(f"    🎯 Stage Manager: Prepared test response: '{test_response}'")
        
        # Handle update_data to track completion
        elif function_name == 'update_data':
            field = arguments.get('field', '').lower()
            value = arguments.get('value', '')
            final_value = arguments.get('final_value', value)  # In case of type conversion
            print(f"    ✅ Stage Manager: Data updated - {field}: {final_value}")
            
            # Track update completion for stage management
            if self.last_question_field == field:
                print(f"    🎯 Stage Manager: Question '{field}' completed with update")
                self.current_stage = "data_updated"
    
    def get_pending_test_response(self):
        """Get and clear pending test response"""
        if self.pending_test_response:
            response = self.pending_test_response
            self.pending_test_response = None
            return response
        return None
    
    def get_stage_summary(self):
        """Get current stage information for debugging"""
        return {
            'current_stage': self.current_stage,
            'last_question_field': self.last_question_field,
            'questions_asked': len(self.question_history),
            'function_calls': len(self.function_call_log),
            'test_mode': self.test_mode
        }