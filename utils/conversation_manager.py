#!/usr/bin/env python3
"""
ConversationManager for tracking user/assistant messages and tool calls
Designed for flexibility with multiple output formats and session management
"""
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

@dataclass
class ToolCall:
    function_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None
    
@dataclass
class ToolResult:
    call_id: Optional[str]
    function_name: str
    result: Any
    success: bool = True
    error: Optional[str] = None

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    message_id: str
    session_id: str
    tool_calls: List[ToolCall] = None
    tool_results: List[ToolResult] = None
    metadata: Dict[str, Any] = None

class ConversationManager:
    """
    Manages conversation history with separation of user/assistant messages
    and detailed tool call tracking
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.messages: List[Message] = []
        self.message_counter = 0
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID within this session"""
        self.message_counter += 1
        return f"{self.session_id}_msg_{self.message_counter:03d}"
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a user message to the conversation"""
        message_id = self._generate_message_id()
        
        message = Message(
            role=MessageType.USER.value,
            content=content,
            timestamp=datetime.datetime.now().isoformat(),
            message_id=message_id,
            session_id=self.session_id,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        return message_id
    
    def add_assistant_message(
        self, 
        content: str, 
        sk_response = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add an assistant message, extracting tool calls from SK response
        
        Args:
            content: The text content of the assistant's response
            sk_response: The full Semantic Kernel response object
            metadata: Additional metadata to store
        """
        message_id = self._generate_message_id()
        
        # Extract tool calls from SK response if available
        tool_calls = []
        tool_results = []
        
        if sk_response and hasattr(sk_response, 'value') and sk_response.value:
            chat_message = sk_response.value[0] if sk_response.value else None
            
            if chat_message:
                # Extract tool calls from metadata or function_call_results
                if hasattr(chat_message, 'metadata') and chat_message.metadata:
                    # Look for tool calls in metadata
                    if 'tool_calls' in chat_message.metadata:
                        for tool_call in chat_message.metadata['tool_calls']:
                            tool_calls.append(ToolCall(
                                function_name=tool_call.get('function', {}).get('name', ''),
                                arguments=tool_call.get('function', {}).get('arguments', {}),
                                call_id=tool_call.get('id')
                            ))
                
                # Extract function call results if available
                if hasattr(chat_message, 'items') and chat_message.items:
                    for item in chat_message.items:
                        if hasattr(item, 'function_call_result'):
                            tool_results.append(ToolResult(
                                call_id=None,  # May not be available
                                function_name=item.function_call_result.function_name,
                                result=item.function_call_result.result,
                                success=True
                            ))
        
        message = Message(
            role=MessageType.ASSISTANT.value,
            content=content,
            timestamp=datetime.datetime.now().isoformat(),
            message_id=message_id,
            session_id=self.session_id,
            tool_calls=tool_calls if tool_calls else None,
            tool_results=tool_results if tool_results else None,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        return message_id
    
    def add_tool_call_manually(
        self, 
        function_name: str, 
        arguments: Dict[str, Any], 
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> str:
        """
        Manually add a tool call and result (for cases where SK doesn't capture it)
        """
        message_id = self._generate_message_id()
        
        tool_call = ToolCall(
            function_name=function_name,
            arguments=arguments,
            call_id=f"manual_{message_id}"
        )
        
        tool_result = ToolResult(
            call_id=tool_call.call_id,
            function_name=function_name,
            result=result,
            success=success,
            error=error
        )
        
        message = Message(
            role="tool_execution",
            content=f"Tool call: {function_name}({arguments}) -> {result}",
            timestamp=datetime.datetime.now().isoformat(),
            message_id=message_id,
            session_id=self.session_id,
            tool_calls=[tool_call],
            tool_results=[tool_result]
        )
        
        self.messages.append(message)
        return message_id
    
    # === RETRIEVAL METHODS ===
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages in chronological order"""
        return self.messages.copy()
    
    def get_user_messages(self) -> List[Message]:
        """Get only user messages"""
        return [msg for msg in self.messages if msg.role == MessageType.USER.value]
    
    def get_assistant_messages(self) -> List[Message]:
        """Get only assistant messages"""
        return [msg for msg in self.messages if msg.role == MessageType.ASSISTANT.value]
    
    def get_tool_calls_history(self) -> List[Dict[str, Any]]:
        """Get all tool calls and their results"""
        tool_history = []
        
        for msg in self.messages:
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Find corresponding result
                    result = None
                    if msg.tool_results:
                        result = next((r for r in msg.tool_results 
                                     if r.call_id == tool_call.call_id), None)
                    
                    tool_history.append({
                        'timestamp': msg.timestamp,
                        'message_id': msg.message_id,
                        'function_name': tool_call.function_name,
                        'arguments': tool_call.arguments,
                        'result': result.result if result else None,
                        'success': result.success if result else None,
                        'error': result.error if result else None
                    })
        
        return tool_history
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        user_msgs = self.get_user_messages()
        assistant_msgs = self.get_assistant_messages()
        tool_calls = self.get_tool_calls_history()
        
        return {
            'session_id': self.session_id,
            'total_messages': len(self.messages),
            'user_messages': len(user_msgs),
            'assistant_messages': len(assistant_msgs),
            'tool_calls': len(tool_calls),
            'start_time': self.messages[0].timestamp if self.messages else None,
            'end_time': self.messages[-1].timestamp if self.messages else None,
            'functions_used': list(set(tc['function_name'] for tc in tool_calls))
        }
    
    def get_conversation_turns(self) -> List[Dict[str, Any]]:
        """Get conversation organized by turns (user -> assistant actions)"""
        turns = []
        current_turn = None
        
        for msg in self.messages:
            if msg.role == MessageType.USER.value:
                # Start new turn
                current_turn = {
                    'user_message': msg.content,
                    'user_timestamp': msg.timestamp,
                    'assistant_actions': []
                }
                turns.append(current_turn)
            
            elif msg.role == MessageType.ASSISTANT.value and current_turn:
                # Add assistant response to current turn
                action = {
                    'type': 'response',
                    'content': msg.content,
                    'timestamp': msg.timestamp
                }
                current_turn['assistant_actions'].append(action)
            
            elif msg.role == 'tool_execution' and current_turn:
                # Add tool calls to current turn
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        result = None
                        if msg.tool_results:
                            result = next((r for r in msg.tool_results 
                                         if r.call_id == tool_call.call_id), None)
                        
                        action = {
                            'type': 'tool_call',
                            'function_name': tool_call.function_name,
                            'arguments': tool_call.arguments,
                            'result': result.result if result else None,
                            'timestamp': msg.timestamp
                        }
                        current_turn['assistant_actions'].append(action)
        
        return turns
    
    # === EXPORT METHODS (Future extensibility) ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire conversation to dictionary"""
        return {
            'session_id': self.session_id,
            'messages': [asdict(msg) for msg in self.messages],
            'summary': self.get_conversation_summary()
        }
    
    def to_json_string(self) -> str:
        """Convert to JSON string (for future JSON export)"""
        import json
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def print_conversation(self, include_tool_calls: bool = True):
        """Print a formatted view of the conversation"""
        print(f"\n=== CONVERSATION HISTORY ({self.session_id}) ===")
        
        for msg in self.messages:
            timestamp = msg.timestamp.split('T')[1][:8]  # Just time part
            
            if msg.role == MessageType.USER.value:
                print(f"\n[{timestamp}] 👤 USER:")
                print(f"  {msg.content}")
            
            elif msg.role == MessageType.ASSISTANT.value:
                print(f"\n[{timestamp}] 🤖 ASSISTANT:")
                print(f"  {msg.content}")
                
                if include_tool_calls and msg.tool_calls:
                    print(f"  🔧 TOOL CALLS:")
                    for tool_call in msg.tool_calls:
                        print(f"    - {tool_call.function_name}({tool_call.arguments})")
                        
                        if msg.tool_results:
                            result = next((r for r in msg.tool_results 
                                         if r.call_id == tool_call.call_id), None)
                            if result:
                                print(f"      → {result.result}")
        
        print(f"\n=== SUMMARY ===")
        summary = self.get_conversation_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("=" * 50)
    
    def print_conversation_turns(self):
        """Print conversation organized by turns showing all assistant actions grouped"""
        print(f"\n🔄 CONVERSATION FLOW ({self.session_id})")
        print("=" * 50)
        
        turns = self.get_conversation_turns()
        
        for i, turn in enumerate(turns, 1):
            user_time = turn['user_timestamp'].split('T')[1][:8]
            
            print(f"\n📍 TURN {i}")
            print(f"   👤 [{user_time}] USER: {turn['user_message']}")
            
            if turn['assistant_actions']:
                print(f"   🤖 ASSISTANT:")
                # Sort actions by timestamp to show in correct order
                actions = sorted(turn['assistant_actions'], key=lambda x: x['timestamp'])
                
                for j, action in enumerate(actions, 1):
                    action_time = action['timestamp'].split('T')[1][:8]
                    
                    if action['type'] == 'tool_call':
                        # Format arguments nicely - truncate long values
                        formatted_args = []
                        for k, v in action['arguments'].items():
                            v_str = str(v)
                            if len(v_str) > 40:
                                v_str = v_str[:37] + "..."
                            formatted_args.append(f"{k}='{v_str}'")
                        args_str = ", ".join(formatted_args)
                        print(f"      🔧 [{action_time}] {action['function_name']}({args_str})")
                        if action['result']:
                            print(f"         → {action['result']}")
                    
                    elif action['type'] == 'response':
                        print(f"      💬 [{action_time}] \"{action['content']}\"")
            else:
                print(f"   🤖 (no actions recorded)")
        
        print("=" * 50)