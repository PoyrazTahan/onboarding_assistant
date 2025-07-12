#!/usr/bin/env python3
"""
Turkish Persona Agent - Context-aware empathetic Turkish communication
Processes conversation context and provides natural, multi-message responses
"""

import sys
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

# Check for debug mode
DEBUG_MODE = "--debug" in sys.argv

# Setup telemetry integration
TELEMETRY_AVAILABLE = False
if DEBUG_MODE:
    try:
        from monitoring.telemetry import telemetry
        TELEMETRY_AVAILABLE = True
    except ImportError:
        pass

class TurkishPersonaAgent:
    """Context-aware Turkish persona with empathy and natural conversation flow"""
    
    def __init__(self):
        self.kernel = None
        self.chat_service = None
        self.prompt_template = None
        
    async def initialize(self):
        """Initialize Turkish persona agent with template loading"""
        # Simple kernel setup
        self.kernel = Kernel()
        
        # Add chat completion service
        self.chat_service = OpenAIChatCompletion(
            service_id="turkish_persona",
            api_key=None,  # Uses OPENAI_API_KEY env var
            ai_model_id="gpt-4o-mini"
        )
        self.kernel.add_service(self.chat_service)
        
        # Load prompt template
        self._load_prompt_template()
        
        if DEBUG_MODE:
            print("🇹🇷 Turkish Persona Agent initialized with context awareness")
    
    def _load_prompt_template(self):
        """Load Turkish persona prompt template"""
        try:
            with open("prompts/templates/turkish_persona_prompt.txt", 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            raise RuntimeError("Turkish persona prompt template not found")
    
    def _extract_conversation_context(self, session):
        """Extract clean conversation flow without backend noise"""
        if not session or not session.blocks:
            return "Yeni konuşma başlıyor."
        
        conversation_lines = []
        
        for block in session.blocks:
            if block['type'] == 'programmatic' and block['subtype'] == 'greeting':
                # Skip greeting - it will be generated fresh by Turkish agent
                continue
                
            elif block['type'] == 'ai_interaction':
                # User input
                user_input = block['user_input']
                conversation_lines.append(f"Kullanıcı: {user_input}")
                
                # Check for successful data updates
                successful_updates = []
                for action in block['response']['actions']:
                    if action['function'] == 'update_data' and 'Updated' in action['result']:
                        field = action['arguments'].get('field')
                        value = action['arguments'].get('value')
                        successful_updates.append(f"{field}={value}")
                
                # AI response (will be replaced by Turkish version)
                if block['response']['final_message']:
                    english_response = block['response']['final_message']
                    
                    # Add update context if any
                    if successful_updates:
                        conversation_lines.append(f"[VERİ GÜNCELLENDİ: {', '.join(successful_updates)}]")
                    
                    conversation_lines.append(f"Asistan (EN): {english_response}")
        
        return "\n".join(conversation_lines)
    
    def _determine_last_action_result(self, session):
        """Determine the result of the last action with precise status"""
        if not session or not session.blocks:
            return "CONVERSATION_START - No previous actions"
        
        # Get the latest AI interaction block
        for block in reversed(session.blocks):
            if block['type'] == 'ai_interaction':
                actions = block['response']['actions']
                if actions:
                    last_action = actions[-1]
                    if last_action['function'] == 'update_data':
                        if 'Updated' in last_action['result']:
                            field = last_action['arguments'].get('field')
                            value = last_action['arguments'].get('value')
                            return f"DATA_UPDATED_SUCCESS - {field} successfully updated to: {value}"
                        else:
                            return f"DATA_UPDATE_FAILED - {last_action['result']}"
                    elif last_action['function'] == 'ask_question':
                        field = last_action['arguments'].get('field')
                        return f"QUESTION_ASKED - Asked for {field} field"
                else:
                    # No actions in this block - just conversation
                    return "CONVERSATION_ONLY - No data operations"
                break
        
        return "FIRST_MESSAGE - Initial interaction"
    
    def _extract_next_question(self, english_response):
        """Extract the next question from English response if any"""
        # Look for question patterns
        if '?' in english_response:
            # Find sentences with question marks
            sentences = english_response.split('.')
            for sentence in sentences:
                if '?' in sentence:
                    return sentence.strip()
        
        # Look for common question starters
        question_starters = ['What', 'How', 'Could you', 'Can you', 'Tell me']
        for starter in question_starters:
            if starter in english_response:
                # Extract from starter to end or next period
                start_idx = english_response.find(starter)
                end_idx = english_response.find('.', start_idx)
                if end_idx == -1:
                    end_idx = len(english_response)
                return english_response[start_idx:end_idx].strip()
        
        return "Soru bulunamadı"
    
    def _determine_instruction_type(self, english_response):
        """Determine if this is a greeting or question instruction"""
        if "INSTRUCTION TO NORA" in english_response:
            return "GREETING"
        elif "?" in english_response or any(starter in english_response for starter in ['What', 'Could you', 'Tell me']):
            return "QUESTION"
        else:
            return "UNKNOWN"
    
    def _parse_xml_response(self, turkish_response):
        """Parse XML ChatBox responses into list of messages"""
        try:
            from utils.xml_parser import extract_xml_tags, CHATBOX_PATTERNS
            return extract_xml_tags(turkish_response, CHATBOX_PATTERNS)
        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ XML parsing failed: {e}")
            return [turkish_response.strip()]
    
    async def process_with_context(self, english_response, session):
        """Process English response with full conversation context"""
        
        # Validation
        if not english_response or not english_response.strip():
            raise ValueError("Turkish agent requires non-empty English response")
        
        # Log telemetry
        if TELEMETRY_AVAILABLE:
            telemetry.conversation_start("turkish_persona", english_response[:100])
        
        try:
            # Build context
            conversation_context = self._extract_conversation_context(session)
            last_action_result = self._determine_last_action_result(session)
            next_question = self._extract_next_question(english_response)
            instruction_type = self._determine_instruction_type(english_response)
            
            # Get current data status using same format as core agent
            from tools.data_manager import DataManager
            data_manager = DataManager()
            current_data_status = data_manager.get_data_status()
            
            # Build prompt with all context
            full_prompt = self.prompt_template.replace("{{CONVERSATION_CONTEXT}}", conversation_context)
            full_prompt = full_prompt.replace("{{LAST_ACTION_RESULT}}", last_action_result)
            full_prompt = full_prompt.replace("{{NEXT_QUESTION}}", next_question)
            full_prompt = full_prompt.replace("{{INSTRUCTION_TYPE}}", instruction_type)
            full_prompt = full_prompt.replace("{{CURRENT_DATA_STATUS}}", current_data_status)
            
            # Invoke Turkish persona
            result = await self.kernel.invoke_prompt(
                function_name="turkish_persona_context",
                plugin_name="turkish_persona", 
                prompt=full_prompt
            )
            
            turkish_response = str(result).strip()
            
            if not turkish_response:
                raise ValueError(f"Turkish agent returned empty response")
            
            # Parse XML response into multiple messages
            messages = self._parse_xml_response(turkish_response)
            
            if DEBUG_MODE:
                print(f"🇹🇷 Generated {len(messages)} messages: {[msg[:20]+'...' for msg in messages]}")
            
            # Log success
            if TELEMETRY_AVAILABLE:
                telemetry.conversation_end("turkish_persona", f"{len(messages)} messages generated")
            
            return messages
            
        except Exception as e:
            # Log error
            if TELEMETRY_AVAILABLE:
                telemetry.error("turkish_persona", str(e))
            
            error_msg = f"Turkish persona processing failed: {e}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    async def translate_to_persona(self, english_response, session):
        """Main interface - process with full conversation context"""
        if not session:
            raise ValueError("Turkish agent requires session context for proper operation")
        
        return await self.process_with_context(english_response, session)