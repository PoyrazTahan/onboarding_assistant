#!/usr/bin/env python3
"""
Simple agent for learning Semantic Kernel basics
Goal: Update data.json through conversation until all fields are filled
"""
#%%
import nest_asyncio
nest_asyncio.apply()

#%%
import os
import json
import asyncio
import sys
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Import our conversation manager
from conversation_manager import ConversationManager

# Check for debug flag
DEBUG_MODE = "--debug" in sys.argv

# Custom logging chat service
class LoggingChatService(OpenAIChatCompletion):
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
            print(f"\n=== DEBUG: DETAILED API CALL INFO ===")
            print(f"Args count: {len(args)}")
            print(f"Kwargs keys: {list(kwargs.keys())}")
            if settings:
                print(f"Settings: {settings}")
            if 'kernel' in kwargs:
                kernel = kwargs['kernel']
                if hasattr(kernel, 'plugins'):
                    print(f"Kernel plugins detailed:")
                    for plugin_name, plugin in kernel.plugins.items():
                        funcs = list(plugin.functions.keys())
                        print(f"  Plugin '{plugin_name}': {funcs}")
        
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

# Load environment
load_dotenv()

class DataManager:
    """Manages the simple data.json file"""
    
    def __init__(self, data_file="data/data.json", conversation_manager=None):
        self.data_file = data_file
        self.conversation_manager = conversation_manager
        
    def load_data(self):
        """Load data from JSON file"""
        with open(self.data_file, 'r') as f:
            return json.load(f)
    
    def save_data(self, data):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
    def get_data_status(self) -> str:
        """Get current data status with detailed human-readable format"""
        data = self.load_data()
        
        # Separate filled and missing data
        filled = {key: value for key, value in data.items() if value is not None}
        missing = [key for key, value in data.items() if value is None]
        
        status_report = []
        
        # === RECORDED DATA SECTION ===
        status_report.append("=== RECORDED USER DATA ===")
        if not filled:
            status_report.append("• No data recorded yet")
        else:
            for field, value in filled.items():
                if field == "age":
                    status_report.append(f"- Age: {value}")
                elif field == "weight":
                    status_report.append(f"- Weight: {value}")
                elif field == "height":
                    status_report.append(f"- Height: {value}")
        
        # === MISSING FIELDS SECTION ===
        status_report.append("\n=== MISSING FIELDS ===")
        if not missing:
            status_report.append("• All fields complete!")
        else:
            for field in missing:
                if field == "age":
                    status_report.append("• Age: null")
                elif field == "weight":
                    status_report.append("• Weight: null")
                elif field == "height":
                    status_report.append("• Height: null")
        
        # === NEXT ACTION GUIDANCE ===
        status_report.append("\n=== WORKFLOW GUIDANCE ===")
        if missing:
            next_field = missing[0]  # First missing field
            status_report.append(f"• NEXT ACTION: Ask question for '{next_field}' field")
        else:
            status_report.append("• NEXT ACTION: All data collected, end conversation")
        
        return "\n".join(status_report)
    
    @kernel_function(
        name="update_data",
        description="Update a specific field ONLY when you have actual user-provided information. Do NOT call with empty values or duplicate existing data."
    )
    def update_data(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to update (must be: age, weight, or height) field type is case insensetive",
            is_required=True
        ),
        value: str = InputVariable(
            name="value", 
            description="New value to set (numbers for age/height)",
            is_required=True
        )
    ) -> str:
        # DETAILED TRACKING: Add timestamp and call counter
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🚀 [{timestamp}] Function called: update_data(field='{field}', value='{value}')")
        
        data = self.load_data()
        print(f"   📊 Current data before update: {data}")
        
        if field not in data:
            error_msg = f"Error: Field '{field}' not found. Available fields: {list(data.keys())}"
            print(f"   ❌ {error_msg}")
            return error_msg
        
        print(f"   🔄 Attempting to update '{field}' from '{data[field]}' to '{value}'")
        
        # VALIDATION: Prevent empty/meaningless updates
        if not value or value.strip() == '':
            error_msg = f"Cannot update {field} with empty value. Only update when you have actual user-provided information."
            print(f"   ❌ {error_msg}")
            return error_msg
        
        # VALIDATION: Prevent unnecessary updates of existing data
        current_value = data[field]
        if current_value is not None and str(current_value) == str(value):
            error_msg = f"Field {field} already has value '{current_value}'. No update needed unless user provides new information."
            print(f"   ⚠️ {error_msg}")
            return error_msg
        
        # Convert to appropriate type
        if field in ["age", "height"]:
            try:
                data[field] = int(value)
            except ValueError:
                error_msg = f"Error: {field} must be a number, got '{value}'"
                print(f"   ❌ {error_msg}")
                return error_msg
        else:
            data[field] = value
        
        self.save_data(data)
        result = f"Updated {field} to {data[field]}"
        print(f"   ✅ {result}")
        print(f"   📊 Data after update: {data}")
        print()
        return result
    
    @kernel_function(
        name="ask_question",
        description="Ask user for specific missing information"
    )
    def ask_question(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to ask about (age, weight, or height), field type is case insensetive",
            is_required=True
        ),
        message: str = InputVariable(
            name="message",
            description="Custom message to display to user",
            is_required=True
        )
    ) -> str:
        # DETAILED TRACKING: Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"💬 [{timestamp}] Function called: ask_question(field='{field}', message='{message}')")
        
        data = self.load_data()
        print(f"   📊 Current data: {data}")
        print(f"   🤔 Asking about field '{field}' which currently has value: {data.get(field, 'NOT_FOUND')}")
        
        result = f"[ASKING] {field}: {message}"
        print(f"   📝 Result: {result}")
        print()
        return result

async def main():
    """Main function to test our simple agent"""
    
    print("🧪 Testing Simple Data Collection Agent...")
    
    # Initialize conversation manager
    conv_manager = ConversationManager()
    print(f"📝 Started conversation session: {conv_manager.session_id}")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add OpenAI service with logging
    chat_service = LoggingChatService(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Connect chat service to conversation manager
    chat_service.set_conversation_manager(conv_manager)
    
    # Add data manager plugin with conversation manager
    data_manager = DataManager(conversation_manager=conv_manager)
    data_plugin = kernel.add_plugin(
        plugin=data_manager,
        plugin_name="data_plugin"
    )
    
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    print(f"\n📋 SETTINGS: Function={settings.function_choice_behavior.type_.value.upper()}(max:{settings.function_choice_behavior.maximum_auto_invoke_attempts}) | Temp={settings.temperature or 'def'} | MaxTok={settings.max_tokens or '∞'} | Stream={settings.stream}")
    
    features = []
    if hasattr(settings, 'reasoning_effort'): features.append("reasoning")
    if hasattr(settings, 'structured_json_response'): features.append("json")
    if hasattr(settings, 'response_format'): features.append("format")
    if hasattr(settings, 'tool_choice'): features.append("tool_choice")
    if hasattr(settings, 'seed'): features.append("seed")
    print(f"🔍 FEATURES: {' | '.join(features) if features else 'basic'}")
    
    print(f"✅ Plugin added with functions: {[f.name for f in data_plugin.functions.values()]}")
    
    # Debug function registration details
    print(f"\n🔧 FUNCTION REGISTRATION:")
    for func_name, func in data_plugin.functions.items():
        print(f"   {func_name}: {func.description} | Params: {[p.name for p in func.parameters]}")
    
    if DEBUG_MODE:
        print("\n=== ENHANCED PARAMETER DEBUG ===")
        for func_name, func in data_plugin.functions.items():
            print(f"Function: {func_name}")
            print(f"  - Return type: {func.return_parameter}")
            for param in func.parameters:
                print(f"  Parameter: {param.name}")
                print(f"    - Direct description: {param.description}")
                if hasattr(param, 'default_value') and param.default_value:
                    if hasattr(param.default_value, 'description'):
                        print(f"    - InputVariable description: {param.default_value.description}")
    
    # Load prompt from file and add current data status
    with open("agents/prompts/prompt.txt", 'r') as f:
        base_prompt = f.read()
    
    # Get current data status and add to prompt
    current_status = data_manager.get_data_status()
    prompt = f"{base_prompt}\n\nCURRENT DATA STATUS:\n{current_status}\n\nUser: {{{{$user_input}}}}\nAssistant: "
    
    print(f"📝 PROMPT LENGTH: {len(prompt)} characters")
    print(f"📊 DATA STATUS: {len([k for k, v in data_manager.load_data().items() if v is not None])}/3 fields filled")
     
    # Create chat function
    chat_function = kernel.add_function(
        function_name="data_chat",
        plugin_name="chat_plugin",
        prompt=prompt
    )
    
    print("\n=== SK KERNEL INSPECTION ===")
    print(f"Kernel plugins: {list(kernel.plugins.keys())}")
    print(f"Kernel services: {list(kernel.services.keys())}")
    print("\n=== SK KERNEL INSPECTION ===")
    
    
    for user_input in ["I was born in 1996"]:
        print(f"\nUser: {user_input}")
        
        # Track user message
        conv_manager.add_user_message(user_input)

        print("Testing direct invoke...")
        # Try using KernelArguments to pass settings
        arguments = KernelArguments(
            user_input=user_input,
            settings=settings
        )
        try:
            response = await kernel.invoke(
                chat_function,
                arguments
            )   
        except Exception as e:
            print(f"❌ Invoke Error: {e}")
            import traceback
            traceback.print_exc()
            
        # Extract clean response and metrics
        print(f"\n=== API CALL SUMMARY ===")
        
        # Get the actual response content
        chat_message = response.value[0]  # First (and only) message
        clean_response = chat_message.content
        
        # Track assistant message with SK response for tool extraction
        conv_manager.add_assistant_message(
            content=clean_response,
            sk_response=response,
            metadata={
                'model': 'gpt-4o-mini',
                'function_choice_behavior': str(settings.function_choice_behavior.type_.value)
            }
        )
        
        # Extract token usage from metadata
        usage = chat_message.metadata.get('usage')
        if DEBUG_MODE and usage:
            print(f"📊 TOKEN USAGE:")
            print(f"   INPUT  - Prompt tokens: {usage.prompt_tokens}")
            print(f"   OUTPUT - Completion tokens: {usage.completion_tokens}")
            print(f"          - Reasoning tokens: {usage.completion_tokens_details.reasoning_tokens}")
            print(f"          - Accepted prediction tokens: {usage.completion_tokens_details.accepted_prediction_tokens}")
            # print(f"   TOTAL: {usage.total_tokens}")
        
        print(f"\n💬 ASSISTANT RESPONSE:")
        print(clean_response)
        print("=" * 50)

        # Check if functions were called
        print(f"Data after invoke: {data_manager.load_data()}")
        
        # Print conversation summary
        print(f"\n=== CONVERSATION TRACKING ===")
        summary = conv_manager.get_conversation_summary()
        print(f"Messages: {summary['user_messages']} user, {summary['assistant_messages']} assistant")
        print(f"Tool calls: {summary['tool_calls']}")
        print(f"Functions used: {summary['functions_used']}")
        
        # Print detailed conversation
        conv_manager.print_conversation()

    
#%%
if __name__ == "__main__":
    asyncio.run(main())

# %%
