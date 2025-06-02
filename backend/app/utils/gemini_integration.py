import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class GeminiEnhancer:
    """Gemini AI integration for enhancing movie recommendations"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("Gemini API key not found. Enhancement features disabled.")
    
    async def enhance_recommendations(self, recommendations: List[Dict[str, Any]], 
                                    preferences: 'UserPreferences') -> List[Dict[str, Any]]:
        """Enhance recommendations with Gemini insights"""
        if not self.enabled:
            return recommendations
        
        try:
            # Generate enhanced descriptions
            enhanced_recs = []
            for movie in recommendations:
                enhanced_movie = await self._enhance_single_movie(movie, preferences)
                enhanced_recs.append(enhanced_movie)
            
            return enhanced_recs
            
        except Exception as e:
            logger.error(f"Error enhancing recommendations with Gemini: {e}")
            return recommendations
    
    async def _enhance_single_movie(self, movie: Dict[str, Any], 
                                   preferences: 'UserPreferences') -> Dict[str, Any]:
        """Enhance a single movie recommendation"""
        if not self.enabled:
            return movie
        
        try:
            # Create prompt for Gemini
            prompt = self._create_enhancement_prompt(movie, preferences)
            
            # Call Gemini API (placeholder - implement actual API call)
            enhanced_description = await self._call_gemini_api(prompt)
            
            # Update movie data
            enhanced_movie = movie.copy()
            if enhanced_description:
                enhanced_movie['ai_description'] = enhanced_description
                enhanced_movie['enhanced'] = True
            
            return enhanced_movie
            
        except Exception as e:
            logger.error(f"Error enhancing movie {movie.get('title', 'Unknown')}: {e}")
            return movie
    
    def _create_enhancement_prompt(self, movie: Dict[str, Any], 
                                  preferences: 'UserPreferences') -> str:
        """Create prompt for Gemini to enhance movie description"""
        
        user_prefs = {
            'genres': preferences.genres,
            'mood': preferences.mood,
            'keywords': preferences.keywords or 'none specified'
        }
        
        prompt = f"""
        Based on the user's preferences and the movie details below, provide a personalized 
        explanation (2-3 sentences) of why this movie would appeal to them.

        User Preferences:
        - Favorite Genres: {', '.join(user_prefs['genres'])}
        - Current Mood: {user_prefs['mood']}
        - Keywords: {user_prefs['keywords']}

        Movie Details:
        - Title: {movie.get('title', 'Unknown')}
        - Genre: {movie.get('genre', 'Unknown')}
        - Description: {movie.get('description', 'No description available')}
        - Director: {movie.get('director', 'Unknown')}

        Please provide a compelling, personalized reason why this user would enjoy this movie.
        Focus on connecting the movie's elements to their stated preferences.
        """
        
        return prompt
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Call Gemini API - placeholder implementation"""
        # This is a placeholder. In a real implementation, you would:
        # 1. Install google-generativeai package
        # 2. Configure the API client
        # 3. Make the actual API call
        
        try:
            # Simulated API response for demonstration
            await asyncio.sleep(0.1)  # Simulate API call delay
            
            # Return a simulated enhancement
            return "This movie perfectly matches your preferences with its engaging storyline and excellent performances."
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None
    
    def generate_preference_insights(self, preferences: 'UserPreferences') -> str:
        """Generate insights about user preferences"""
        if not self.enabled:
            return "Preference analysis unavailable"
        
        # Create insight prompt
        prompt = f"""
        Analyze these movie preferences and provide 2-3 insights about the user's taste:
        
        Genres: {', '.join(preferences.genres)}
        Mood: {preferences.mood}
        Language: {preferences.language}
        Preferred Era: {preferences.decade}
        Duration: {preferences.duration}
        
        Provide brief, friendly insights about their movie taste.
        """
        
        # In real implementation, call Gemini API here
        return "Based on your preferences, you enjoy diverse storytelling with emotional depth."

# Alternative Claude Integration
class ClaudeEnhancer:
    """Claude AI integration for enhancing recommendations"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("Claude API key not found. Enhancement features disabled.")
    
    async def enhance_recommendations(self, recommendations: List[Dict[str, Any]], 
                                    preferences: 'UserPreferences') -> List[Dict[str, Any]]:
        """Enhance recommendations with Claude insights"""
        if not self.enabled:
            return recommendations
        
        try:
            enhanced_recs = []
            for movie in recommendations:
                enhanced_movie = await self._enhance_with_claude(movie, preferences)
                enhanced_recs.append(enhanced_movie)
            
            return enhanced_recs
            
        except Exception as e:
            logger.error(f"Error enhancing with Claude: {e}")
            return recommendations
    
    async def _enhance_with_claude(self, movie: Dict[str, Any], 
                                  preferences: 'UserPreferences') -> Dict[str, Any]:
        """Enhance movie with Claude analysis"""
        
        # Placeholder implementation
        enhanced_movie = movie.copy()
        enhanced_movie['ai_insight'] = f"Recommended because it matches your interest in {', '.join(preferences.genres[:2])} and your {preferences.mood.lower()} mood."
        enhanced_movie['enhanced'] = True
        
        return enhanced_movie