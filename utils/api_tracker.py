"""
API Tracker for monitoring LLM API usage, costs, and performance.
Supports multiple providers (OpenAI, Gemini) with unified tracking.
"""

import time
from typing import Dict, Optional, Union
import semantic_kernel as sk

# Pricing per 1M tokens for different models
PRICING_CONFIG = {
    # OpenAI Models
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    
    # Gemini Models
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash-lite-preview-06-17": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
    "gemma-3n-e2b-it": {"input": 0.00, "output": 0.00},
    "gemma-3n-e4b-it": {"input": 0.00, "output": 0.00},
}

class APITracker:
    """
    Unified API tracker for monitoring LLM usage across different providers.
    Tracks tokens, costs, response times, and call counts.
    """
    
    def __init__(self, provider: str = "unknown"):
        self.provider = provider
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.call_history = []
        
    def track_call(self, 
                   input_tokens: int, 
                   output_tokens: int, 
                   response_time: float, 
                   model_id: str,
                   call_description: str = "API Call") -> float:
        """
        Track a single API call with tokens, timing, and cost calculation.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            response_time: Response time in seconds
            model_id: Model identifier (e.g., "gpt-4o-mini", "gemini-1.5-flash")
            call_description: Description of the call for tracking
            
        Returns:
            float: Cost of this specific call
        """
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_time += response_time
        
        # Calculate cost
        call_cost = 0.0
        if model_id in PRICING_CONFIG:
            pricing = PRICING_CONFIG[model_id]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            call_cost = input_cost + output_cost
            self.total_cost += call_cost
        
        # Store call history
        call_record = {
            "call_number": self.total_calls,
            "description": call_description,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time": response_time,
            "cost": call_cost,
            "timestamp": time.time()
        }
        self.call_history.append(call_record)
        
        return call_cost
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters).
        For more accurate tracking, integrate with tiktoken or similar.
        """
        return len(text) // 4
    
    def get_pricing_info(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get pricing information for a specific model."""
        return PRICING_CONFIG.get(model_id)
    
    def print_call_details(self, input_tokens: int, output_tokens: int, 
                          response_time: float, call_cost: float):
        """Print detailed information about the current call."""
        print(f"⏱️  Response Time: {response_time:.2f}s")
        print(f"🔢 Input Tokens: ~{input_tokens:,}")
        print(f"🔢 Output Tokens: ~{output_tokens:,}")
        print(f"💰 Call Cost: ~${call_cost:.6f}")
    
    def print_summary(self):
        """Print comprehensive API usage summary."""
        print("=" * 60)
        print(f"📊 API USAGE SUMMARY ({self.provider.upper()})")
        print("=" * 60)
        print(f"Total API Calls: {self.total_calls}")
        print(f"Total Input Tokens: {self.total_input_tokens:,}")
        print(f"Total Output Tokens: {self.total_output_tokens:,}")
        print(f"Total Tokens: {(self.total_input_tokens + self.total_output_tokens):,}")
        print(f"Total Response Time: {self.total_time:.2f}s")
        print(f"Average Response Time: {self.total_time/self.total_calls if self.total_calls > 0 else 0:.2f}s")
        print(f"Total Cost: ${self.total_cost:.6f}")
        print(f"Average Cost per Call: ${self.total_cost/self.total_calls if self.total_calls > 0 else 0:.6f}")
        print("=" * 60)
    
    def get_stats(self) -> Dict:
        """Get usage statistics as a dictionary."""
        return {
            "provider": self.provider,
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_time": self.total_time,
            "total_cost": self.total_cost,
            "avg_response_time": self.total_time/self.total_calls if self.total_calls > 0 else 0,
            "avg_cost_per_call": self.total_cost/self.total_calls if self.total_calls > 0 else 0,
            "call_history": self.call_history
        }
    
    def reset(self):
        """Reset all tracking statistics."""
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.call_history = []


async def tracked_invoke(kernel: sk.Kernel, 
                        function, 
                        input_text: str, 
                        model_id: str,
                        tracker: APITracker,
                        call_description: str = "API Call") -> str:
    """
    Wrapper function to track API calls with timing and token usage.
    
    Args:
        kernel: Semantic Kernel instance
        function: The kernel function to invoke
        input_text: Input text for the function
        model_id: Model identifier for pricing
        tracker: APITracker instance
        call_description: Description of the call
        
    Returns:
        str: The response from the API call
    """
    start_time = time.time()
    
    # Make the API call
    result = await kernel.invoke(function, input=input_text)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # Estimate tokens (rough approximation)
    input_tokens = tracker.estimate_tokens(input_text)
    output_tokens = tracker.estimate_tokens(str(result))
    
    # Track the call
    call_cost = tracker.track_call(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        response_time=response_time,
        model_id=model_id,
        call_description=call_description
    )
    
    return result


def print_model_pricing(model_id: str):
    """Print pricing information for a specific model."""
    if model_id in PRICING_CONFIG:
        pricing = PRICING_CONFIG[model_id]
        print(f"💰 Pricing: ${pricing['input']}/1M input tokens, ${pricing['output']}/1M output tokens")
    else:
        print(f"⚠️  Pricing not available for model: {model_id}")


def get_available_models() -> Dict[str, Dict]:
    """Get all available models and their pricing."""
    return PRICING_CONFIG.copy()