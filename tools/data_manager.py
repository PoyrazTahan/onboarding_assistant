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
        """Handle widget-enabled field question with UI display and auto-update"""
        # Log initial ask_question for telemetry
        self._log_function_call("ask_question", 
                               {"field": field, "message": message}, 
                               {"widget_detected": True}, 
                               {"success": True, "widget": True})
        
        # STAGE 2 TRACKING: Record widget ask
        self._add_to_session("ask_question", {"field": field, "message": message}, 
                           f"[WIDGET_TRIGGERED] {field}: {message}")
        
        try:
            # Initialize widget handler if needed (lazy loading)
            if not self.widget_handler:
                from ui.widget_handler import WidgetHandler
                self.widget_handler = WidgetHandler()
            
            # Get widget configuration for this field
            widget_config = self.widget_config["widget_fields"][field]
            
            # Create widget question structure
            widget_question = {
                "question_text": message,
                "field": field,
                "options": widget_config.get("options", []),
                "type": widget_config.get("type", "select")
            }
            
            # Show widget UI and get user selection (ACTUAL VALUE, not number)
            selected_value = self.widget_handler.show_widget_interface(widget_question)
            
            if selected_value:
                # Automatically update data with selected value
                update_result = self.update_data(field, selected_value)
                
                # STAGE 2 TRACKING: Record widget completion
                self._add_to_session("widget_complete", 
                                   {"field": field, "selected_value": selected_value}, 
                                   f"[WIDGET_COMPLETED] {field}: {selected_value}")
                
                # Return result that shows user ALREADY PROVIDED the answer via widget
                # This makes LLM think user answered the question, not that we're still asking
                return f"[USER_ANSWERED] {field}: User selected {selected_value} via interactive widget. {field.capitalize()} has been updated."
            else:
                # Widget was cancelled or failed
                return f"{message}\n❌ Widget selection cancelled"
                
        except Exception as e:
            # Fallback to normal question if widget fails
            error_msg = f"Widget error: {e}"
            self._log_function_call("ask_question", 
                                   {"field": field, "message": message}, 
                                   {"widget_error": error_msg}, 
                                   {"success": False, "widget": True})
            
            # Fall back to normal asking behavior
            return f"[ASKING] {field}: {message} (widget unavailable)"
        
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
        description="Update a specific field ONLY when you have actual user-provided information. Do NOT call with empty values or duplicate existing data."
    )
    def update_data(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to update (must be: age, weight, or height) field type is case insensitive",
            is_required=True
        ),
        value: str = InputVariable(
            name="value", 
            description="New value to set (numbers for age/height)",
            is_required=True
        )
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
        
        # Type conversion
        if actual_field in ["age", "height"]:
            try:
                data[actual_field] = int(value)
            except ValueError:
                return self._handle_error("type_conversion", field, value,
                                        f"Error: {actual_field} must be a number, got '{value}'")
        else:
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
        description="Ask user for specific missing information"
    )
    def ask_question(
        self,
        field: str = InputVariable(
            name="field",
            description="Field name to ask about (age, weight, or height), field type is case insensitive",
            is_required=True
        ),
        message: str = InputVariable(
            name="message",
            description="Custom message to display to user",
            is_required=True
        )
    ) -> str:
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