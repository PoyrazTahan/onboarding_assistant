import json
import random
from datetime import datetime
from typing import Optional, Dict, List
from semantic_kernel.functions import kernel_function

class WidgetHandler:
    """Handles widget interactions for immutable fields"""
    
    def __init__(self, user_id: str = "user"):
        self.user_id = user_id
        self.base_path = f"/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/{user_id}"
        self.user_data_path = f"{self.base_path}/user_data.json"
        self.questions_path = "/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/questions.json"
    
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
    
    def show_widget_interface(self, question: Dict) -> Optional[str]:
        """Show widget interface and get user selection"""
        from ui.chat_ui import print_widget_interface, print_widget_completed
        
        print_widget_interface()
        print(f"\n📝 {question['question_text']}")
        
        # Handle different question formats
        if "options" in question:
            # Regular options question
            options = question["options"]
            print("\nSeçenekler:")
            for i, option in enumerate(options, 1):
                print(f"{i}) {option}")
        elif question.get("expected_format") == "scale":
            # Scale question (1-10)
            scale = question.get("scale", "1-10")
            print(f"\nSeçenekler ({scale} arasında):")
            start, end = map(int, scale.split("-"))
            options = [str(i) for i in range(start, end + 1)]
            for i, option in enumerate(options, 1):
                print(f"{i}) {option}")
        else:
            print("❌ No options available for this question")
            return None
        
        # Get user input
        while True:
            try:
                user_input = input("\nSeçiminizi yapın (sadece rakam): ").strip()
                choice_num = int(user_input)
                
                if 1 <= choice_num <= len(options):
                    selected_option = options[choice_num - 1]
                    print(f"✅ Seçiminiz: {selected_option}")
                    print_widget_completed()
                    return selected_option
                else:
                    print(f"❌ Lütfen 1-{len(options)} arasında bir rakam girin")
                    
            except ValueError:
                print("❌ Lütfen sadece rakam girin")
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Widget iptal edildi (test mode)")
                # Return actual option text instead of just "1"
                if options:
                    selected_option = options[0]
                    print(f"✅ Test seçimi: {selected_option}")
                    return selected_option
                return "1"
    
    
    
    def trigger_widget(self) -> str:
        """Legacy compatibility - triggers first unanswered widget"""
        unanswered = self.get_unanswered_widget_questions()
        
        if not unanswered:
            return "Tüm widget soruları tamamlandı!"
        
        # Use first unanswered question
        question = unanswered[0]
        return self.ask_question(question["field"], f"Widget soru: {question['question_text']}")
    
