#!/usr/bin/env python3
"""
DataManager - Handles data.json operations with case-insensitive field names
Provides kernel functions for updating and querying user data
"""

import json
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable

class DataManager:
    """Manages the simple data.json file"""
    
    def __init__(self, data_file="data/data.json", conversation_manager=None):
        self.data_file = data_file
        self.conversation_manager = conversation_manager
        
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
        
        # === RECORDED DATA SECTION ===
        status_report.append("=== RECORDED USER DATA ===")
        if not filled:
            status_report.append("• No data recorded yet")
        else:
            for field, value in filled.items():
                if field == "age":
                    status_report.append(f"- Age: {value}")
                elif field == "weight":
                    status_report.append(f"- Weight: {value}")
                elif field == "height":
                    status_report.append(f"- Height: {value}")
        
        # === MISSING FIELDS SECTION ===
        status_report.append("\n=== MISSING FIELDS ===")
        if not missing:
            status_report.append("• All fields complete!")
        else:
            for field in missing:
                if field == "age":
                    status_report.append("• Age: null")
                elif field == "weight":
                    status_report.append("• Weight: null")
                elif field == "height":
                    status_report.append("• Height: null")
        
        # === NEXT ACTION GUIDANCE ===
        status_report.append("\n=== WORKFLOW GUIDANCE ===")
        if missing:
            next_field = missing[0]  # First missing field
            status_report.append(f"• NEXT ACTION: Ask question for '{next_field}' field")
        else:
            status_report.append("• NEXT ACTION: All data collected, end conversation")
        
        return "\n".join(status_report)
    
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
        # DETAILED TRACKING: Add timestamp and call counter
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🚀 [{timestamp}] Function called: update_data(field='{field}', value='{value}')")
        
        data = self.load_data()
        print(f"   📊 Current data before update: {data}")
        
        # Make field case-insensitive by checking lowercase versions
        field_lower = field.lower()
        available_fields = list(data.keys())
        field_map = {f.lower(): f for f in available_fields}
        
        if field_lower not in field_map:
            error_msg = f"Error: Field '{field}' not found. Available fields: {available_fields}"
            print(f"   ❌ {error_msg}")
            return error_msg
        
        # Use the correctly cased field name
        actual_field = field_map[field_lower]
        
        print(f"   🔄 Attempting to update '{actual_field}' from '{data[actual_field]}' to '{value}'")
        
        # VALIDATION: Prevent empty/meaningless updates
        if not value or value.strip() == '':
            error_msg = f"Cannot update {actual_field} with empty value. Only update when you have actual user-provided information."
            print(f"   ❌ {error_msg}")
            return error_msg
        
        # VALIDATION: Prevent unnecessary updates of existing data
        current_value = data[actual_field]
        if current_value is not None and str(current_value) == str(value):
            error_msg = f"Field {actual_field} already has value '{current_value}'. No update needed unless user provides new information."
            print(f"   ⚠️ {error_msg}")
            return error_msg
        
        # Convert to appropriate type
        if actual_field in ["age", "height"]:
            try:
                data[actual_field] = int(value)
            except ValueError:
                error_msg = f"Error: {actual_field} must be a number, got '{value}'"
                print(f"   ❌ {error_msg}")
                return error_msg
        else:
            data[actual_field] = value
        
        self.save_data(data)
        result = f"Updated {actual_field} to {data[actual_field]}"
        print(f"   ✅ {result}")
        print(f"   📊 Data after update: {data}")
        print()
        
        # Update function call result in conversation manager
        if self.conversation_manager:
            self.conversation_manager.add_tool_call_manually(
                function_name="update_data",
                arguments={"field": field, "value": value},
                result=result,
                success=True
            )
        
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
        # DETAILED TRACKING: Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"💬 [{timestamp}] Function called: ask_question(field='{field}', message='{message}')")
        
        data = self.load_data()
        print(f"   📊 Current data: {data}")
        
        # Make field case-insensitive
        field_lower = field.lower()
        available_fields = list(data.keys())
        field_map = {f.lower(): f for f in available_fields}
        
        if field_lower in field_map:
            actual_field = field_map[field_lower]
            print(f"   🤔 Asking about field '{actual_field}' which currently has value: {data.get(actual_field, 'NOT_FOUND')}")
            result = f"[ASKING] {actual_field}: {message}"
        else:
            print(f"   🤔 Asking about field '{field}' which currently has value: NOT_FOUND")
            result = f"[ASKING] {field}: {message}"
        
        print(f"   📝 Result: {result}")
        print()
        
        # Update function call result in conversation manager
        if self.conversation_manager:
            self.conversation_manager.add_tool_call_manually(
                function_name="ask_question",
                arguments={"field": field, "message": message},
                result=result,
                success=True
            )
        
        return result