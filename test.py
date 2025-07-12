#!/usr/bin/env python3
"""
Test runner with automated evaluation - Runs test scenarios and validates results
PRODUCTION: Delete this file and use app.py directly
"""

import json
import sys
import os
import asyncio
import shutil
from datetime import datetime
from pathlib import Path

def load_test_scenarios():
    """Load test scenarios from test.json"""
    with open("data/test.json", 'r') as f:
        data = json.load(f)
    return data.get("test_scenarios", [])

def setup_test_data(scenario):
    """Setup data.json for specific test scenario"""
    # Default empty state
    default_data = {"age": None, "weight": None, "height": None}
    
    # Apply existing data if specified
    if "existing_data" in scenario:
        default_data.update(scenario["existing_data"])
    
    # Save to data.json
    with open("data/data.json", 'w') as f:
        json.dump(default_data, f, indent=2)
    
    print(f"📋 Setup data state: {default_data}")

def setup_test_outputs(test_name):
    """Setup clean output directories for test run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = f".test_results/{test_name.replace(' ', '_')}_{timestamp}"
    
    # Create test output directory
    Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    Path(f"{test_dir}/sessions").mkdir(exist_ok=True)
    Path(f"{test_dir}/telemetry").mkdir(exist_ok=True)
    
    return test_dir

def compare_results(final_data, expected_data):
    """Compare final results with expected results"""
    mismatches = []
    
    for field, expected_value in expected_data.items():
        actual_value = final_data.get(field)
        if actual_value != expected_value:
            mismatches.append({
                "field": field,
                "expected": expected_value,
                "actual": actual_value
            })
    
    return len(mismatches) == 0, mismatches

def backup_test_results(test_dir, scenario):
    """Move generated files to test directory after run"""
    # Move only the current session file (newest one)
    if os.path.exists("data/sessions"):
        session_files = [f for f in os.listdir("data/sessions") if f.endswith(".json")]
        if session_files:
            # Get the most recent session file (this test's file)
            newest_session = max(session_files, key=lambda f: os.path.getctime(f"data/sessions/{f}"))
            shutil.move(f"data/sessions/{newest_session}", f"{test_dir}/sessions/session.json")
    
    # Create enhanced final data with test evaluation
    if os.path.exists("data/data.json"):
        with open("data/data.json", 'r') as f:
            final_data = json.load(f)
        
        # Get expected results and starting data
        expected_data = scenario.get("expected_result", {})
        start_data = scenario.get("existing_data", {"age": None, "weight": None, "height": None})
        
        # Compare results
        test_passed, mismatches = compare_results(final_data, expected_data)
        
        # Create comprehensive test result
        test_result = {
            "test_name": scenario["name"],
            "start_data": start_data,
            "final_data": final_data,
            "expected_data": expected_data,
            "test_passed": test_passed,
            "mismatches": mismatches
        }
        
        # Save enhanced result
        with open(f"{test_dir}/final_data.json", 'w') as f:
            json.dump(test_result, f, indent=2)
        
        return test_passed, mismatches
    
    return False, [{"error": "No final data found"}]

def list_tests():
    """List available test scenarios"""
    scenarios = load_test_scenarios()
    print("📋 Available test scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        name = scenario["name"]
        inputs = scenario["inputs"]
        existing = scenario.get("existing_data", {})
        
        print(f"  {i}. {name}")
        if existing:
            filled = [k for k, v in existing.items() if v is not None]
            print(f"     Pre-filled: {filled}")
        print(f"     Will test: {list(inputs.keys())}")
    print()

def run_specific_test(test_number):
    """Run a specific test by number"""
    scenarios = load_test_scenarios()
    
    if test_number < 1 or test_number > len(scenarios):
        print(f"❌ Invalid test number. Available: 1-{len(scenarios)}")
        return None
    
    scenario = scenarios[test_number - 1]
    test_name = scenario["name"]
    print(f"🧪 Running: {test_name}")
    
    # Setup output directory
    test_dir = setup_test_outputs(test_name)
    print(f"📁 Test outputs: {test_dir}")
    
    # Setup data state
    setup_test_data(scenario)
    
    # Update test.json to use this scenario's inputs (backward compatibility)
    with open("data/test.json", 'r') as f:
        test_data = json.load(f)
    
    # Create legacy format for existing test infrastructure
    legacy_inputs = scenario["inputs"]
    test_data.update(legacy_inputs)
    
    with open("data/test.json", 'w') as f:
        json.dump(test_data, f, indent=2)
    
    return test_dir

async def main():
    """Main test runner"""
    
    # No arguments = run all tests
    if len(sys.argv) < 2:
        scenarios = load_test_scenarios()
        print(f"🧪 Running ALL {len(scenarios)} test scenarios")
        
        passed_tests = 0
        failed_tests = 0
        
        for i in range(1, len(scenarios) + 1):
            print(f"\n{'='*60}")
            print(f"🔄 Test {i}/{len(scenarios)}")
            
            test_dir = run_specific_test(i)
            if not test_dir:
                continue
                
            print("🚀 Starting test execution...")
            
            # Setup sys.argv for app.py
            original_argv = sys.argv.copy()
            sys.argv = ["app.py", "--test"]
            
            try:
                from app import main as app_main
                await app_main()
            finally:
                scenario = scenarios[i-1]
                test_passed, mismatches = backup_test_results(test_dir, scenario)
                sys.argv = original_argv
            
            # Display test result
            if test_passed:
                print(f"✅ Test {i} PASSED - Results in: {test_dir}")
                passed_tests += 1
            else:
                print(f"❌ Test {i} FAILED - Results in: {test_dir}")
                print(f"   Mismatches: {len(mismatches)}")
                for mismatch in mismatches:
                    print(f"   • {mismatch['field']}: expected {mismatch['expected']}, got {mismatch['actual']}")
                failed_tests += 1
        
        print(f"\n{'='*60}")
        print(f"🎉 ALL TESTS COMPLETED: {passed_tests} passed, {failed_tests} failed")
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
        
        # Setup test
        test_dir = run_specific_test(test_number)
        if not test_dir:
            return
        
        # Import and run app.py
        print("🚀 Starting test execution...")
        print("=" * 50)
        
        # Add --test flag and any additional flags
        original_argv = sys.argv.copy()
        sys.argv = ["app.py", "--test"]
        
        # Add debug if requested
        if "--debug" in original_argv:
            sys.argv.append("--debug")
        
        try:
            # Import and run the main app
            from app import main as app_main
            await app_main()
        finally:
            # Always backup results and restore argv
            scenarios = load_test_scenarios()
            scenario = scenarios[test_number-1]
            test_passed, mismatches = backup_test_results(test_dir, scenario)
            sys.argv = original_argv
        
        print("=" * 50)
        if test_passed:
            print(f"✅ Test PASSED - Results in: {test_dir}")
        else:
            print(f"❌ Test FAILED - Results in: {test_dir}")
            print(f"Mismatches: {len(mismatches)}")
            for mismatch in mismatches:
                print(f"• {mismatch['field']}: expected {mismatch['expected']}, got {mismatch['actual']}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'list' or 'run <test_number>'")

if __name__ == "__main__":
    asyncio.run(main())