"""
Utility Functions and AI Integrations
"""

from .gemini_integration import GeminiEnhancer, ClaudeEnhancer

__all__ = ["GeminiEnhancer", "ClaudeEnhancer"]

# Utility functions
def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate basic text similarity between two strings"""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def format_duration(minutes: int) -> str:
    """Format duration in minutes to readable string"""
    if minutes < 60:
        return f"{minutes} min"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}min" if mins > 0 else f"{hours}h"