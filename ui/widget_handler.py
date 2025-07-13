import json
import random
import sys
from datetime import datetime
from typing import Optional, Dict, List
from semantic_kernel.functions import kernel_function

# Test mode detection - can be overridden for Jupyter usage
# For Jupyter: import ui.widget_handler; ui.widget_handler.TEST_MODE = True
TEST_MODE = "--test" in sys.argv

class WidgetHandler:
    """Handles widget interactions for immutable fields"""
    
    def __init__(self, user_id: str = "user"):
        self.user_id = user_id
        self.base_path = f"../data/{user_id}"
        self.user_data_path = f"{self.base_path}/user_data.json"
        self.questions_path = "./data/questions.json"
    
    def _load_json(self, file_path: str) -> Dict:
        """Load JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: str, data: Dict) -> bool:
        """Save JSON file safely"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
            return False
    
    def get_unanswered_widget_questions(self) -> List[Dict]:
        """Get all unanswered widget questions ordered by order field"""
        # Load current data
        user_data = self._load_json(self.user_data_path)
        questions_data = self._load_json(self.questions_path)
        
        # Find answered fields
        answered_fields = set()
        if "data_fields" in user_data:
            for field, data in user_data["data_fields"].items():
                if data.get("value") is not None:
                    answered_fields.add(field)
        
        # Filter widget questions that aren't answered and sort by order
        unanswered = []
        for question in questions_data.get("questions", []):
            if (question.get("type") == "widget" and 
                question.get("field") not in answered_fields):
                unanswered.append(question)
        
        # Sort by order field to make it deterministic
        unanswered.sort(key=lambda x: x.get("order", 999))
        
        return unanswered
    
    def show_widget_interface(self, question: Dict, test_value: Optional[str] = None) -> Optional[str]:
        """Show widget interface and get user selection"""
        from ui.chat_ui import print_widget_box
        
        question_text = question['question_text']
        
        # Handle different question formats
        if "options" in question:
            # Regular options question - extract display text for UI
            option_objects = question["options"]
            display_options = [opt["display_tr"] for opt in option_objects]
            options = display_options  # For UI display
        elif question.get("expected_format") == "scale":
            # Scale question (1-10)
            scale = question.get("scale", "1-10")
            start, end = map(int, scale.split("-"))
            options = [str(i) for i in range(start, end + 1)]
            option_objects = None  # No mapping needed for scales
        else:
            print("❌ No options available for this question")
            return None
        
        # Show widget box with all options
        print_widget_box(question_text, options)
        
        # TEST MODE: Automated selection
        if TEST_MODE and test_value is not None:
            expected_value = test_value
            
            if option_objects:  # Widget with value/display mapping
                # Try exact match with English values first
                english_values = [opt["value"] for opt in option_objects]
                if expected_value in english_values:
                    option_index = english_values.index(expected_value)
                    selected_display = options[option_index]  # Turkish display
                    selected_value = expected_value  # English value
                    print(f"    🤖 TEST MODE: Auto-selecting option {option_index + 1}: '{selected_display}' -> '{selected_value}'")
                else:
                    # Treat test value as option number (1-based)
                    option_index = int(expected_value) - 1
                    selected_display = options[option_index]  # Turkish display
                    selected_value = option_objects[option_index]["value"]  # English value
                    print(f"    🤖 TEST MODE: Auto-selecting option {int(expected_value)}: '{selected_display}' -> '{selected_value}'")
                
                print_widget_box(question_text, options, selected_display)
                return selected_value  # Return English value for data consistency
            else:  # Scale questions - no mapping needed
                option_number = int(expected_value)
                selected_option = options[option_number - 1]
                print(f"    🤖 TEST MODE: Auto-selecting option {option_number}: '{selected_option}'")
                print_widget_box(question_text, options, selected_option)
                return selected_option
        
        # INTERACTIVE MODE: Get user input
        while True:
            try:
                user_input = input("    Seçiminizi yapın (sadece rakam): ").strip()
                choice_num = int(user_input)
                
                if 1 <= choice_num <= len(options):
                    choice_index = choice_num - 1
                    selected_display = options[choice_index]  # Turkish display
                    
                    if option_objects:  # Widget with value/display mapping
                        selected_value = option_objects[choice_index]["value"]  # English value
                        print_widget_box(question_text, options, selected_display)
                        return selected_value  # Return English value for data consistency
                    else:  # Scale questions - no mapping needed
                        print_widget_box(question_text, options, selected_display)
                        return selected_display
                else:
                    print(f"    ❌ Lütfen 1-{len(options)} arasında bir rakam girin")
                    
            except ValueError:
                print("    ❌ Lütfen sadece rakam girin")
            except (KeyboardInterrupt, EOFError):
                print("\n    ❌ Widget iptal edildi")
                if options:
                    choice_index = 0
                    selected_display = options[choice_index]
                    
                    if option_objects:  # Widget with value/display mapping
                        selected_value = option_objects[choice_index]["value"]  # English value
                        print_widget_box(question_text, options, selected_display)
                        return selected_value
                    else:  # Scale questions
                        print_widget_box(question_text, options, selected_display)
                        return selected_display
                return None
    
    
    
    def trigger_widget(self) -> str:
        """Legacy compatibility - triggers first unanswered widget"""
        unanswered = self.get_unanswered_widget_questions()
        
        if not unanswered:
            return "Tüm widget soruları tamamlandı!"
        
        # Use first unanswered question
        question = unanswered[0]
        return self.ask_question(question["field"], f"Widget soru: {question['question_text']}")
    
