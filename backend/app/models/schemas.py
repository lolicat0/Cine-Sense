from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserPreferences(BaseModel):
    """User preference model for movie recommendations"""
    genres: List[str] = Field(..., min_items=1, description="Selected genres")
    mood: str = Field(..., description="Current mood")
    language: str = Field(..., description="Preferred language")
    decade: str = Field(..., description="Preferred decade")
    duration: str = Field(..., description="Preferred duration")
    rating: str = Field(..., description="Content rating preference")
    actors: Optional[str] = Field(None, description="Favorite actors")
    directors: Optional[str] = Field(None, description="Favorite directors")
    keywords: Optional[str] = Field(None, description="Keywords or themes")
    
    @validator('genres')
    def validate_genres(cls, v):
        valid_genres = [
            'Action', 'Adventure', 'Comedy', 'Drama', 'Horror', 'Romance',
            'Sci-Fi', 'Fantasy', 'Thriller', 'Mystery', 'Documentary', 'Animation'
        ]
        for genre in v:
            if genre not in valid_genres:
                raise ValueError(f'Invalid genre: {genre}')
        return v
    
    def get_summary(self) -> str:
        """Get a human-readable summary of preferences"""
        summary_parts = []
        
        if self.genres:
            summary_parts.append(f"Genres: {', '.join(self.genres)}")
        
        if self.mood:
            summary_parts.append(f"Mood: {self.mood}")
            
        if self.language and self.language != "Any Language":
            summary_parts.append(f"Language: {self.language}")
            
        if self.decade and self.decade != "No Preference":
            summary_parts.append(f"Era: {self.decade}")
            
        return " | ".join(summary_parts)

class MovieResponse(BaseModel):
    """Movie response model"""
    title: str
    genre: str
    description: str
    rating: float
    year: int
    duration: str
    director: Optional[str] = None
    actors: Optional[str] = None
    poster_url: Optional[str] = None
    confidence_score: Optional[float] = None
    imdb_id: Optional[str] = None
    tags: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Inception",
                "genre": "Sci-Fi, Thriller",
                "description": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                "rating": 8.8,
                "year": 2010,
                "duration": "148 min",
                "director": "Christopher Nolan",
                "actors": "Leonardo DiCaprio, Marion Cotillard, Tom Hardy",
                "confidence_score": 0.92,
                "tags": ["mind-bending", "complex plot", "visual effects"]
            }
        }

class RecommendationResponse(BaseModel):
    """Complete recommendation response"""
    recommendations: List[MovieResponse]
    total_count: int
    preferences_summary: str
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)