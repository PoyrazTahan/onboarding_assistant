#!/usr/bin/env python3
"""
Dictionary utilities for comparing and tracking changes
"""

def dict_diff(dict1, dict2):
    """
    Compare two dictionaries and return the differences
    
    Args:
        dict1: Initial dictionary state
        dict2: Final dictionary state
        
    Returns:
        dict: Changes in format {'key': {'from': old_value, 'to': new_value}}
    """
    changes = {}
    
    # Check all keys from both dictionaries
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        old_value = dict1.get(key)
        new_value = dict2.get(key)
        
        # Only record if values are different
        if old_value != new_value:
            changes[key] = {'from': old_value, 'to': new_value}
    
    return changes