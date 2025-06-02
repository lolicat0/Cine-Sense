import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import logging
from typing import List, Dict, Any, Tuple
import re

logger = logging.getLogger(__name__)

class MovieRecommendationEngine:
    """Machine Learning powered movie recommendation engine"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self.knn_model = NearestNeighbors(
            n_neighbors=50,
            metric='cosine',
            algorithm='brute'
        )
        self.genre_encoder = LabelEncoder()
        self.mood_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.rating_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        
        self.is_model_trained = False
        self.feature_names = []
        self.movies_df = None
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text data"""
        if not text or pd.isna(text):
            return ""
        
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def create_content_features(self, movie_data: Dict) -> str:
        """Create combined content features for similarity matching"""
        features = []
        
        # Add genre information
        if movie_data.get('genre'):
            features.append(movie_data['genre'])
        
        # Add plot/description
        if movie_data.get('description'):
            features.append(movie_data['description'])
            
        # Add director and actors
        if movie_data.get('director'):
            features.append(movie_data['director'])
            
        if movie_data.get('actors'):
            features.append(movie_data['actors'])
            
        # Add keywords/tags
        if movie_data.get('tags'):
            features.extend(movie_data['tags'])
            
        return ' '.join(features)
    
    def train(self, movie_data: List[Dict[str, Any]]):
        """Train the recommendation model"""
        try:
            logger.info("Training movie recommendation model...")
            
            # Convert to DataFrame
            self.movies_df = pd.DataFrame(movie_data)
            
            # Create content features for each movie
            self.movies_df['content_features'] = self.movies_df.apply(
                lambda row: self.create_content_features(row.to_dict()), axis=1
            )
            
            # Clean content features
            self.movies_df['content_features'] = self.movies_df['content_features'].apply(
                self.preprocess_text
            )
            
            # Create TF-IDF matrix
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(
                self.movies_df['content_features']
            )
            
            # Train KNN model for similarity
            self.knn_model.fit(tfidf_matrix)
            
            # Prepare data for rating prediction
            self._train_rating_predictor()
            
            self.is_model_trained = True
            logger.info("Model training completed successfully!")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def _train_rating_predictor(self):
        """Train rating prediction model"""
        try:
            # Create features for rating prediction
            feature_data = []
            
            for _, movie in self.movies_df.iterrows():
                features = self._extract_movie_features(movie.to_dict())
                feature_data.append(features)
            
            X = np.array(feature_data)
            y = self.movies_df['rating'].values
            
            # Remove any NaN values
            mask = ~np.isnan(y)
            X = X[mask]
            y = y[mask]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train rating predictor
            self.rating_predictor.fit(X_scaled, y)
            
            logger.info("Rating predictor trained successfully")
            
        except Exception as e:
            logger.error(f"Error training rating predictor: {e}")
    
    def _extract_movie_features(self, movie: Dict) -> List[float]:
        """Extract numerical features from movie data"""
        features = []
        
        # Year (normalized)
        year = movie.get('year', 2000)
        features.append((year - 1900) / 100.0)
        
        # Duration (extract minutes)
        duration_str = movie.get('duration', '120 min')
        duration = self._extract_duration_minutes(duration_str)
        features.append(duration / 300.0)  # Normalize by 5 hours
        
        # Genre encoding (one-hot style)
        genres = movie.get('genre', '').split(', ')
        common_genres = ['Action', 'Comedy', 'Drama', 'Romance', 'Thriller', 'Horror', 'Sci-Fi']
        for genre in common_genres:
            features.append(1.0 if genre in genres else 0.0)
        
        return features
    
    def _extract_duration_minutes(self, duration_str: str) -> int:
        """Extract minutes from duration string"""
        if not duration_str:
            return 120
        
        # Look for number followed by 'min' or 'minutes'
        match = re.search(r'(\d+)', str(duration_str))
        if match:
            return int(match.group(1))
        return 120
    
    def predict(self, preferences: 'UserPreferences') -> List[Dict[str, Any]]:
        """Generate movie recommendations based on user preferences"""
        if not self.is_model_trained:
            raise ValueError("Model not trained yet")
        
        try:
            # Create preference vector
            preference_text = self._create_preference_text(preferences)
            preference_vector = self.tfidf_vectorizer.transform([preference_text])
            
            # Find similar movies
            distances, indices = self.knn_model.kneighbors(
                preference_vector, n_neighbors=min(20, len(self.movies_df))
            )
            
            # Get candidate movies
            candidate_movies = []
            for i, idx in enumerate(indices[0]):
                movie = self.movies_df.iloc[idx].to_dict()
                
                # Calculate confidence score
                similarity_score = 1 - distances[0][i]
                preference_match = self._calculate_preference_match(movie, preferences)
                confidence_score = (similarity_score * 0.6 + preference_match * 0.4)
                
                movie['confidence_score'] = confidence_score
                candidate_movies.append(movie)
            
            # Filter and rank movies
            filtered_movies = self._filter_by_preferences(candidate_movies, preferences)
            ranked_movies = sorted(filtered_movies, key=lambda x: x['confidence_score'], reverse=True)
            
            # Return top recommendations
            return ranked_movies[:10]
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return []
    
    def _create_preference_text(self, preferences: 'UserPreferences') -> str:
        """Create text representation of user preferences"""
        text_parts = []
        
        # Add genres
        text_parts.extend(preferences.genres)
        
        # Add mood-related keywords
        mood_keywords = {
            'Excited & Energetic': ['action', 'adventure', 'fast-paced', 'thrilling'],
            'Relaxed & Chill': ['comedy', 'romantic', 'feel-good', 'light'],
            'Thoughtful & Deep': ['drama', 'philosophical', 'meaningful', 'complex'],
            'Romantic & Emotional': ['romance', 'emotional', 'love', 'heartwarming'],
            'Adventurous & Bold': ['adventure', 'epic', 'journey', 'exploration'],
            'Nostalgic & Warm': ['family', 'nostalgic', 'classic', 'heartwarming']
        }
        
        if preferences.mood in mood_keywords:
            text_parts.extend(mood_keywords[preferences.mood])
        
        # Add keywords if provided
        if preferences.keywords:
            text_parts.append(preferences.keywords)
        
        # Add actors and directors
        if preferences.actors:
            text_parts.append(preferences.actors)
        if preferences.directors:
            text_parts.append(preferences.directors)
        
        return ' '.join(text_parts)
    
    def _calculate_preference_match(self, movie: Dict, preferences: 'UserPreferences') -> float:
        """Calculate how well a movie matches user preferences"""
        score = 0.0
        total_factors = 0
        
        # Genre matching
        movie_genres = movie.get('genre', '').split(', ')
        genre_match = len(set(preferences.genres) & set(movie_genres)) / len(preferences.genres)
        score += genre_match * 0.4
        total_factors += 0.4
        
        # Language matching
        if preferences.language and preferences.language != "Any Language":
            # This would need language data in the movie dataset
            pass
        
        # Decade matching
        if preferences.decade and preferences.decade != "No Preference":
            movie_year = movie.get('year', 0)
            decade_match = self._check_decade_match(movie_year, preferences.decade)
            score += decade_match * 0.2
            total_factors += 0.2
        
        # Duration matching
        if preferences.duration and preferences.duration != "No Preference":
            movie_duration = self._extract_duration_minutes(movie.get('duration', ''))
            duration_match = self._check_duration_match(movie_duration, preferences.duration)
            score += duration_match * 0.1
            total_factors += 0.1
        
        # Rating matching
        if preferences.rating and preferences.rating != "No Preference":
            # This would need MPAA rating data
            pass
        
        # Actor/Director matching
        if preferences.actors or preferences.directors:
            text_match = self._check_text_match(movie, preferences)
            score += text_match * 0.3
            total_factors += 0.3
        
        return score / max(total_factors, 1.0) if total_factors > 0 else 0.5
    
    def _check_decade_match(self, year: int, decade_pref: str) -> float:
        """Check if movie year matches decade preference"""
        decade_ranges = {
            '2020s': (2020, 2029),
            '2010s': (2010, 2019),
            '2000s': (2000, 2009),
            '1990s': (1990, 1999),
            '1980s': (1980, 1989),
            '1970s': (1970, 1979),
            'Classic (Before 1970)': (1900, 1969)
        }
        
        if decade_pref in decade_ranges:
            start, end = decade_ranges[decade_pref]
            return 1.0 if start <= year <= end else 0.0
        
        return 0.5
    
    def _check_duration_match(self, duration_minutes: int, duration_pref: str) -> float:
        """Check if movie duration matches preference"""
        duration_ranges = {
            'Short (< 90 min)': (0, 89),
            'Medium (90-120 min)': (90, 120),
            'Long (120-180 min)': (121, 180),
            'Epic (> 180 min)': (181, 999)
        }
        
        if duration_pref in duration_ranges:
            start, end = duration_ranges[duration_pref]
            return 1.0 if start <= duration_minutes <= end else 0.0
        
        return 0.5
    
    def _check_text_match(self, movie: Dict, preferences: 'UserPreferences') -> float:
        """Check text matching for actors/directors"""
        movie_text = ' '.join([
            movie.get('actors', ''),
            movie.get('director', ''),
            movie.get('description', '')
        ]).lower()
        
        match_score = 0.0
        total_checks = 0
        
        if preferences.actors:
            actors = [actor.strip().lower() for actor in preferences.actors.split(',')]
            for actor in actors:
                if actor in movie_text:
                    match_score += 1.0
                total_checks += 1
        
        if preferences.directors:
            directors = [director.strip().lower() for director in preferences.directors.split(',')]
            for director in directors:
                if director in movie_text:
                    match_score += 1.0
                total_checks += 1
        
        return match_score / max(total_checks, 1) if total_checks > 0 else 0.0
    
    def _filter_by_preferences(self, movies: List[Dict], preferences: 'UserPreferences') -> List[Dict]:
        """Apply hard filters based on preferences"""
        filtered = []
        
        for movie in movies:
            # Apply minimum confidence threshold
            if movie.get('confidence_score', 0) < 0.1:
                continue
            
            # Apply rating filter if specified
            if preferences.rating and preferences.rating != "No Preference":
                # Add rating filtering logic here
                pass
            
            filtered.append(movie)
        
        return filtered
    
    def is_trained(self) -> bool:
        """Check if model is trained"""
        return self.is_model_trained
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if not self.is_model_trained:
            raise ValueError("Model not trained yet")
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'knn_model': self.knn_model,
            'rating_predictor': self.rating_predictor,
            'scaler': self.scaler,
            'movies_df': self.movies_df,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        model_data = joblib.load(filepath)
        
        self.tfidf_vectorizer = model_data['tfidf_vectorizer']
        self.knn_model = model_data['knn_model']
        self.rating_predictor = model_data['rating_predictor']
        self.scaler = model_data['scaler']
        self.movies_df = model_data['movies_df']
        self.feature_names = model_data['feature_names']
        
        self.is_model_trained = True
        logger.info(f"Model loaded from {filepath}")