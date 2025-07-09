import os
import asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion
from utils.api_tracker import APITracker, tracked_invoke, print_model_pricing

# Load environment variables from .env file
load_dotenv()

# Gemini Model Parameters - easily adjustable
GEMINI_CONFIG = {
    # Options: gemini-1.5-flash, gemini-1.5-pro, gemini-1.0-pro, gemini-2.0-flash-lite
    "ai_model_id": "gemini-2.0-flash-lite",
    "temperature": 0.7,                   # 0.0 = deterministic, 1.0 = creative
    "max_tokens": 1000,                   # Maximum response length
    "top_p": 0.9,                         # Nucleus sampling (0.1-1.0)
    "top_k": 40,                          # Top-k sampling (1-100)
}

# Global tracker instance
api_tracker = APITracker(provider="gemini")

async def main_google():
    # Get API key from .env file
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GEMINI_API_KEY in your .env file")
        return
    
    model_id = GEMINI_CONFIG['ai_model_id']
    print(f"🔧 Using Gemini model: {model_id}")
    print(f"🔧 Temperature: {GEMINI_CONFIG['temperature']}")
    print(f"🔧 Max tokens: {GEMINI_CONFIG['max_tokens']}")
    
    # Show pricing info
    print_model_pricing(model_id)
    print("=" * 50)
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add Gemini chat completion service
    chat_service = GoogleAIChatCompletion(
        gemini_model_id   = model_id,
        api_key           = api_key,
        service_id        = "gemini",
    )
    kernel.add_service(chat_service)
    
    # Create a simple health assistant function using the new API
    health_assistant_prompt = """
    You are a friendly health assistant helping users with their wellness journey. Be short in your answers
    
    User: {{$input}}
    Assistant: 
    """
    
    # Create function using the new API
    health_function = kernel.add_function(
        function_name="health_assistant",
        plugin_name="health_plugin",
        prompt=health_assistant_prompt
    )
    
    # Test basic functionality with tracking
    print("🧪 Testing basic health assistant...")
    test_input = "Hello, I'm ready to start tracking my health!"
    result = await tracked_invoke(kernel, health_function, test_input, model_id, api_tracker, "Health Assistant Test")
    print(f"   User    : \n\t\t{test_input}")
    print(f"✅ Response: \n\t\t{result}")
    print("=" * 50)
    
    # Test with a health-related question
    print("🧪 Testing health question...")
    health_question = "What should I know about tracking my daily water intake?"
    result = await tracked_invoke(kernel, health_function, health_question, model_id, api_tracker, "Health Question Test")
    print(f"   User    : \n\t\t{health_question}")
    print(f"✅ Response: \n\t\t{result}")
    print("=" * 50)
    
    # Test prompt for data extraction (future use)
    extraction_prompt = """
    Extract the numeric value from this user input about their age.
    
    Examples:
    - "twenty" -> 20
    - "I am about to be twenty one" -> 21
    - "around 30" -> 30
    - "I'm 25" -> 25
    
    User input: {{$input}}
    Extracted number: """
    
    extraction_function = kernel.add_function(
        function_name="extract_number",
        plugin_name="extraction_plugin",
        prompt=extraction_prompt
    )
    
    print("🧪 Testing number extraction...")
    test_age_input = "I am thirhty years old"
    result = await tracked_invoke(kernel, extraction_function, test_age_input, model_id, api_tracker, "Number Extraction Test")
    print(f"   User          : \n\t\t{test_age_input}")
    print(f"✅ Age extraction: \n\t\t{result}")
    
    print("=" * 50)
    print("🎉 Phase 1B: API Integration - SUCCESS!")
    print("✅ GEMINI connection working")
    print("✅ Basic health assistant responses working")
    print("✅ Number extraction capability working")
    print("✅ Ready for Phase 2: Agent Structure")
    
    # Print API usage summary
    api_tracker.print_summary() 
    


if __name__ == "__main__":
    asyncio.run(main_google())