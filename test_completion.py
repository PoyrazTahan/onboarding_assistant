#!/usr/bin/env python3
"""
Test case for verifying AI stops asking questions when profile is complete
"""
import json

# Test data states
test_cases = [
    {
        "name": "All fields filled - should acknowledge completion",
        "data_state": {"age": 25, "weight": "70kg", "height": 170},
        "user_input": "Hello",
        "expected_behavior": "Should thank user and confirm profile is complete, NOT ask for more data"
    },
    {
        "name": "Only height missing - should ask for height",
        "data_state": {"age": 25, "weight": "70kg", "height": None},
        "user_input": "Hi there",
        "expected_behavior": "Should ask for height"
    },
    {
        "name": "User provides already recorded data",
        "data_state": {"age": 25, "weight": None, "height": None},
        "user_input": "I'm 25 years old",
        "expected_behavior": "Should NOT update age (already 25), should ask for weight"
    },
    {
        "name": "User updates existing data",
        "data_state": {"age": 25, "weight": None, "height": None},
        "user_input": "Actually I'm 26",
        "expected_behavior": "Should update age to 26, then ask for weight"
    }
]

print("Test Cases for Reasoning-Based Prompt\n")
print("="*60)

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Current Data: {test['data_state']}")
    print(f"User Says: '{test['user_input']}'")
    print(f"Expected: {test['expected_behavior']}")
    
    # Check completion status
    missing = [k for k, v in test['data_state'].items() if v is None]
    if not missing:
        print("⚠️  CRITICAL: All fields filled - AI should recognize completion!")
    
print("\n" + "="*60)
print("\nTo run these tests:")
print("1. Set data.json to each test state")
print("2. Run simple_agent.py with the test input")
print("3. Verify AI behavior matches expected")