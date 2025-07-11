#!/usr/bin/env python3
"""
Semantic Kernel Setup Module
Simple, clean setup for kernel initialization
"""

import os
import sys
import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv

# Import utilities
from tools.data_manager import DataManager
from monitoring.telemetry import telemetry

# Load environment
load_dotenv()

def get_all_kernel_functions():
    """Get all kernel functions from all tools for registration"""
    return {
        'data_operations': DataManager(),
        # future tools can be added here:
        # 'api_operations': APIManager(),
        # 'email_operations': EmailManager(),
    }

def setup_kernel(debug_mode=False):
    """
    Setup and configure Semantic Kernel with all necessary components
    
    Args:
        debug_mode (bool): Whether to enable debug logging (should already be enabled if needed)
        
    Returns:
        tuple: (kernel, data_manager, settings)
    """
    # Clear telemetry events if debug mode (telemetry already enabled in main)
    if debug_mode:
        telemetry.clear_events()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Create kernel
    kernel = sk.Kernel()
    
    # Add OpenAI service
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-4o-mini",
        api_key=api_key,
        service_id="openai"
    )
    kernel.add_service(chat_service)
    
    # Register all tools
    all_tools = get_all_kernel_functions()
    data_manager = None
    
    for tool_name, tool_instance in all_tools.items():
        if debug_mode:
            print(f"📋 Adding {tool_name} plugin - decorator parsing captured")
        
        kernel.add_plugin(tool_instance, plugin_name=tool_name)
        
        # Keep reference to data_manager for backward compatibility
        if tool_name == 'data_operations':
            data_manager = tool_instance
    
    # Create execution settings
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    
    return kernel, data_manager, settings

def get_available_functions(kernel):
    """
    Get list of available function names from kernel plugins
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        list: List of available function names
    """
    available_functions = []
    for plugin_name, plugin in kernel.plugins.items():
        if plugin_name != 'chat_plugin':  # Skip chat plugin
            available_functions.extend([f"{plugin_name}.{func}" for func in plugin.functions.keys()])
    return available_functions