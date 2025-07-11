#!/usr/bin/env python3
"""
Simple Telemetry Collector for Semantic Kernel
Collects events as structured data instead of raw logs
"""

import json
import time
import logging
import sys
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional


class PromptEvolutionHandler(logging.Handler):
    """Custom logging handler to capture OpenAI request evolution"""
    
    def __init__(self, telemetry_collector):
        super().__init__()
        self.telemetry = telemetry_collector
        self.conversation_prompts = {}  # Track prompts per conversation
        
    def emit(self, record):
        try:
            message = record.getMessage()
            
            # Look for OpenAI request options
            if "Request options:" in message and "json_data" in message:
                self._extract_prompt_from_request(message)
                
        except Exception:
            # Don't let telemetry errors break the application
            pass
    
    def _extract_prompt_from_request(self, message):
        """Extract and track prompt evolution from OpenAI request"""
        try:
            # Extract the json_data part
            json_start = message.find("'json_data': {")
            if json_start == -1:
                return
                
            # Find the matching closing brace for json_data
            json_part = message[json_start + len("'json_data': "):]
            
            # Parse the request data (this is tricky with the log format)
            # Let's try to extract just the messages array
            messages_start = json_part.find("'messages': [")
            if messages_start == -1:
                return
                
            # Extract messages array (simplified parsing)
            messages_part = json_part[messages_start + len("'messages': "):]
            
            # Find the end of messages array by counting brackets
            bracket_count = 0
            end_pos = 0
            for i, char in enumerate(messages_part):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos > 0:
                messages_str = messages_part[:end_pos]
                self._process_messages_evolution(messages_str)
                
        except Exception:
            # Robust parsing - if it fails, just skip
            pass
    
    def _process_messages_evolution(self, messages_str):
        """Process the evolution of messages in the conversation"""
        try:
            # Create a simple hash of the messages for comparison
            prompt_hash = hashlib.md5(messages_str.encode()).hexdigest()[:8]
            
            # Count messages to determine evolution stage
            message_count = messages_str.count("'role':")
            
            if message_count == 1:
                # Initial prompt - just user message
                self.telemetry.prompt_initial(messages_str, prompt_hash)
                self.conversation_prompts['original'] = messages_str
                self.conversation_prompts['hash'] = prompt_hash
                
            elif message_count > 1:
                # Evolved prompt - has function calls/results
                if 'original' in self.conversation_prompts:
                    # Extract what was added
                    additions = self._extract_additions(messages_str)
                    self.telemetry.prompt_evolved(
                        original_hash=self.conversation_prompts['hash'],
                        evolved_messages=messages_str,
                        additions=additions,
                        message_count=message_count
                    )
                else:
                    # Fallback if we missed the original
                    self.telemetry.prompt_initial(messages_str, prompt_hash)
                    
        except Exception:
            pass
    
    def _extract_additions(self, evolved_messages):
        """Extract what was added to the original prompt"""
        try:
            # Count tool calls and tool responses
            tool_calls = evolved_messages.count("'tool_calls':")
            tool_responses = evolved_messages.count("'role': 'tool'")
            
            additions = []
            if tool_calls > 0:
                additions.append(f"function_calls: {tool_calls}")
            if tool_responses > 0:
                additions.append(f"function_results: {tool_responses}")
                
            return " + ".join(additions) if additions else "unknown_additions"
            
        except Exception:
            return "parsing_failed"


class TelemetryCollector:
    """Simple telemetry collector that captures events as structured data"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.event_stack: List[str] = []  # For hierarchical tracking
        self._setup_traditional_logging()
        self._setup_prompt_tracking()
    
    def _setup_prompt_tracking(self):
        """Setup prompt evolution tracking"""
        # Hook into OpenAI client logger
        openai_logger = logging.getLogger("openai._base_client")
        prompt_handler = PromptEvolutionHandler(self)
        openai_logger.addHandler(prompt_handler)
        openai_logger.setLevel(logging.DEBUG)
    
    def _setup_traditional_logging(self):
        """Setup traditional Python logging to capture SK internal logs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.traditional_log_file = f"telemetry_{timestamp}.log"
        
        # Configure comprehensive logging for maximum debugging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.traditional_log_file)
            ],
            force=True  # Override any existing configuration
        )
        
        # Configure all SK loggers for maximum verbosity
        sk_loggers = [
            "semantic_kernel",
            "semantic_kernel.kernel", 
            "semantic_kernel.functions",
            "semantic_kernel.connectors",
            "semantic_kernel.connectors.ai.open_ai",
            "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion",
            "semantic_kernel.functions.kernel_function"
        ]
        
        for logger_name in sk_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
        
    def _create_event(self, event_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a base event structure"""
        event = {
            "id": f"{event_type}_{int(time.time() * 1000)}",
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
            "children": []
        }
        
        # Add to parent if we're in a hierarchical context
        if self.event_stack and self.events:
            parent_id = self.event_stack[-1]
            for event_item in self.events:
                if event_item["id"] == parent_id:
                    event_item["children"].append(event)
                    return event
        
        # Top-level event
        self.events.append(event)
        return event
    
    def conversation_start(self, conversation_id: str, user_input: str):
        """Track conversation start"""
        event = self._create_event("CONVERSATION_START", {
            "conversation_id": conversation_id,
            "user_input": user_input
        })
        self.event_stack.append(event["id"])
        return event["id"]
    
    def conversation_end(self, conversation_id: str, assistant_response: str):
        """Track conversation end"""
        event = self._create_event("CONVERSATION_END", {
            "conversation_id": conversation_id,
            "assistant_response": assistant_response
        })
        if self.event_stack:
            self.event_stack.pop()
        return event["id"]
    
    def function_call_start(self, function_name: str, parameters: Dict[str, Any]):
        """Track function call start"""
        event = self._create_event("FUNCTION_CALL_START", {
            "function_name": function_name,
            "parameters": parameters
        })
        self.event_stack.append(event["id"])
        return event["id"]
    
    def function_call_end(self, function_name: str, result: str):
        """Track function call end"""
        event = self._create_event("FUNCTION_CALL_END", {
            "function_name": function_name,
            "result": result
        })
        if self.event_stack:
            self.event_stack.pop()
        return event["id"]
    
    def function_response(self, function_name: str, response: str):
        """Track function response (child of function call)"""
        return self._create_event("FUNCTION_RESPONSE", {
            "function_name": function_name,
            "response": response
        })["id"]
    
    def ai_request(self, prompt: str, model: str):
        """Track AI model request"""
        event = self._create_event("AI_REQUEST", {
            "prompt": prompt,
            "model": model,
            "prompt_length": len(prompt)
        })
        self.event_stack.append(event["id"])
        return event["id"]
    
    def ai_response(self, response: str, model: str):
        """Track AI model response"""
        event = self._create_event("AI_RESPONSE", {
            "response": response,
            "model": model,
            "response_length": len(response)
        })
        if self.event_stack:
            self.event_stack.pop()
        return event["id"]
    
    def token_usage(self, input_tokens: int, output_tokens: int, total_tokens: int):
        """Track token usage"""
        return self._create_event("TOKEN_USAGE", {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        })["id"]
    
    def prompt_initial(self, messages_str: str, prompt_hash: str):
        """Track initial prompt (first request to LLM)"""
        # Extract user content for display
        user_content = self._extract_user_content(messages_str)
        
        return self._create_event("PROMPT_INITIAL", {
            "prompt_hash": prompt_hash,
            "user_content": user_content,
            "full_messages": messages_str,
            "message_count": 1
        })["id"]
    
    def prompt_evolved(self, original_hash: str, evolved_messages: str, additions: str, message_count: int):
        """Track evolved prompt (subsequent requests with function results)"""
        evolved_hash = hashlib.md5(evolved_messages.encode()).hexdigest()[:8]
        
        return self._create_event("PROMPT_EVOLVED", {
            "original_hash": original_hash,
            "evolved_hash": evolved_hash,
            "additions": additions,
            "message_count": message_count,
            "evolution": f"[[ORIGINAL_PROMPT_{original_hash}]] + {additions}"
        })["id"]
    
    def prompt_reread(self, prompt_hash: str):
        """Track when same prompt is read again"""
        return self._create_event("PROMPT_REREAD", {
            "prompt_hash": prompt_hash,
            "note": "Same prompt re-read, no changes"
        })["id"]
    
    def error(self, error_type: str, message: str, details: Dict[str, Any] = None):
        """Track errors"""
        return self._create_event("ERROR", {
            "error_type": error_type,
            "message": message,
            "details": details or {}
        })["id"]
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all collected events"""
        return self.events
    
    def clear_events(self):
        """Clear all events"""
        self.events = []
        self.event_stack = []
    
    def to_log_file(self, filename: str):
        """Convert structured events to readable log file"""
        with open(filename, 'w') as f:
            f.write(f"TELEMETRY LOG - Generated at {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            
            self._write_events_to_file(f, self.events, indent=0)
    
    def to_timestamped_log(self, base_filename: str = "telemetry"):
        """Create timestamped log file with all events dumped as raw data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}.log"
        
        with open(filename, 'w') as f:
            f.write(f"COMPLETE TELEMETRY DUMP - {datetime.now().isoformat()}\n")
            f.write("=" * 100 + "\n")
            f.write(f"Total Events: {len(self.events)}\n")
            f.write("=" * 100 + "\n\n")
            
            # Dump everything as JSON for complete data preservation
            f.write("RAW EVENT DATA:\n")
            f.write("-" * 50 + "\n")
            json.dump(self.events, f, indent=2, default=str)
            f.write("\n\n")
            
            # Also include human readable version
            f.write("HUMAN READABLE FORMAT:\n")
            f.write("-" * 50 + "\n")
            self._write_events_to_file(f, self.events, indent=0)
    
    def _extract_user_content(self, messages_str: str):
        """Extract user content from messages for display"""
        try:
            # Simple extraction of user content
            user_start = messages_str.find("'content': '")
            if user_start != -1:
                content_start = user_start + len("'content': '")
                content_end = messages_str.find("'", content_start)
                if content_end != -1:
                    content = messages_str[content_start:content_end]
                    return content
            return "Could not extract user content"
        except Exception:
            return "Extraction failed"
        
        return filename
    
    def get_traditional_log_filename(self) -> str:
        """Get the filename of the traditional logging output"""
        return self.traditional_log_file
    
    def _write_events_to_file(self, file, events: List[Dict[str, Any]], indent: int):
        """Write events hierarchically to file"""
        for event in events:
            timestamp = event["timestamp"]
            event_type = event["type"]
            data = event["data"]
            
            # Write main event
            prefix = "  " * indent
            file.write(f"{prefix}[{timestamp}] {event_type}\n")
            
            # Write event data without truncation
            for key, value in data.items():
                file.write(f"{prefix}  {key}: {value}\n")
            
            # Write children with increased indent
            if event["children"]:
                file.write(f"{prefix}  └─ Children:\n")
                self._write_events_to_file(file, event["children"], indent + 2)
            
            file.write("\n")
    
    def to_json_file(self, filename: str):
        """Save events as JSON for programmatic access"""
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=2, default=str)


# Global instance for easy access
telemetry = TelemetryCollector()