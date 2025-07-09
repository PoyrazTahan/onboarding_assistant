import json
import os
from datetime import datetime
from typing import List, Dict, Any

class ConversationManager:
    """Manages clean conversation history separate from LLM context with session support"""
    
    def __init__(self, user_id: str = "user", session_based: bool = True, conversations_path: str = None):
        self.user_id = user_id
        self.session_based = session_based
        self.current_session_id = self._generate_session_id() if session_based else None
        
        # Use provided conversations_path or default to user folder
        if conversations_path:
            self.base_path = conversations_path
        else:
            self.base_path = f"/Users/dogapoyraztahan/_repos/heltia/onboarding_assistant/data/{user_id}"
        
        if session_based:
            self.conversation_path = f"{self.base_path}/{self.current_session_id}.json"
            self.conversation_history = []  # Always start fresh for sessions
        else:
            self.conversation_path = f"{self.base_path}/conversation_history.json"
            self.conversation_history = self._load_conversation_history()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_conversation_history(self) -> List[Dict[str, Any]]:
        """Load conversation history from file"""
        try:
            if os.path.exists(self.conversation_path):
                with open(self.conversation_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("messages", [])
            return []
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []
    
    def _save_conversation_history(self):
        """Save conversation history to file"""
        try:
            # Ensure directory exists
            os.makedirs(self.base_path, exist_ok=True)
            
            data = {
                "user_id": self.user_id,
                "session_id": self.current_session_id if self.session_based else "persistent",
                "session_based": self.session_based,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_messages": len(self.conversation_history),
                "messages": self.conversation_history
            }
            
            with open(self.conversation_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving conversation history: {e}")
    
    def add_user_message(self, message: str):
        """Add a clean user message to history"""
        self.conversation_history.append({
            "role": "user",
            "content": message.strip(),
            "timestamp": datetime.now().isoformat()
        })
        self._save_conversation_history()
    
    def add_assistant_message(self, message: str):
        """Add a clean assistant message to history"""
        # Clean the message of any function call artifacts
        cleaned_message = self._clean_assistant_message(message)
        
        self.conversation_history.append({
            "role": "assistant", 
            "content": cleaned_message,
            "timestamp": datetime.now().isoformat()
        })
        self._save_conversation_history()
    
    def add_widget_exchange(self, question: str, answer: str):
        """Add widget question and answer as natural conversation"""
        # Add widget question as system message (different from assistant)
        self.conversation_history.append({
            "role": "system",
            "content": f"📋 Widget Question: {question.strip()}",
            "timestamp": datetime.now().isoformat(),
            "type": "widget_question"
        })
        
        # Add widget answer as user message  
        self.conversation_history.append({
            "role": "user",
            "content": answer.strip(),
            "timestamp": datetime.now().isoformat(),
            "type": "widget_answer"
        })
        
        self._save_conversation_history()
    
    def _clean_assistant_message(self, message: str) -> str:
        """Clean assistant message of function calls and artifacts"""
        import re
        
        # Remove function call patterns
        cleaned = re.sub(r'\[Call[^\]]*\]', '', message)
        cleaned = re.sub(r'\[\]', '', cleaned)
        cleaned = re.sub(r'trigger_widget\(\)', '', cleaned)
        cleaned = re.sub(r'get_user_status\(\)', '', cleaned)
        cleaned = re.sub(r'get_questions\(\)', '', cleaned)
        cleaned = re.sub(r'get_question_details\([^)]*\)', '', cleaned)
        cleaned = re.sub(r'ask_question\([^)]*\)', '', cleaned)
        cleaned = re.sub(r'update_user_data\([^)]*\)', '', cleaned)
        cleaned = re.sub(r'Widget completed: [^\n]*', '', cleaned)
        
        # Remove Gemini 2.5-flash specific patterns
        cleaned = re.sub(r'<call:>[^>]*', '', cleaned)
        cleaned = re.sub(r'<call:>', '', cleaned)
        cleaned = re.sub(r'```tool_code[^`]*```', '', cleaned)
        
        # Remove repetitive phrases and duplicates
        sentences = [s.strip() for s in cleaned.split('.') if s.strip()]
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            if sentence.lower() not in seen and len(sentence) > 5:
                unique_sentences.append(sentence)
                seen.add(sentence.lower())
        
        cleaned = '. '.join(unique_sentences)
        if cleaned and not cleaned.endswith('.'):
            cleaned += '.'
            
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def get_conversation_for_llm(self) -> str:
        """Get conversation history formatted for LLM context"""
        if not self.conversation_history:
            return ""
        
        formatted = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            if msg["role"] == "user":
                role = "Kullanıcı"
            elif msg["role"] == "system":
                role = "Sistem"
            else:
                role = "Asistan"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def get_conversation_for_display(self) -> List[Dict[str, Any]]:
        """Get conversation history for display purposes"""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self._save_conversation_history()
    
    def get_last_message(self, role: str = None) -> Dict[str, Any]:
        """Get the last message, optionally filtered by role"""
        if not self.conversation_history:
            return None
            
        if role:
            for msg in reversed(self.conversation_history):
                if msg["role"] == role:
                    return msg
            return None
        else:
            return self.conversation_history[-1]
    
    def export_conversation(self) -> str:
        """Export conversation as readable text"""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        
        session_info = f" - Oturum {self.current_session_id}" if self.session_based else ""
        formatted = [f"📞 Konuşma Geçmişi - {self.user_id}{session_info}"]
        formatted.append("=" * 50)
        
        for i, msg in enumerate(self.conversation_history, 1):
            if msg["role"] == "user":
                role_icon = "👤"
                role_name = "Sen"
            elif msg["role"] == "system":
                role_icon = "📋"
                role_name = "Widget"
            else:
                role_icon = "🤖"
                role_name = "Asistan"
            
            timestamp = msg.get("timestamp", "")[:19].replace("T", " ")
            
            formatted.append(f"\n{i:2d}. {role_icon} {role_name} ({timestamp}):")
            formatted.append(f"    {msg['content']}")
        
        return "\n".join(formatted)
    
    def get_session_files(self) -> List[str]:
        """Get list of session files for this user"""
        if not os.path.exists(self.base_path):
            return []
        
        session_files = []
        for filename in os.listdir(self.base_path):
            if filename.endswith(".json") and filename != "conversation_history.json":
                session_files.append(os.path.join(self.base_path, filename))
        
        return sorted(session_files, reverse=True)  # Most recent first
    
    def load_session(self, session_id: str):
        """Load a specific session"""
        session_path = f"{self.base_path}/{session_id}.json"
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversation_history = data.get("messages", [])
                    self.current_session_id = session_id
                    self.conversation_path = session_path
                    return True
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
        return False
    
    def start_new_session(self):
        """Start a new session (only for session-based mode)"""
        if self.session_based:
            self.current_session_id = self._generate_session_id()
            self.conversation_path = f"{self.base_path}/{self.current_session_id}.json"
            self.conversation_history = []
            print(f"🔄 Yeni oturum başlatıldı: {self.current_session_id}")
    
    def get_current_session_info(self) -> Dict[str, Any]:
        """Get information about current session"""
        return {
            "session_id": self.current_session_id,
            "session_based": self.session_based,
            "message_count": len(self.conversation_history),
            "session_file": self.conversation_path
        }