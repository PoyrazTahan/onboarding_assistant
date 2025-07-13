#!/usr/bin/env python3
"""
DataManager - Handles data.json operations with case-insensitive field names
Provides kernel functions for updating and querying user data
"""

import json
import sys
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable

# Check for debug mode
DEBUG_MODE = "--debug" in sys.argv

# Setup telemetry once at module level
TELEMETRY_AVAILABLE = False
if DEBUG_MODE:
    try:
        from monitoring.telemetry import telemetry
        TELEMETRY_AVAILABLE = True
    except ImportError:
        pass

class DataManager:
    """Manages the simple data.json file
    
    DUAL TRACKING: Stage 1 (Agent) tracks LLM requests, Stage 2 (here) tracks actual execution.
    Both needed for debugging: LLM behavior vs function execution vs routing issues.
    """
    
    def __init__(self, data_file="data/data.json", session=None, current_block_id=None):
        self.data_file = data_file
        self.widget_config_file = "data/widget_config.json"
        self.session = session
        self.current_block_id = current_block_id
        self.widget_config = self._load_widget_config()
        self.widget_handler = None  # Lazy load when needed
        
    def _log_function_call(self, function_name, inputs, outputs, metadata=None):
        """Unified telemetry logging for function calls"""
        if TELEMETRY_AVAILABLE:
            telemetry.local_function_log(
                source=f"DataManager.{function_name}",
                message=f"Function executed: {function_name}",
                data={
                    "inputs": inputs,
                    "outputs": outputs,
                    "metadata": metadata or {}
                }
            )
    
    def _handle_error(self, error_type, field, value, message):
        """Unified error handling with logging"""
        print(f"   ❌ {message}")
        self._log_function_call("update_data", 
                               {"field": field, "value": value}, 
                               {"result": message}, 
                               {"success": False, "error_type": error_type})
        return message
    
    def _add_to_session(self, function_name, args, result):
        """STAGE 2: Track actual execution (vs Stage 1 LLM requests in Agent)"""
        if self.session and self.current_block_id:
            self.session.add_action_to_block(self.current_block_id, function_name, args, result)
            # Also notify stage manager for real-time tracking
            self.session.stage_manager.on_function_call(function_name, args, result)
    
    def _load_widget_config(self):
        """Load widget configuration (hidden from LLM)"""
        try:
            with open(self.widget_config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"widget_fields": {}}
        except Exception as e:
            print(f"   ⚠️ Warning: Could not load widget config: {e}")
            return {"widget_fields": {}}
    
    def _is_widget_field(self, field):
        """Check if field has widget UI enabled"""
        field_lower = field.lower()
        widget_fields = self.widget_config.get("widget_fields", {})
        return field_lower in widget_fields and widget_fields[field_lower].get("enabled", False)
    
    def _handle_widget_question(self, field, message):
        """Flag widget for post-response execution to maintain proper block separation"""
        
        # Log widget detection for telemetry
        self._log_function_call("ask_question", 
                               {"field": field, "message": message}, 
                               {"widget_detected": True, "flagged_for_execution": True}, 
                               {"success": True, "widget": True})
        
        # Get widget configuration for this field
        widget_config = self.widget_config["widget_fields"][field]
        
        # Create widget information for later execution
        widget_info = {
            "field": field,
            "message": message,
            "widget_config": widget_config,
            "question_structure": {
                "question_text": message,
                "field": field,
                "options": widget_config.get("options", []),
                "type": widget_config.get("type", "select")
            }
        }
        
        # Flag widget for execution after LLM response
        if self.session and self.session.stage_manager:
            self.session.stage_manager.flag_widget_needed(widget_info)
        
        # Return simple [ASKING] response - widget will execute after LLM responds
        result = f"[ASKING] {field}: {message}"
        
        # STAGE 2 TRACKING: Record the ask (widget execution will be tracked separately)
        self._add_to_session("ask_question", {"field": field, "message": message}, result)
        
        return result
        
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
        
        # Build status sections
        recorded_section = [
            "=== RECORDED USER DATA ===",
            "• No data recorded yet" if not filled else 
            "\n".join([f"- {field.capitalize()}: {value}" for field, value in filled.items()])
        ]
        
        missing_section = [
            "\n=== MISSING FIELDS ===",
            "• All fields complete!" if not missing else 
            "\n".join([f"• {field.capitalize()}: null" for field in missing])
        ]
        
        next_action = [
            "\n=== WORKFLOW GUIDANCE ===",
            f"• NEXT ACTION: Ask question for '{missing[0]}' field" if missing else 
            "• NEXT ACTION: All data collected, end conversation"
        ]
        
        return "\n".join(recorded_section + missing_section + next_action)
    
    @kernel_function(
        name="update_data",
        description="Saves the user's answer to a specific field. After saving, this function's return message will EXPLICITLY tell you what to do next: either call ask_question for the next empty field or confirm that the process is complete. You must follow this instruction."
    )
    def update_data(
        self,
        field: str,
        value: str
    ) -> str:
        data = self.load_data()
        
        # Find actual field name (case-insensitive)
        actual_field = None
        for key in data.keys():
            if key.lower() == field.lower():
                actual_field = key
                break
        
        # Validation with unified error handling
        if actual_field is None:
            return self._handle_error("field_not_found", field, value,
                                    f"Error: Field '{field}' not found. Available fields: {list(data.keys())}")
        
        if not value or not value.strip():
            return self._handle_error("empty_value", field, value,
                                    f"Cannot update {actual_field} with empty value. Only update when you have actual user-provided information.")
        
        if data[actual_field] is not None and str(data[actual_field]) == str(value):
            return self._handle_error("duplicate_value", field, value,
                                    f"Field {actual_field} already has value '{data[actual_field]}'. No update needed unless user provides new information.")
        
        # Type conversion for numeric fields
        if actual_field == "age":
            try:
                data[actual_field] = int(value)
            except ValueError:
                return self._handle_error("type_conversion", field, value,
                                        f"Error: {actual_field} must be a whole number, got '{value}' ")
        elif actual_field == "height":
            try:
                # Handle height as float (removing any units like 'cm')
                clean_value = value.replace('cm', '').replace('centimeter', '').strip()
                data[actual_field] = float(clean_value)
            except ValueError:
                return self._handle_error("type_conversion", field, value,
                                        f"Error: {actual_field} must be a number in centimeters, got '{value}' ")
        elif actual_field == "weight":
            try:
                # Handle weight as float (removing any units like 'kg')
                clean_value = value.replace('kg', '').replace('kilo', '').strip()
                data[actual_field] = float(clean_value)
            except ValueError:
                return self._handle_error("type_conversion", field, value,
                                        f"Error: {actual_field} must be a number in kilograms, got '{value}' ")
        else:
            # All other fields (widget-based) remain as strings
            data[actual_field] = value
        
        # Success path
        self.save_data(data)
        result = f"Updated {actual_field} to {data[actual_field]}"
        
        self._log_function_call("update_data", 
                               {"field": field, "value": value, "current_data": data}, 
                               {"result": result, "actual_field": actual_field, "new_value": data[actual_field]}, 
                               {"success": True})
        
        # STAGE 2 TRACKING: Record successful execution
        self._add_to_session("update_data", {"field": field, "value": value}, result)
        return result
    
    @kernel_function(
        name="ask_question",
        description="Use this function, and ONLY this function, to ask the user a question. Your primary goal is to fill all data fields one by one. Call this function to ask the single next question in the data collection process."
    )
    def ask_question(
        self,
        field: str,
        message: str
    ) -> str:
        # Convert InputVariable to string if needed
        field = str(field) if hasattr(field, '__str__') else field
        message = str(message) if hasattr(message, '__str__') else message 
        data = self.load_data()
        
        # Simple field validation (normalize to lowercase for comparison)
        if field.lower() not in data:
            return self._handle_error("field_not_found", field, message,
                                    f"Error: Field '{field}' not found. Available fields: {list(data.keys())}")
        
        # Use the actual lowercase field name from data
        actual_field = field.lower()
        
        # WIDGET DETECTION: Check if this field requires widget UI
        if self._is_widget_field(actual_field):
            return self._handle_widget_question(actual_field, message)
        
        # Normal non-widget flow
        result = f"[ASKING] {actual_field}: {message}"
        
        self._log_function_call("ask_question", 
                               {"field": field, "message": message}, 
                               {"result": result, "actual_field": actual_field}, 
                               {"success": True})
        
        # STAGE 2 TRACKING: Record successful execution  
        self._add_to_session("ask_question", {"field": field, "message": message}, result)
        return result