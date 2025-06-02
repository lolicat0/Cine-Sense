"""
Machine Learning Models and Data Schemas
"""

from .ml_model import MovieRecommendationEngine
from .schemas import UserPreferences, MovieResponse, RecommendationResponse, ErrorResponse

__all__ = [
    "MovieRecommendationEngine",
    "UserPreferences", 
    "MovieResponse", 
    "RecommendationResponse", 
    "ErrorResponse"
]