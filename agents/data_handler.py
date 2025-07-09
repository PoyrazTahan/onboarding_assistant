import json
import os
from datetime import datetime
from typing import Dict, Any, List
from semantic_kernel.functions import kernel_function

class DataHandler:
    """Handles data operations for user profiles and system configurations"""
    
    def __init__(self, user_id: str = "user"):
        self.user_id = user_id
        self.base_path = f"/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/{user_id}"
        self.user_data_path = f"{self.base_path}/user_data.json"
        self.questions_path = "/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/questions.json"
        # REMOVED: actions_path - not needed for data collection phase
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON file safely"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
            return False
    
    @kernel_function(
        name="get_user_status",
        description="Get curated user status and question progress for LLM decision making"
    )
    def get_user_status_and_questions(self) -> str:
        """Get curated user status and question progress for LLM decision making"""
        user_data = self._load_json(self.user_data_path)
        questions_data = self._load_json(self.questions_path)
        
        # Build curated status summary
        status_lines = []
        
        # Progress overview
        completed_fields = []
        pending_questions = []
        
        # Process each question by order
        for question in sorted(questions_data.get("questions", []), key=lambda x: x["order"]):
            field = question["field"]
            question_type = question["type"]
            question_text = question["question_text"]
            order = question["order"]
            
            # Check if answered
            current_value = None
            is_answered = False
            
            if "data_fields" in user_data and field in user_data["data_fields"]:
                field_data = user_data["data_fields"][field]
                current_value = field_data.get("value")
                is_answered = current_value is not None
            
            if is_answered:
                completed_fields.append(f"{field}={current_value}")
            else:
                pending_questions.append({
                    "field": field,
                    "type": question_type,
                    "question": question_text,
                    "order": order,
                    "validation": question.get("validation", ""),
                    "instructions": question.get("instructions", "")
                })
        
        # Build focused status summary
        total_questions = len(questions_data.get("questions", []))
        completed_count = len(completed_fields)
        
        status_lines.append(f"PROGRESS: {completed_count}/{total_questions} questions completed")
        
        if completed_fields:
            status_lines.append(f"COMPLETED: {', '.join(completed_fields)}")
        
        if pending_questions:
            next_question = pending_questions[0]  # Next in order
            status_lines.append(f"NEXT: {next_question['field']} ({next_question['type']}) - Order {next_question['order']}")
            status_lines.append(f"QUESTION: {next_question['question']}")
            
            if next_question['type'] == 'free_form':
                if next_question['validation']:
                    status_lines.append(f"VALIDATION: {next_question['validation']}")
                if next_question['instructions']:
                    status_lines.append(f"INSTRUCTIONS: {next_question['instructions']}")
            
            # Show remaining questions
            remaining_fields = [q['field'] for q in pending_questions]
            status_lines.append(f"REMAINING: {', '.join(remaining_fields)}")
        else:
            status_lines.append("STATUS: All questions completed!")
        
        return "\n".join(status_lines)
    
    @kernel_function(
        name="update_user_data",
        description="Update mutable user data fields (age, height, weight only)"
    )
    def update_user_data(self, field_name: str, value: str) -> str:
        """Update a mutable field with new value"""
        
        # Load current data
        user_data = self._load_json(self.user_data_path)
        
        # Check if field exists and is writable
        if "data_fields" not in user_data or field_name not in user_data["data_fields"]:
            return f"Error: Field '{field_name}' not found in user data"
        
        field_data = user_data["data_fields"][field_name]
        if field_data.get("permissions") != "read_write":
            return f"Error: Field '{field_name}' is read-only. Only read_write fields can be updated."
        
        # Validate and convert value
        try:
            if field_name == "age":
                # Convert age to integer
                numeric_value = int(value)
                if not (18 <= numeric_value <= 120):
                    return f"Error: Age must be between 18 and 120, got {numeric_value}"
            elif field_name == "height":
                # Convert height to integer (cm)
                numeric_value = int(value)
                if not (100 <= numeric_value <= 250):
                    return f"Error: Height must be between 100 and 250 cm, got {numeric_value}"
            elif field_name == "weight":
                # Convert weight to integer (kg)
                numeric_value = int(value)
                if not (30 <= numeric_value <= 300):
                    return f"Error: Weight must be between 30 and 300 kg, got {numeric_value}"
            else:
                return f"Error: Unknown field '{field_name}'"
        except ValueError:
            return f"Error: Could not convert '{value}' to number for field '{field_name}'"
        
        # Update the field
        user_data["data_fields"][field_name]["value"] = numeric_value
        user_data["data_fields"][field_name]["updated_at"] = datetime.now().isoformat()
        user_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated data
        if self._save_json(self.user_data_path, user_data):
            return f"Successfully updated {field_name} to {numeric_value}"
        else:
            return f"Error: Could not save update for {field_name}"
    
    @kernel_function(
        name="get_questions",
        description="Get focused questions overview for LLM context"
    )
    def get_questions(self) -> str:
        """Get curated questions overview for LLM decision making"""
        questions_data = self._load_json(self.questions_path)
        
        if "questions" not in questions_data:
            return "Error: No questions found in configuration"
        
        # Create focused overview
        overview_lines = []
        overview_lines.append("QUESTION SEQUENCE:")
        
        free_form_questions = []
        widget_questions = []
        
        # Group by type and sort by order
        for q in sorted(questions_data["questions"], key=lambda x: x["order"]):
            field = q["field"]
            question_type = q["type"]
            order = q["order"]
            
            if question_type == "free_form":
                free_form_questions.append(f"{order}. {field} (free-form)")
            else:
                widget_questions.append(f"{order}. {field} (widget)")
        
        # Present focused summary
        overview_lines.append("Free-form (LLM can update): " + ", ".join(free_form_questions))
        overview_lines.append("Widget (read-only): " + ", ".join(widget_questions))
        
        overview_lines.append("\nTOTAL: " + str(len(questions_data["questions"])) + " questions")
        
        return "\n".join(overview_lines)
    
    @kernel_function(
        name="get_question_details",
        description="Get specific question details for LLM when needed"
    )
    def get_question_details(self, field_name: str) -> str:
        """Get specific question details for focused LLM processing"""
        questions_data = self._load_json(self.questions_path)
        
        # Find the specific question
        for q in questions_data.get("questions", []):
            if q["field"] == field_name:
                details = []
                details.append(f"FIELD: {q['field']}")
                details.append(f"TYPE: {q['type']}")
                details.append(f"QUESTION: {q['question_text']}")
                details.append(f"ORDER: {q['order']}")
                
                if q["type"] == "free_form":
                    if q.get("validation"):
                        details.append(f"VALIDATION: {q['validation']}")
                    if q.get("instructions"):
                        details.append(f"INSTRUCTIONS: {q['instructions']}")
                elif q["type"] == "widget":
                    if q.get("options"):
                        details.append(f"OPTIONS: {', '.join(q['options'])}")
                
                return "\n".join(details)
        
        return f"Error: Question '{field_name}' not found"
    
    def update_widget_data(self, field_name: str, value: str) -> str:
        """Update widget data in user_data.json"""
        
        # Load current data
        user_data = self._load_json(self.user_data_path)
        
        # Check if field exists in data_fields
        if "data_fields" not in user_data:
            return f"Error: No data_fields section found"
        
        if field_name not in user_data["data_fields"]:
            return f"Error: Field '{field_name}' not found in data_fields"
        
        # Update the field
        user_data["data_fields"][field_name]["value"] = value
        user_data["data_fields"][field_name]["updated_at"] = datetime.now().isoformat()
        user_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated data
        if self._save_json(self.user_data_path, user_data):
            return f"Successfully updated {field_name} to {value}"
        else:
            return f"Error: Could not save update for {field_name}"
    
    @kernel_function(
        name="ask_question", 
        description="Ask a specific question with contextual message. Auto-detects widget vs free-form and handles appropriately."
    )
    def ask_question(self, field: str, contextual_message: str) -> str:
        """Ask a specific question with contextual reasoning - auto-detects widget vs free-form"""
        
        # First determine if this is a widget question
        questions_data = self._load_json(self.questions_path)
        target_question = None
        
        for question in questions_data.get("questions", []):
            if question.get("field") == field:
                target_question = question
                break
        
        if not target_question:
            return f"Error: Unknown field '{field}'"
        
        # Check if this field is already answered
        user_data = self._load_json(self.user_data_path)
        if ("data_fields" in user_data and 
            field in user_data["data_fields"] and 
            user_data["data_fields"][field].get("value") is not None):
            return f"Question for {field} already answered"
        
        # For widget questions, show contextual message + trigger widget interface
        if target_question["type"] == "widget":
            # Show LLM's contextual message
            print(f"\n🤖 Asistan: {contextual_message}")
            
            # Show widget interface with the actual question from questions.json
            from ui.widgets.widget_handler import WidgetHandler
            widget_handler = WidgetHandler(self.user_id)
            selected_answer = widget_handler.show_widget_interface(target_question)
            
            if selected_answer is None:
                return "Widget iptal edildi"
            
            # Update data
            success = self.update_widget_data(field, selected_answer)
            
            if "Successfully updated" in success:
                # Add to conversation history as widget_question
                from utils.conversation_manager import ConversationManager
                conv_manager = ConversationManager(self.user_id, session_based=True, 
                                                  conversations_path="/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/conversations")
                conv_manager.add_widget_exchange(
                    question=target_question["question_text"],
                    answer=selected_answer
                )
                
                # Return confirmation (this won't be shown to user)
                return f"Widget completed: {field} = {selected_answer}"
            else:
                return f"Widget güncelleme hatası: {success}"
        
        # For free-form questions, return the contextual message
        else:
            return f"{contextual_message} (Free-form question for {field})"