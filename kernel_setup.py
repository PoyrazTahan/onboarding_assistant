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
from utils.data_manager import DataManager
from utils.telemetry_collector import telemetry

# Load environment
load_dotenv()

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
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Add data plugin
    if debug_mode:
        print("📋 Adding data plugin - decorator parsing will be captured in telemetry")
    
    data_plugin = kernel.add_plugin(
        plugin=data_manager,
        plugin_name="data_plugin"
    )
    
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
            available_functions.extend(list(plugin.functions.keys()))
    return available_functions