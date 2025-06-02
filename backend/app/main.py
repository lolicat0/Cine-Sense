from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import List, Dict, Any

from .models.ml_model import MovieRecommendationEngine
from .models.schemas import UserPreferences, MovieResponse, RecommendationResponse
from .utils.gemini_integration import GeminiEnhancer
from .data.movie_dataset import MovieDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CineSense API",
    description="AI-Powered Movie Recommendation System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
movie_db = MovieDatabase()
recommendation_engine = MovieRecommendationEngine()
gemini_enhancer = GeminiEnhancer()

@app.on_event("startup")
async def startup_event():
    """Initialize ML models and data on startup"""
    try:
        logger.info("Initializing CineSense API...")
        
        # Load movie database
        await movie_db.initialize()
        logger.info(f"Loaded {len(movie_db.movies)} movies")
        
        # Train recommendation model
        recommendation_engine.train(movie_db.get_training_data())
        logger.info("Recommendation engine trained successfully")
        
        logger.info("CineSense API initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CineSense API is running!", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database_size": len(movie_db.movies),
        "model_trained": recommendation_engine.is_trained()
    }

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(preferences: UserPreferences):
    """Get personalized movie recommendations"""
    try:
        logger.info(f"Processing recommendation request: {preferences.dict()}")
        
        # Get base recommendations from ML model
        base_recommendations = recommendation_engine.predict(preferences)
        
        # Enhance with Gemini if available
        enhanced_recommendations = await gemini_enhancer.enhance_recommendations(
            base_recommendations, preferences
        )
        
        # Format response
        movie_responses = []
        for movie_data in enhanced_recommendations:
            movie_responses.append(MovieResponse(**movie_data))
        
        response = RecommendationResponse(
            recommendations=movie_responses,
            total_count=len(movie_responses),
            preferences_summary=preferences.get_summary()
        )
        
        logger.info(f"Returning {len(movie_responses)} recommendations")
        return response
        
    except Exception as e:
        logger.error(f"Error processing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@app.get("/api/movies")
async def get_movies(
    genre: str = None,
    year: int = None,
    rating_min: float = None,
    limit: int = 20
):
    """Get movies with optional filters"""
    try:
        movies = movie_db.filter_movies(
            genre=genre,
            year=year,
            rating_min=rating_min,
            limit=limit
        )
        
        return {
            "movies": movies,
            "count": len(movies),
            "filters": {
                "genre": genre,
                "year": year,
                "rating_min": rating_min
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch movies")

@app.get("/api/genres")
async def get_genres():
    """Get all available genres"""
    return {"genres": movie_db.get_genres()}

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    return movie_db.get_stats()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)