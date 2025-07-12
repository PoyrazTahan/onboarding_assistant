#!/usr/bin/env python3
"""
XML Parser Utility - Generic XML/HTML content extraction
Clean, reusable parsing functions following coding principles
"""

import re

def extract_xml_tags(text, tag_patterns, fallback_to_original=True):
    """
    Extract content from XML tags using multiple patterns
    
    Args:
        text (str): Text containing XML tags
        tag_patterns (list): List of regex patterns to try (e.g., ['<ChatBox>(.*?)</ChatBox>'])
        fallback_to_original (bool): Return original text if no matches found
        
    Returns:
        list: List of extracted text content
    """
    if not text or not text.strip():
        return []
    
    # Clean markdown code blocks if present
    cleaned_text = _remove_markdown_blocks(text)
    
    # Try each pattern until we find matches
    for pattern in tag_patterns:
        matches = re.findall(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
        if matches:
            results = []
            for match in matches:
                clean_content = match.strip()
                if clean_content:
                    results.append(clean_content)
            if results:
                return results
    
    # Fallback: strip all XML/HTML tags and return
    if fallback_to_original:
        clean_text = strip_html_tags(cleaned_text)
        return [clean_text] if clean_text else [text.strip()]
    
    return []

def _remove_markdown_blocks(text):
    """Remove markdown code blocks (```xml...```)"""
    if '```xml' in text:
        start = text.find('```xml') + 6
        end = text.find('```', start)
        if end != -1:
            return text[start:end].strip()
    return text

def strip_html_tags(text):
    """Remove HTML/XML tags and clean entities"""
    if not text:
        return ""
    
    # Remove all HTML/XML tags
    clean_text = re.sub(r'<[^>]*>', '', text)
    
    # Clean common HTML entities
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    
    return clean_text.strip()

# Common tag patterns for reuse
CHATBOX_PATTERNS = [
    r'<ChatBox>(.*?)</ChatBox>',
    r'<message>(.*?)</message>', 
    r'<mesaj>(.*?)</mesaj>',
    r'<text>(.*?)</text>'
]