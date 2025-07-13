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
            "\n=== PLANNER GUIDANCE ===",
            f"• MISSING FIELDS: {', '.join(missing[:5])}" + ("..." if len(missing) > 5 else "") if missing else 
            "• STATUS: All data collected, ready for recommendations"
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
        description="Ask a strategic question about a specific field. CRITICAL: Only call this function ONCE per response - never ask multiple questions simultaneously. As PLANNER AGENT, use strategic thinking to choose which field to ask about based on conversation context, user concerns, related health patterns, and available recommendations. Always include brief reasoning for your choice in your response message. You must use this function to ask questions so we can track which field you're targeting."
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
    
    def _calculate_bmi(self, data):
        """Calculate BMI if weight and height available - simple, no try-catch"""
        weight = data.get("weight")
        height = data.get("height") 
        
        if weight is None or height is None:
            return None
            
        # Direct validation - fail fast if invalid data
        if weight <= 0 or height <= 0:
            return None
            
        # Convert height to meters and calculate BMI
        height_m = height / 100
        return round(weight / (height_m * height_m), 1)
    
    def _get_bmi_category(self, bmi):
        """Get BMI category - simple conditions, no nested logic"""
        if bmi < 18.5:
            return "Underweight"
        if bmi < 25:
            return "Normal" 
        if bmi < 30:
            return "Overweight"
        return "Obese"
    
    def _load_actions_data(self):
        """Load actions.json for recommendations - fail fast if missing"""
        with open("data/actions.json", 'r') as f:
            return json.load(f)
    
    def _get_relevant_actions(self, data):
        """Process actions.json and return relevant recommendations based on current data"""
        actions_data = self._load_actions_data()
        reminders = actions_data["recommendations"]["reminders"]
        specialists = actions_data["recommendations"]["specialists"]
        
        # BMI-based insights
        bmi = self._calculate_bmi(data)
        bmi_insight = ""
        if bmi:
            category = self._get_bmi_category(bmi)
            bmi_insight = f"Current BMI: {bmi} ({category})"
        else:
            missing_fields = []
            if data.get("weight") is None:
                missing_fields.append("weight")
            if data.get("height") is None: 
                missing_fields.append("height")
            bmi_insight = f"BMI: Not available (missing {', '.join(missing_fields)})"
        
        # Simple condition matching - no nested loops
        applicable_reminders = []
        for reminder in reminders:
            conditions = reminder.get("conditions", {})
            
            # BMI condition check
            if "bmi_over_25" in conditions and bmi and bmi > 25:
                applicable_reminders.append(reminder)
                continue
                
            # Always recommend items
            if conditions.get("always_recommend"):
                applicable_reminders.append(reminder)
                continue
                
            # Gender-specific conditions
            if "gender" in conditions and data.get("gender") == conditions["gender"]:
                # Age condition for gender-specific items
                if "age_over" in conditions:
                    age = data.get("age")
                    if age and age > conditions["age_over"]:
                        applicable_reminders.append(reminder)
                else:
                    applicable_reminders.append(reminder)
                continue
                
            # Water intake condition
            if "water_intake_less_than" in conditions:
                water = data.get("water_intake")
                target = conditions["water_intake_less_than"]
                if water and water != target and water not in ["7-8 glasses (1400-1600 ml)", "More than 8 glasses (+1600 ml)"]:
                    applicable_reminders.append(reminder)
                continue
                
            # Supplement usage condition
            if "supplement_usage" in conditions and data.get("supplement_usage") == conditions["supplement_usage"]:
                applicable_reminders.append(reminder)
                continue
                
            # Smoking status condition (not in specific list)
            if "smoking_status_not" in conditions:
                smoking = data.get("smoking_status")
                if smoking and smoking not in conditions["smoking_status_not"]:
                    applicable_reminders.append(reminder)
                continue
                
            # Low sleep quality condition
            if "sleep_quality_low" in conditions:
                sleep = data.get("sleep_quality")
                if sleep and sleep in conditions["sleep_quality_low"]:
                    applicable_reminders.append(reminder)
                continue
                
            # Low mood condition
            if "mood_level_low" in conditions:
                mood = data.get("mood_level")
                if mood and mood in conditions["mood_level_low"]:
                    applicable_reminders.append(reminder)
                continue
                
            # High sugar intake condition
            if "sugar_intake_high" in conditions:
                sugar = data.get("sugar_intake")
                if sugar and sugar in conditions["sugar_intake_high"]:
                    applicable_reminders.append(reminder)
                continue
                
            # Low stress (high stress level) condition
            if "stress_level_low" in conditions:
                stress = data.get("stress_level")
                if stress and stress in conditions["stress_level_low"]:
                    applicable_reminders.append(reminder)
                continue
                
            # Low activity level condition
            if "activity_level_low" in conditions:
                activity = data.get("activity_level")
                if activity and activity in conditions["activity_level_low"]:
                    applicable_reminders.append(reminder)
                continue
        
        # Applicable specialists - simple matching
        applicable_specialists = []
        for specialist in specialists:
            conditions = specialist.get("conditions", {})
            
            # Has children condition
            if "has_children" in conditions:
                children = data.get("has_children")
                if children and children in conditions["has_children"]:
                    applicable_specialists.append(specialist)
        
        return {
            "bmi_insight": bmi_insight,
            "applicable_reminders": applicable_reminders,
            "applicable_specialists": applicable_specialists
        }
    
    def get_data_status_with_insights(self) -> str:
        """Enhanced data status with BMI and health insights for PLANNER AGENT"""
        data = self.load_data()
        
        # Get basic data status sections
        filled = {key: value for key, value in data.items() if value is not None}
        missing = [key for key, value in data.items() if value is None]
        
        # Build enhanced sections
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
        
        # Add health insights section
        insights = self._get_relevant_actions(data)
        health_section = [
            f"\n=== HEALTH INSIGHTS ===",
            f"• {insights['bmi_insight']}",
            f"• Available recommendations: {len(insights['applicable_reminders'])} reminders, {len(insights['applicable_specialists'])} specialists"
        ]
        
        next_action = [
            "\n=== PLANNER AGENT GUIDANCE ===",
            f"• NEXT ACTION: Strategic question for '{missing[0]}' field OR related field based on context" if missing else 
            "• NEXT ACTION: Provide personalized recommendations - call provide_recommendations()"
        ]
        
        return "\n".join(recorded_section + missing_section + health_section + next_action)
    
    @kernel_function(
        name="provide_recommendations",
        description="Provide final health recommendations and complete the planning session. Use this when you have sufficient data to give personalized health advice and want to end the data collection phase."
    )
    def _parse_recommendations(self, recommendations_text):
        """Parse structured recommendation format - simple regex approach"""
        import re
        from datetime import datetime
        
        # Split into recommendation part and Nora instructions
        parts = recommendations_text.split("</FINAL_RECOMMENDATION>")
        recommendation_xml = parts[0] + "</FINAL_RECOMMENDATION>"
        nora_instructions = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse each priority level - simple regex patterns
        priority_pattern = r'<(\w+_priority)>\s*<explanation>(.*?)</explanation>\s*<action_list>\[(.*?)\]</action_list>\s*</\w+_priority>'
        matches = re.findall(priority_pattern, recommendation_xml, re.DOTALL)
        
        parsed_recommendations = {}
        for priority_level, explanation, actions in matches:
            # Clean up action list - split by comma and strip whitespace
            action_list = [action.strip() for action in actions.split(',')]
            parsed_recommendations[priority_level] = {
                "explanation": explanation.strip(),
                "actions": action_list
            }
        
        return parsed_recommendations, nora_instructions.replace("Nora,", "").strip()
    
    def _save_recommendations(self, parsed_recs, nora_instructions, user_data, insights):
        """Save structured recommendations to data/recommendations.json"""
        from datetime import datetime
        
        # Build comprehensive recommendation record
        recommendation_record = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "session_type": "health_data_collection",
                "planner_agent_version": "v1.0"
            },
            "user_profile": {
                "basic_info": {
                    "age": user_data.get("age"),
                    "gender": user_data.get("gender"),
                    "bmi": self._calculate_bmi(user_data),
                    "bmi_category": self._get_bmi_category(self._calculate_bmi(user_data)) if self._calculate_bmi(user_data) else None
                },
                "health_indicators": {
                    "smoking_status": user_data.get("smoking_status"),
                    "activity_level": user_data.get("activity_level"),
                    "sleep_quality": user_data.get("sleep_quality"),
                    "stress_level": user_data.get("stress_level"),
                    "water_intake": user_data.get("water_intake"),
                    "has_children": user_data.get("has_children")
                },
                "all_data": user_data
            },
            "recommendations": {
                "structured_output": parsed_recs,
                "available_actions_count": {
                    "reminders": len(insights['applicable_reminders']),
                    "specialists": len(insights['applicable_specialists'])
                },
                "nora_instructions": nora_instructions
            },
            "justifications": {
                "key_risk_factors": self._identify_risk_factors(user_data),
                "health_insights": insights['bmi_insight'],
                "recommendation_reasoning": "Based on user profile analysis and available health action conditions"
            }
        }
        
        # Save to recommendations.json - fail fast if directory issue
        with open("data/recommendations.json", 'w') as f:
            json.dump(recommendation_record, f, indent=2)
        
        return recommendation_record
    
    def _identify_risk_factors(self, user_data):
        """Identify key risk factors for justification"""
        risk_factors = []
        
        # High priority risks
        smoking = user_data.get("smoking_status")
        if smoking and smoking not in ["No", "Social smoker (few days a week)"]:
            risk_factors.append(f"Heavy smoking: {smoking}")
        
        # BMI risks
        bmi = self._calculate_bmi(user_data)
        if bmi:
            if bmi >= 30:
                risk_factors.append(f"Obesity: BMI {bmi}")
            elif bmi >= 25:
                risk_factors.append(f"Overweight: BMI {bmi}")
            elif bmi < 18.5:
                risk_factors.append(f"Underweight: BMI {bmi}")
        
        # Pregnancy considerations
        children = user_data.get("has_children")
        if children == "Pregnant":
            risk_factors.append("Pregnancy: requires specialized health attention")
        
        # Low water intake
        water = user_data.get("water_intake")
        if water and "1-2 glasses" in water:
            risk_factors.append("Severe dehydration risk: very low water intake")
        
        # Mental health indicators
        sleep = user_data.get("sleep_quality")
        stress = user_data.get("stress_level")
        if sleep in ["Never", "Sometimes"] and stress in ["Never", "Sometimes"]:
            risk_factors.append("Mental health concerns: poor sleep and high stress")
        
        return risk_factors if risk_factors else ["No major risk factors identified"]

    @kernel_function(
        name="provide_recommendations",
        description="Provide final health recommendations and complete the planning session. Use this when you have sufficient data to give personalized health advice and want to end the data collection phase."
    )
    def provide_recommendations(
        self,
        recommendations: str
    ) -> str:
        """Complete planning phase with structured recommendations and save to file"""
        data = self.load_data()
        insights = self._get_relevant_actions(data)
        
        # Parse the structured recommendations
        parsed_recs, nora_instructions = self._parse_recommendations(recommendations)
        
        # Save structured recommendations to file
        recommendation_record = self._save_recommendations(parsed_recs, nora_instructions, data, insights)
        
        result = f"[RECOMMENDATIONS PROVIDED] Planning session complete.\n\nUser recommendations:\n{recommendations}\n\nAvailable actions: {len(insights['applicable_reminders'])} reminders, {len(insights['applicable_specialists'])} specialists\n\n💾 Recommendations saved to: data/recommendations.json"
        
        self._log_function_call("provide_recommendations",
                               {"recommendations": recommendations, "user_data": data},
                               {"result": result, "available_actions": insights, "saved_file": "data/recommendations.json"},
                               {"success": True, "session_complete": True})
        
        # STAGE 2 TRACKING: Record completion
        self._add_to_session("provide_recommendations", {"recommendations": recommendations}, result)
        return result