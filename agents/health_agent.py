import os
import json
import asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion
from semantic_kernel.functions import KernelArguments

from utils.api_tracker import APITracker, tracked_invoke
from utils.conversation_manager import ConversationManager
from agents.data_handler import DataHandler
from ui.widgets.widget_handler import WidgetHandler

class HealthAgent:
    """Main health assistant agent for onboarding"""
    
    def __init__(self, user_id: str = "user", session_based: bool = True):
        self.user_id = user_id
        self.data_handler = DataHandler(user_id)
        self.widget_handler = WidgetHandler(user_id)
        self.conversation_manager = ConversationManager(user_id, session_based=session_based, conversations_path="/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/conversations")
        # REMOVED: function_parser - using only Semantic Kernel
        self.api_tracker = APITracker(provider="gemini")
        self.kernel = None
        self.chat_function = None
        
        # Load environment variables
        load_dotenv()
        
        # Load config
        self.config = self._load_config()
        
    def _load_config(self):
        """Load Gemini configuration"""
        config_path = os.path.join(os.path.dirname(__file__), "../config/gemini.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _load_prompt(self):
        """Load comprehensive monolith agent prompt"""
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/main_prompt.txt")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def initialize(self):
        """Initialize the agent"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Please set GEMINI_API_KEY in your .env file")
        
        print(f"🔧 Initializing Health Agent with {self.config['ai_model_id']}")
        
        # Create kernel
        self.kernel = sk.Kernel()
        
        # Add Gemini service
        chat_service = GoogleAIChatCompletion(
            gemini_model_id=self.config['ai_model_id'],
            api_key=api_key,
            service_id="gemini",
        )
        self.kernel.add_service(chat_service)
        
        # Add all required functions to kernel for function calling
        # REMOVED: trigger_widget - LLM only uses ask_question() which handles widgets automatically
        
        self.kernel.add_function(
            function_name="get_user_status",
            plugin_name="data_plugin",
            function=self.data_handler.get_user_status_and_questions
        )
        
        self.kernel.add_function(
            function_name="get_questions",
            plugin_name="data_plugin",
            function=self.data_handler.get_questions
        )
        
        self.kernel.add_function(
            function_name="get_question_details",
            plugin_name="data_plugin",
            function=self.data_handler.get_question_details
        )
        
        self.kernel.add_function(
            function_name="update_user_data",
            plugin_name="data_plugin",
            function=self.data_handler.update_user_data
        )
        
        self.kernel.add_function(
            function_name="ask_question",
            plugin_name="data_plugin",
            function=self.data_handler.ask_question
        )
        
        # REMOVED: Duplicate trigger_widget registration
        
        print("✅ All required functions added to kernel for function calling")
        
        # Create chat function
        prompt = self._load_prompt()
        self.chat_function = self.kernel.add_function(
            function_name="health_chat",
            plugin_name="chat_plugin",
            prompt=prompt
        )
        
        print("✅ Agent initialized successfully!")
    
    def _get_next_question(self):
        """Get the next unanswered question (legacy method - delegates to new systematic approach)"""
        return self._get_next_missing_question()
    
    async def chat(self, user_input: str, legacy_conversation_history: str = ""):
        """Chat with the user using clean conversation management"""
        
        # Store user input in clean conversation history
        if user_input.strip():
            self.conversation_manager.add_user_message(user_input)
        
        # Handle data updates for mutable fields
        conversation_for_context = self.conversation_manager.get_conversation_for_llm()
        # REMOVED: Manual data updates - LLM handles via Semantic Kernel functions
        
        # Get comprehensive user status and questions context  
        user_status = self.data_handler.get_user_status_and_questions()
        
        # Manual string replacement for prompt including all context
        prompt = self._load_prompt()
        filled_prompt = prompt.replace("{user_input}", user_input)
        
        # Add comprehensive user status to prompt
        filled_prompt += f"\n\n## KULLANICI DURUMU VE SORULAR:\n{user_status}\n"
        
        # Add clean conversation history to context
        clean_conversation_history = self.conversation_manager.get_conversation_for_llm()
        if clean_conversation_history:
            filled_prompt += f"\n\n## TEMİZ KONUŞMA GEÇMİŞİ:\n{clean_conversation_history}\n"
        
        # Create a simple function with the filled prompt
        simple_function = self.kernel.add_function(
            function_name="widget_chat",
            plugin_name="widget_chat_plugin",
            prompt=filled_prompt + "\n\nAsistan:"
        )
        
        # Get response with empty context
        import time
        start_time = time.time()
        response = await tracked_invoke(
            self.kernel,
            simple_function,
            "",
            self.config['ai_model_id'],
            self.api_tracker,
            "Widget Chat"
        )
        elapsed_time = time.time() - start_time
        
        # Convert response to string if it's a FunctionResult
        response_str = str(response)
        
        # Print compact API info
        cost = self.api_tracker.call_history[-1]['cost'] if self.api_tracker.call_history else 0.0
        print(f"🔄 API: ${cost:.2f} • {elapsed_time:.1f}s")
        
        # Clean response and store in conversation history
        # Semantic Kernel handles function calls automatically
        cleaned_response = self.conversation_manager._clean_assistant_message(response_str)
        if cleaned_response:
            self.conversation_manager.add_assistant_message(cleaned_response)
        
        return cleaned_response or response_str
    
    # REMOVED: Hardcoded question sequence logic - LLM will decide what to ask next
    # REMOVED: Complex regex extraction methods - LLM will handle via Semantic Kernel functions
    
    def print_summary(self):
        """Print API usage summary"""
        self.api_tracker.print_summary()