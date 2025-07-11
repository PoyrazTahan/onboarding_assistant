#!/usr/bin/env python3
"""
Prompt Manager - Dynamic prompt construction and template management
Handles all prompt-related logic and template loading
"""

import os
from typing import Dict, Any, Optional


class PromptManager:
    """Manages prompt templates and dynamic prompt construction"""
    
    def __init__(self, templates_dir="prompts/templates"):
        self.templates_dir = templates_dir
        self._templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from templates directory"""
        template_files = {
            'system_prompt': 'system_prompt.txt',
            'fallback_prompt': 'fallback_prompt.txt',
            'greeting_new': 'greeting_new.txt',
            'greeting_return': 'greeting_return.txt'
        }
        
        for template_name, filename in template_files.items():
            filepath = os.path.join(self.templates_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._templates[template_name] = f.read().strip()
            except FileNotFoundError:
                print(f"⚠️  Template {filename} not found, using fallback")
                self._templates[template_name] = f"[Missing template: {template_name}]"
    
    def get_system_prompt(self) -> str:
        """Get the main system prompt for agent reasoning"""
        # Try to load the main system prompt, fallback to simpler version
        if 'system_prompt' in self._templates and not self._templates['system_prompt'].startswith('[Missing'):
            return self._templates['system_prompt']
        else:
            return self._templates.get('fallback_prompt', 'You are a helpful assistant.')
    
    def get_greeting(self, data_state: Dict[str, Any]) -> str:
        """Get appropriate greeting based on current data state"""
        # Check if user has any existing data
        has_data = any(value is not None for value in data_state.values())
        
        if has_data:
            # User has some data, use return greeting
            return self._templates.get('greeting_return', 'Can I ask you a few more questions?')
        else:
            # New user, use new greeting
            return self._templates.get('greeting_new', 'Hello! Let me help you with your information.')
    
    def build_conversation_prompt(
        self, 
        conversation_history: str,
        current_status: str,
        user_input_placeholder: str = "{{$user_input}}"
    ) -> str:
        """Build the full conversation prompt with all context"""
        system_prompt = self.get_system_prompt()
        
        # Build the full prompt with context
        full_prompt = f"""{system_prompt}

CONVERSATION HISTORY:
{conversation_history}

CURRENT DATA STATUS:
{current_status}

User: {user_input_placeholder}
Assistant: """
        
        return full_prompt
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Get a specific template by name"""
        return self._templates.get(template_name)
    
    def list_templates(self) -> Dict[str, str]:
        """List all available templates"""
        return self._templates.copy()
    
    def reload_templates(self):
        """Reload all templates from disk"""
        self._templates.clear()
        self._load_templates()
        print("🔄 Prompt templates reloaded")
    
    def add_custom_template(self, name: str, content: str):
        """Add a custom template programmatically"""
        self._templates[name] = content
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about loaded templates"""
        return {
            'templates_dir': self.templates_dir,
            'loaded_templates': list(self._templates.keys()),
            'template_sizes': {name: len(content) for name, content in self._templates.items()},
            'system_prompt_preview': self._templates.get('system_prompt', '')[:200] + "..."
        }