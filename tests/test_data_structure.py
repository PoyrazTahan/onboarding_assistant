#!/usr/bin/env python3
"""
Simple test script to validate data structure and basic functionality
"""

import json
import os
from pathlib import Path

def test_data_structure():
    """Test if all required data files exist and have correct structure"""
    
    print("=== Testing Data Structure ===\n")
    
    # Test data files exist
    data_files = [
        "data/questions.json",
        "data/actions.json",
        "data/users/user_001/AI_mutable.json",
        "data/users/user_001/AI_immutable.json",
        "data/users/user_001/session_state.json"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
    
    print("\n=== Testing Questions Structure ===\n")
    
    # Test questions.json structure
    try:
        with open("data/questions.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
            print(f"✓ Questions file loaded successfully")
            print(f"✓ Total questions: {len(questions['questions'])}")
            
            # Check if all 13 fields are present
            fields = [q['field'] for q in questions['questions']]
            expected_fields = ['age', 'gender', 'height', 'weight', 'sleep', 'stress', 'wellbeing', 
                             'activity', 'sugar', 'water_consumption', 'smoking', 'supplements', 'parenting']
            
            print(f"✓ Fields found: {fields}")
            
            missing_fields = set(expected_fields) - set(fields)
            if missing_fields:
                print(f"✗ Missing fields: {missing_fields}")
            else:
                print(f"✓ All 13 fields present")
                
    except Exception as e:
        print(f"✗ Error loading questions: {e}")
    
    print("\n=== Testing Actions Structure ===\n")
    
    # Test actions.json structure
    try:
        with open("data/actions.json", "r", encoding="utf-8") as f:
            actions = json.load(f)
            print(f"✓ Actions file loaded successfully")
            print(f"✓ Total actions: {len(actions['actions'])}")
            
            # Show action categories
            categories = set(action['category'] for action in actions['actions'])
            print(f"✓ Action categories: {categories}")
            
    except Exception as e:
        print(f"✗ Error loading actions: {e}")
    
    print("\n=== Testing User Data Structure ===\n")
    
    # Test user mutable data structure (free-form fields only)
    try:
        with open("data/users/user_001/AI_mutable.json", "r", encoding="utf-8") as f:
            mutable_data = json.load(f)
            print(f"✓ Mutable data loaded successfully")
            print(f"✓ User ID: {mutable_data['user_id']}")
            print(f"✓ Free-form data fields: {len(mutable_data['free_form_data'])}")
            
            # Check free-form fields
            free_form_fields = list(mutable_data['free_form_data'].keys())
            expected_free_form = ['age', 'height', 'weight']
            
            print(f"✓ Free form fields: {free_form_fields}")
            
            if set(free_form_fields) == set(expected_free_form):
                print(f"✓ All expected free-form fields present")
            else:
                print(f"✗ Missing free-form fields: {set(expected_free_form) - set(free_form_fields)}")
            
    except Exception as e:
        print(f"✗ Error loading mutable data: {e}")
    
    # Test user immutable data structure (widget fields)
    try:
        with open("data/users/user_001/AI_immutable.json", "r", encoding="utf-8") as f:
            immutable_data = json.load(f)
            print(f"✓ Immutable data loaded successfully")
            print(f"✓ Widget data fields: {len(immutable_data['widget_data'])}")
            
            # Check widget fields
            widget_fields = list(immutable_data['widget_data'].keys())
            expected_widget = ['sleep', 'stress', 'wellbeing', 'activity', 'sugar', 'water_consumption', 'smoking', 'supplements', 'parenting', 'gender']
            
            print(f"✓ Widget fields: {widget_fields}")
            
            if set(widget_fields) == set(expected_widget):
                print(f"✓ All expected widget fields present")
            else:
                print(f"✗ Missing widget fields: {set(expected_widget) - set(widget_fields)}")
            
    except Exception as e:
        print(f"✗ Error loading immutable data: {e}")

def test_sample_inputs():
    """Test sample inputs and expected outputs"""
    
    print("\n=== Testing Sample Inputs ===\n")
    
    # Sample inputs for each field type
    sample_inputs = {
        "age": "25",
        "height": "175", 
        "weight": "70",
        "water_consumption": "6",
        "sleep": "7",
        "stress": "5",
        "gender": "Erkek",
        "activity": "Orta",
        "smoking": "Hayır"
    }
    
    print("Sample inputs to test:")
    for field, value in sample_inputs.items():
        print(f"  {field}: {value}")
    
    # This would be where we test actual agent responses
    print("\n✓ Sample inputs defined (agents not implemented yet)")

if __name__ == "__main__":
    test_data_structure()
    test_sample_inputs()
    print("\n=== Test Summary ===")
    print("Phase 1A: Data structure setup - READY")
    print("Next: Phase 1B - API Integration")