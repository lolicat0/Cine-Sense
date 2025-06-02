"""
CineSense Backend Application
AI-Powered Movie Recommendation System
"""

__version__ = "1.0.0"
__author__ = "CineSense Team"
__description__ = "AI-Powered Movie Recommendation System"

# Import main components for easy access
from .main import app
from .models.ml_model import MovieRecommendationEngine
from .data.movie_dataset import MovieDatabase
from .utils.gemini_integration import GeminiEnhancer, ClaudeEnhancer

__all__ = [
    "app",
    "MovieRecommendationEngine", 
    "MovieDatabase",
    "GeminiEnhancer",
    "ClaudeEnhancer"
]