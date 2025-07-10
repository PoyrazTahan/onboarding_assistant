#!/usr/bin/env python3
"""
Simple agent for learning Semantic Kernel basics
Goal: Update data.json through conversation until all fields are filled
"""
#%%
import nest_asyncio
import asyncio
import aiohttp
nest_asyncio.apply()

#%%
import os
import json
import asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Custom logging chat service
class LoggingChatService(OpenAIChatCompletion):
    async def get_chat_message_contents(self, *args, **kwargs):
        print(f"\n=== CHAT SERVICE CALL ===")
        print(f"Args count: {len(args)}")
        print(f"Kwargs keys: {list(kwargs.keys())}")
        
        # Look for chat_history or messages in args
        for i, arg in enumerate(args):
            print(f"Arg {i} type: {type(arg)}")
            if hasattr(arg, 'messages'):
                print(f"  Messages: {arg.messages}")
            elif hasattr(arg, 'role'):
                print(f"  Role: {arg.role}")
                print(f"  Content: {arg.content}")
            elif isinstance(arg, (list, tuple)):
                print(f"  List/Tuple length: {len(arg)}")
                for j, item in enumerate(arg):
                    print(f"    Item {j}: {type(item)} - {item}")
        
        # Look for messages in kwargs
        if 'messages' in kwargs:
            print(f"Kwargs messages: {kwargs['messages']}")
        if 'chat_history' in kwargs:
            print(f"Kwargs chat_history: {kwargs['chat_history']}")
        
        # Check for settings/execution_settings
        if 'settings' in kwargs:
            print(f"Kwargs settings: {kwargs['settings']}")
            if hasattr(kwargs['settings'], 'function_choice_behavior'):
                print(f"  Function choice behavior: {kwargs['settings'].function_choice_behavior}")
        
        print("=" * 50)
        
        result = await super().get_chat_message_contents(*args, **kwargs)
        
        print(f"\n=== CHAT SERVICE RESPONSE ===")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'content'):
            print(f"Result content: {result.content}")
        print("=" * 50)
        
        return result

# Load environment
load_dotenv()

class DataManager:
    """Manages the simple data.json file"""
    
    def __init__(self, data_file="data/data.json"):
        self.data_file = data_file
        
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
        
        # === EXISTING DATA SECTION ===
        status_report.append("=== EXISTING DATA ===")
        if not filled:
            status_report.append("• No information available yet - this could be a new user")
            status_report.append("• Start with a friendly greeting and ask for basic information")
        else:
            for field, value in filled.items():
                if field == "age":
                    status_report.append(f"- Age: {value}")
                elif field == "weight":
                    status_report.append(f"- Weight: {value}")
                elif field == "height":
                    status_report.append(f"- Height: {value}")
        
        # === MISSING DATA SECTION ===
        status_report.append("\n=== MISSING DATA ===")
        if not missing:
            status_report.append("• All data collected! No further information needed.")
            status_report.append("• You can summarize what you've learned and end the conversation.")
        else:
            for field in missing:
                if field == "age":
                    status_report.append("• Age: Ask how old they are (needed for health recommendations)")
                elif field == "weight":
                    status_report.append("• Weight: Ask their current weight in kg (for BMI calculation)")
                elif field == "height":
                    status_report.append("• Height: Ask their height in cm (for BMI calculation)")
        
        return "\n".join(status_report)
    
    @kernel_function(
        name="update_data",
        description="Update a specific field in data.json"
    )
    def update_data(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to update (must be: age, weight, or height)",
            is_required=True
        ),
        value: str = InputVariable(
            name="value", 
            description="New value to set (numbers for age/height)",
            is_required=True
        )
    ) -> str:
        print(f"🚀 Function called: update_data(field='{field}', value='{value}')")
        
        data = self.load_data()
        
        if field not in data:
            return f"Error: Field '{field}' not found. Available fields: {list(data.keys())}"
        
        # Convert to appropriate type
        if field in ["age", "height"]:
            try:
                data[field] = int(value)
            except ValueError:
                return f"Error: {field} must be a number, got '{value}'"
        else:
            data[field] = value
        
        self.save_data(data)
        return f"Updated {field} to {data[field]}"
    
    @kernel_function(
        name="ask_question",
        description="Ask user for specific missing information"
    )
    def ask_question(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to ask about (age, weight, or height)",
            is_required=True
        ),
        message: str = InputVariable(
            name="message",
            description="Custom message to display to user",
            is_required=True
        )
    ) -> str:
        print(f"🚀 Function called: ask_question(field='{field}', message='{message}')")
        return f"[ASKING] {field}: {message}"

async def main():
    """Main function to test our simple agent"""
    
    print("🧪 Testing Simple Data Collection Agent...")
    
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
    
    # Add data manager plugin
    data_manager = DataManager()
    data_plugin = kernel.add_plugin(
        plugin=data_manager,
        plugin_name="data_plugin"
    )
    
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    print(f"\n=== EXECUTION SETTINGS DEBUG ===")
    print(f"Settings function_choice_behavior: {settings.function_choice_behavior}")
    print(f"Settings dict: {settings}")
    print("=" * 50)
    
    print(f"✅ Plugin added with functions: {[f.name for f in data_plugin.functions.values()]}")
    
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
    
    chat_service = kernel.get_service("openai")
    print(f"Chat service type: {type(chat_service)}")
    
    for user_input in ["I was born in 1996"]:
        print(f"\nUser: {user_input}")

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
        
        # Extract token usage from metadata
        usage = chat_message.metadata.get('usage')
        if usage:
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

    
#%%
# if __name__ == "__main__":
#     asyncio.run(main())

# %%
