#!/usr/bin/env python3
"""
Core Agent Test Runner - Clean test automation for data collection scenarios
"""

import json
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from ui.chat_ui import print_system_message, print_user_message

def load_test_scenarios():
    """Load test scenarios from test.json"""
    with open("data/test.json", 'r') as f:
        data = json.load(f)
    return data.get("test_scenarios", [])

def setup_test_data(scenario):
    """Setup test data - only modify if existing_data specified"""
    existing_data = scenario.get("existing_data", {})
    
    if existing_data:
        # Load current data.json and update with pre-filled fields
        with open("data/data.json", 'r') as f:
            current_data = json.load(f)
        
        current_data.update(existing_data)
        
        with open("data/data.json", 'w') as f:
            json.dump(current_data, f, indent=2)
            
        return current_data
    
    # No existing_data - use current data.json as-is
    with open("data/data.json", 'r') as f:
        return json.load(f)

def evaluate_test(scenario):
    """Evaluate test result - compare actual vs expected"""
    if not os.path.exists("data/data.json"):
        return False, [{"error": "No final data found"}], {}
    
    with open("data/data.json", 'r') as f:
        final_data = json.load(f)
    
    expected_data = scenario.get("expected_result", {})
    mismatches = []
    
    for field, expected_value in expected_data.items():
        actual_value = final_data.get(field)
        if actual_value != expected_value:
            mismatches.append({
                "field": field,
                "expected": expected_value,
                "actual": actual_value
            })
    
    return len(mismatches) == 0, mismatches, final_data

def print_test_summary(test_num, scenario, test_passed, mismatches, final_data, start_data):
    """Print concise test summary"""
    status = "✅ PASS" if test_passed else "❌ FAIL"
    profile = scenario.get("profile", "generic")
    
    print(f"{test_num:2d}. {status} {scenario['name']} ({profile})")
    
    if not test_passed:
        print(f"    Mismatches: {len(mismatches)}")
        for mismatch in mismatches[:3]:  # Show first 3 mismatches
            field = mismatch['field']
            expected = mismatch['expected']
            actual = mismatch['actual']
            print(f"    • {field}: expected '{expected}', got '{actual}'")
        if len(mismatches) > 3:
            print(f"    • ... and {len(mismatches) - 3} more")
    
    # Show data completion stats
    filled_fields = sum(1 for v in final_data.values() if v is not None)
    total_fields = len(final_data)
    pre_filled = sum(1 for v in start_data.values() if v is not None)
    
    print(f"    Data: {pre_filled}→{filled_fields}/{total_fields} fields")

def save_session_result(scenario, final_data, test_passed, mismatches, session_id):
    """Save complete session result with test evaluation"""
    import os
    results_dir = ".test_results"
    os.makedirs(results_dir, exist_ok=True)
    
    test_name = scenario['name'].replace(' ', '_').lower()
    
    session_result = {
        "test_info": {
            "name": scenario['name'],
            "profile": scenario.get('profile', 'generic'),
            "description": scenario.get('description', ''),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        },
        "inputs_provided": scenario.get('inputs', {}),
        "expected_result": scenario.get('expected_result', {}),
        "actual_result": final_data,
        "test_evaluation": {
            "passed": test_passed,
            "total_fields": len(scenario.get('expected_result', {})),
            "matched_fields": len(scenario.get('expected_result', {})) - len(mismatches),
            "mismatches": mismatches
        },
        "data_completion": {
            "filled_fields": sum(1 for v in final_data.values() if v is not None),
            "total_fields": len(final_data),
            "completion_rate": sum(1 for v in final_data.values() if v is not None) / len(final_data) if final_data else 0
        }
    }
    
    result_file = f"{results_dir}/{test_name}.json"
    with open(result_file, 'w') as f:
        json.dump(session_result, f, indent=2)
    
    status = "✅ PASS" if test_passed else "❌ FAIL"
    print(f"    💾 Session result saved: {result_file} ({status})")

async def run_core_agent_test(test_inputs, test_name="test"):
    """Run core agent test with provided inputs directly (no file overwriting)"""
    # Set up flags before import
    import sys
    original_argv = sys.argv.copy()
    sys.argv = ["test.py", "--test", "--core-agent"]
    
    try:
        # Import and setup  
        from core.agent import Agent
        from app import ConversationHandler
        
        # Initialize agent
        agent = Agent(debug_mode=False)
        await agent.initialize()
        
        # Start session
        session = agent.start_session()
        
        # Create test conversation handler with automation
        conversation_handler = TestConversationHandler(agent, test_name)
        await conversation_handler.run_test_mode(test_data=test_inputs)
        
        return agent
        
    finally:
        # Restore original argv
        sys.argv = original_argv

class TestConversationHandler:
    """Test automation handler - simulates user input for automated testing"""
    
    def __init__(self, agent, test_name):
        from app import ConversationHandler
        self.base_handler = ConversationHandler(agent)
        self.agent = agent
        self.test_name = test_name
        
    def _get_next_test_input(self, session):
        """Test automation: get next simulated user input"""
        # Check for pending widget first (highest priority)
        widget_info = session.stage_manager.get_pending_widget()
        if widget_info:
            return self._execute_test_widget(widget_info)
        
        # Check for test mode automation  
        test_response = session.stage_manager.get_pending_test_response()
        if test_response:
            print(f"    🎯 TEST MODE: Detected question, next input will be: '{test_response}'")
            return test_response
        
        # Fallback for test automation
        print(f"    🤖 TEST MODE: No question detected, continuing conversation")
        return "Please continue, try to use available functions_calls correctly."
    
    def _execute_test_widget(self, widget_info):
        """Execute widget with test automation"""
        # Get test value for this field
        session = self.agent.get_session()
        field = widget_info["field"]
        test_value = None
        
        if (hasattr(session.stage_manager, 'test_data') and 
            session.stage_manager.test_data and 
            field in session.stage_manager.test_data):
            test_value = session.stage_manager.test_data[field]
        
        # Initialize widget handler with test automation
        from ui.widget_handler import WidgetHandler
        widget_handler = WidgetHandler()
        
        # Execute widget with test value
        selected_value = widget_handler.show_widget_interface(
            widget_info["question_structure"], 
            test_value=test_value
        )
        
        if selected_value:
            # Auto-call update_data with selected value
            update_result = self.agent.data_manager.update_data(widget_info["field"], selected_value)
            print(f"    ✅ WIDGET: Auto-updated {widget_info['field']} = {selected_value}")
            
            # Store completion info for hidden LLM context injection
            widget_completion = {
                "field": widget_info["field"],
                "selected_value": selected_value,
                "update_result": update_result
            }
            
            # Store in session for next LLM call context injection
            session.stage_manager.widget_completion = widget_completion
            
            print(f"    🎛️ WIDGET: Selected '{selected_value}', using as next user input")
            return selected_value
        
        return "Please continue"
        
    async def run_test_mode(self, test_data=None):
        """Run test mode with automation"""
        print_system_message("🧪 Running in TEST MODE with automation")
        
        # Enable test mode on session's stage manager
        session = self.agent.get_session()
        if test_data is not None:
            session.stage_manager.enable_test_mode_with_data(test_data)
        else:
            session.stage_manager.enable_test_mode()
        
        # Handle initial greeting
        greeting = self.base_handler._get_greeting()
        if greeting:
            await self.base_handler._display_agent_message(greeting)
        
        # Start with initial greeting response
        user_input = "Hello, I need help filling out my data."
        turn_number = 0
        
        while not self.base_handler._is_complete() and turn_number < 20:  # Safety limit
            print_user_message(user_input)
            
            # Process input through agent
            response = await self.base_handler._process_input(user_input, turn_number=turn_number)
            await self.base_handler._display_agent_message(response)
            
            # Check if conversation is complete
            if self.base_handler._is_complete():
                print_system_message("✅ All data collected! Conversation complete.")
                break
            
            # Get next test input (handles both widgets and regular automation)
            user_input = self._get_next_test_input(session)
            
            turn_number += 1

async def run_test_scenario(scenario, test_number=None):
    """Run a single test scenario and return results"""
    start_data = setup_test_data(scenario)
    test_inputs = scenario.get("inputs", {})
    test_name = scenario['name'].replace(' ', '_').lower()
    
    try:
        agent = await run_core_agent_test(test_inputs, test_name)
    except Exception as e:
        error_msg = f"❌ CRASH {scenario['name']} - {str(e)}"
        if test_number:
            print(error_msg)
        return None, error_msg
    
    # Evaluate results
    test_passed, mismatches, final_data = evaluate_test(scenario)
    
    # Save session result
    session = agent.get_session()
    save_session_result(scenario, final_data, test_passed, mismatches, session.id)
    
    # Print summary
    display_number = test_number if test_number else ""
    print_test_summary(display_number, scenario, test_passed, mismatches, final_data, start_data)
    
    return test_passed, None

def list_tests():
    """List available test scenarios with profile information"""
    scenarios = load_test_scenarios()
    print("📋 Available test scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        name = scenario["name"]
        profile = scenario.get("profile", "generic")
        existing = scenario.get("existing_data", {})
        
        filled_count = sum(1 for v in existing.values() if v is not None) if existing else 0
        
        print(f"  {i:2d}. {name} ({profile}) - {filled_count} pre-filled")
    print()

async def main():
    """Main test runner with aggregated results"""
    
    # No arguments = run all tests
    if len(sys.argv) < 2:
        scenarios = load_test_scenarios()
        print(f"🧪 Core Agent Test Suite - {len(scenarios)} scenarios")
        print("=" * 60)
        
        passed_tests = 0
        failed_tests = 0
        
        for i, scenario in enumerate(scenarios, 1):
            result, error = await run_test_scenario(scenario, i)
            if result is None:  # Crashed
                print(f"  {i:2d}. {error}")
                failed_tests += 1
            elif result:  # Passed
                passed_tests += 1
            else:  # Failed
                failed_tests += 1
        
        print("=" * 60)
        print(f"📊 Results: {passed_tests} passed, {failed_tests} failed")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_tests()
        return
    
    if command == "run":
        if len(sys.argv) < 3:
            print("❌ Please specify test number")
            list_tests()
            return
        
        try:
            test_number = int(sys.argv[2])
        except ValueError:
            print("❌ Test number must be an integer")
            return
        
        # Get specific test scenario
        scenarios = load_test_scenarios()
        if test_number < 1 or test_number > len(scenarios):
            print(f"❌ Invalid test number. Available: 1-{len(scenarios)}")
            return
        
        scenario = scenarios[test_number - 1]
        print(f"🧪 Running: {scenario['name']} ({scenario.get('profile', 'generic')})")
        
        await run_test_scenario(scenario, test_number)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'list' or 'run <test_number>'")

if __name__ == "__main__":
    asyncio.run(main())