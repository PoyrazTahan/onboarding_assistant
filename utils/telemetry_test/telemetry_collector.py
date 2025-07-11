#!/usr/bin/env python3
"""
Simple Telemetry Collector for Semantic Kernel
Collects events as structured data instead of raw logs
"""

import json
import time
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional


class TelemetryCollector:
    """Simple telemetry collector that captures events as structured data"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.event_stack: List[str] = []  # For hierarchical tracking
        self._setup_traditional_logging()
    
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
            
            # Write event data
            for key, value in data.items():
                if key in ["prompt", "response", "assistant_response"] and len(str(value)) > 100:
                    # Truncate long text
                    truncated = str(value)[:100] + "..."
                    file.write(f"{prefix}  {key}: {truncated}\n")
                else:
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