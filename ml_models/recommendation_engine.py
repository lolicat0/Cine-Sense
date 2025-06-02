import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import pickle
from collections import defaultdict
import math

# Scikit-learn imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentBasedRecommender:
    """
    Content-based recommendation engine using movie features
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.config['tfidf_max_features'],
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        self.scaler = StandardScaler()
        self.knn_model = NearestNeighbors(
            n_neighbors=self.config['n_neighbors'],
            metric='cosine',
            algorithm='brute'
        )
        
        # Data storage
        self.movies_df = None
        self.content_matrix = None
        self.feature_matrix = None
        self.similarity_matrix = None
        self.movie_embeddings = None
        
        # Training state
        self.is_fitted = False
        self.feature_names = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'tfidf_max_features': 5000,
            'n_neighbors': 50,
            'similarity_threshold': 0.1,
            'content_weight': 0.7,
            'metadata_weight': 0.3,
            'diversity_factor': 0.1,
            'recency_boost': 0.1,
            'popularity_boost': 0.05
        }
    
    def fit(self, movies_df: pd.DataFrame) -> 'ContentBasedRecommender':
        """Train the content-based recommender"""
        logger.info("Training content-based recommender...")
        
        self.movies_df = movies_df.copy()
        
        # Create content features
        self._create_content_features()
        
        # Create metadata features
        self._create_metadata_features()
        
        # Combine features
        self._create_combined_features()
        
        # Train similarity model
        self._train_similarity_model()
        
        self.is_fitted = True
        logger.info("Content-based recommender training completed")
        
        return self
    
    def _create_content_features(self):
        """Create TF-IDF features from text content"""
        logger.info("Creating content features...")
        
        # Combine text fields
        text_fields = ['description', 'genre', 'actors', 'director']
        combined_text = []
        
        for _, movie in self.movies_df.iterrows():
            text_parts = []
            for field in text_fields:
                if field in movie and pd.notna(movie[field]):
                    text_parts.append(str(movie[field]))
            
            # Add tags if available
            if 'tags' in movie and isinstance(movie['tags'], list):
                text_parts.extend(movie['tags'])
            elif 'tags_string' in movie and pd.notna(movie['tags_string']):
                text_parts.append(str(movie['tags_string']))
            
            combined_text.append(' '.join(text_parts))
        
        # Create TF-IDF matrix
        self.content_matrix = self.tfidf_vectorizer.fit_transform(combined_text)
        logger.info(f"Created content matrix: {self.content_matrix.shape}")
    
    def _create_metadata_features(self):
        """Create features from movie metadata"""
        logger.info("Creating metadata features...")
        
        features = []
        feature_names = []
        
        # Numerical features
        numerical_cols = ['rating', 'year', 'duration_minutes']
        for col in numerical_cols:
            if col in self.movies_df.columns:
                values = self.movies_df[col].fillna(self.movies_df[col].median())
                features.append(values.values.reshape(-1, 1))
                feature_names.append(col)
        
        # Categorical features (one-hot encoded)
        categorical_cols = ['language', 'mpaa_rating']
        for col in categorical_cols:
            if col in self.movies_df.columns:
                dummies = pd.get_dummies(self.movies_df[col], prefix=col)
                features.append(dummies.values)
                feature_names.extend(dummies.columns.tolist())
        
        # Genre binary features
        if 'genre' in self.movies_df.columns:
            major_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller']
            genre_features = []
            
            for genre in major_genres:
                genre_col = self.movies_df['genre'].str.contains(genre, case=False, na=False).astype(int)
                genre_features.append(genre_col.values.reshape(-1, 1))
                feature_names.append(f'genre_{genre.lower()}')
            
            if genre_features:
                features.extend(genre_features)
        
        # Combine all features
        if features:
            self.feature_matrix = np.hstack(features)
            self.feature_names = feature_names
            
            # Scale features
            self.feature_matrix = self.scaler.fit_transform(self.feature_matrix)
            
            logger.info(f"Created metadata matrix: {self.feature_matrix.shape}")
        else:
            logger.warning("No metadata features created")
    
    def _create_combined_features(self):
        """Combine content and metadata features"""
        logger.info("Combining features...")
        
        # Convert content matrix to dense for combination
        content_dense = self.content_matrix.toarray()
        
        if self.feature_matrix is not None:
            # Combine content and metadata features
            self.movie_embeddings = np.hstack([
                content_dense * self.config['content_weight'],
                self.feature_matrix * self.config['metadata_weight']
            ])
        else:
            self.movie_embeddings = content_dense
        
        logger.info(f"Combined embeddings shape: {self.movie_embeddings.shape}")
    
    def _train_similarity_model(self):
        """Train KNN model for similarity search"""
        logger.info("Training similarity model...")
        
        self.knn_model.fit(self.movie_embeddings)
        
        # Pre-compute similarity matrix for faster lookups
        if len(self.movies_df) <= 1000:  # Only for smaller datasets
            self.similarity_matrix = cosine_similarity(self.movie_embeddings)
            logger.info("Pre-computed similarity matrix")
    
    def recommend(self, user_preferences: Dict[str, Any], n_recommendations: int = 10,
                 exclude_movies: List[str] = None) -> List[Dict[str, Any]]:
        """Generate content-based recommendations"""
        if not self.is_fitted:
            raise ValueError("Recommender not fitted. Call fit() first.")
        
        logger.info(f"Generating {n_recommendations} content-based recommendations...")
        
        # Create user preference vector
        user_vector = self._create_user_vector(user_preferences)
        
        # Find similar movies
        if user_vector is not None:
            # Use user preferences for similarity
            distances, indices = self.knn_model.kneighbors(
                user_vector.reshape(1, -1), 
                n_neighbors=min(n_recommendations * 3, len(self.movies_df))
            )
            
            candidate_indices = indices[0]
            candidate_distances = distances[0]
        else:
            # Fallback: use popularity and rating
            candidate_indices = self._get_popular_movies(n_recommendations * 3)
            candidate_distances = np.zeros(len(candidate_indices))
        
        # Filter and rank candidates
        recommendations = self._rank_candidates(
            candidate_indices, candidate_distances, user_preferences, 
            n_recommendations, exclude_movies
        )
        
        return recommendations
    
    def _create_user_vector(self, preferences: Dict[str, Any]) -> Optional[np.ndarray]:
        """Create user preference vector"""
        try:
            # Create text from user preferences
            text_parts = []
            
            # Add genres
            if 'genres' in preferences and preferences['genres']:
                text_parts.extend(preferences['genres'])
            
            # Add mood keywords
            if 'mood' in preferences:
                mood_keywords = self._get_mood_keywords(preferences['mood'])
                text_parts.extend(mood_keywords)
            
            # Add other text preferences
            for field in ['actors', 'directors', 'keywords']:
                if field in preferences and preferences[field]:
                    text_parts.append(str(preferences[field]))
            
            if not text_parts:
                return None
            
            # Create TF-IDF vector
            combined_text = ' '.join(text_parts)
            content_vector = self.tfidf_vectorizer.transform([combined_text]).toarray()[0]
            
            # Create metadata vector
            metadata_vector = self._create_metadata_vector(preferences)
            
            # Combine vectors
            if metadata_vector is not None:
                user_vector = np.hstack([
                    content_vector * self.config['content_weight'],
                    metadata_vector * self.config['metadata_weight']
                ])
            else:
                user_vector = content_vector
            
            return user_vector
            
        except Exception as e:
            logger.error(f"Error creating user vector: {e}")
            return None
    
    def _get_mood_keywords(self, mood: str) -> List[str]:
        """Get keywords associated with mood"""
        mood_mappings = {
            'Excited & Energetic': ['action', 'adventure', 'fast-paced', 'thrilling', 'intense'],
            'Relaxed & Chill': ['comedy', 'romantic', 'feel-good', 'light', 'fun'],
            'Thoughtful & Deep': ['drama', 'philosophical', 'meaningful', 'complex', 'serious'],
            'Romantic & Emotional': ['romance', 'emotional', 'love', 'heartwarming', 'touching'],
            'Adventurous & Bold': ['adventure', 'epic', 'journey', 'exploration', 'heroic'],
            'Nostalgic & Warm': ['family', 'nostalgic', 'classic', 'heartwarming', 'traditional']
        }
        
        return mood_mappings.get(mood, [])
    
    def _create_metadata_vector(self, preferences: Dict[str, Any]) -> Optional[np.ndarray]:
        """Create metadata vector from preferences"""
        if self.feature_matrix is None:
            return None
        
        try:
            # Initialize vector
            vector = np.zeros(self.feature_matrix.shape[1])
            
            # Set preferences
            idx = 0
            
            # Numerical features
            for col in ['rating', 'year', 'duration_minutes']:
                if col in self.feature_names:
                    # Set target values based on preferences
                    if col == 'rating':
                        vector[idx] = 0.8  # Prefer higher ratings
                    elif col == 'year':
                        # Decode decade preference
                        if 'decade' in preferences:
                            target_year = self._decode_decade(preferences['decade'])
                            if target_year:
                                # Normalize year
                                normalized_year = (target_year - 1900) / 130
                                vector[idx] = normalized_year
                    elif col == 'duration_minutes':
                        # Decode duration preference
                        if 'duration' in preferences:
                            target_duration = self._decode_duration(preferences['duration'])
                            if target_duration:
                                # Normalize duration
                                normalized_duration = target_duration / 300
                                vector[idx] = normalized_duration
                    idx += 1
            
            # Categorical features would be handled here
            # For simplicity, we'll skip them in this implementation
            
            return vector
            
        except Exception as e:
            logger.error(f"Error creating metadata vector: {e}")
            return None
    
    def _decode_decade(self, decade_pref: str) -> Optional[int]:
        """Decode decade preference to target year"""
        decade_mapping = {
            '2020s': 2025,
            '2010s': 2015,
            '2000s': 2005,
            '1990s': 1995,
            '1980s': 1985,
            '1970s': 1975,
            'Classic (Before 1970)': 1960
        }
        return decade_mapping.get(decade_pref)
    
    def _decode_duration(self, duration_pref: str) -> Optional[int]:
        """Decode duration preference to target minutes"""
        duration_mapping = {
            'Short (< 90 min)': 80,
            'Medium (90-120 min)': 105,
            'Long (120-180 min)': 150,
            'Epic (> 180 min)': 200
        }
        return duration_mapping.get(duration_pref)
    
    def _get_popular_movies(self, n_movies: int) -> np.ndarray:
        """Get indices of popular movies as fallback"""
        if 'rating' in self.movies_df.columns and 'year' in self.movies_df.columns:
            # Sort by rating and recency
            scores = (
                self.movies_df['rating'] * 0.7 + 
                (self.movies_df['year'] - self.movies_df['year'].min()) / 
                (self.movies_df['year'].max() - self.movies_df['year'].min()) * 0.3
            )
            indices = scores.nlargest(n_movies).index.values
        else:
            # Random selection as last resort
            indices = np.random.choice(len(self.movies_df), size=min(n_movies, len(self.movies_df)), replace=False)
        
        return indices
    
    def _rank_candidates(self, candidate_indices: np.ndarray, distances: np.ndarray,
                        user_preferences: Dict[str, Any], n_recommendations: int,
                        exclude_movies: List[str] = None) -> List[Dict[str, Any]]:
        """Rank and filter candidate recommendations"""
        recommendations = []
        exclude_movies = exclude_movies or []
        
        for i, (idx, distance) in enumerate(zip(candidate_indices, distances)):
            movie = self.movies_df.iloc[idx]
            
            # Skip excluded movies
            if movie.get('title') in exclude_movies:
                continue
            
            # Calculate recommendation score
            similarity_score = 1 - distance if distance > 0 else 1.0
            preference_score = self._calculate_preference_match(movie, user_preferences)
            popularity_score = self._calculate_popularity_score(movie)
            diversity_penalty = self._calculate_diversity_penalty(movie, recommendations)
            
            # Combined score
            final_score = (
                similarity_score * 0.5 +
                preference_score * 0.3 +
                popularity_score * 0.1 +
                diversity_penalty * 0.1
            )
            
            recommendation = {
                'title': movie.get('title', 'Unknown'),
                'genre': movie.get('genre', ''),
                'description': movie.get('description', ''),
                'rating': float(movie.get('rating', 0)),
                'year': int(movie.get('year', 0)),
                'duration': movie.get('duration', ''),
                'director': movie.get('director', ''),
                'actors': movie.get('actors', ''),
                'poster_url': movie.get('poster_url', ''),
                'confidence_score': float(final_score),
                'similarity_score': float(similarity_score),
                'preference_match': float(preference_score),
                'movie_index': int(idx),
                'recommendation_reason': self._generate_explanation(movie, user_preferences, similarity_score)
            }
            
            recommendations.append(recommendation)
            
            if len(recommendations) >= n_recommendations:
                break
        
        # Sort by final score
        recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return recommendations[:n_recommendations]
    
    def _calculate_preference_match(self, movie: pd.Series, preferences: Dict[str, Any]) -> float:
        """Calculate how well movie matches user preferences"""
        match_score = 0.0
        total_weight = 0.0
        
        # Genre matching
        if 'genres' in preferences and preferences['genres'] and 'genre' in movie:
            user_genres = set(preferences['genres'])
            movie_genres = set(str(movie['genre']).split(', '))
            
            overlap = len(user_genres.intersection(movie_genres))
            if len(user_genres) > 0:
                genre_match = overlap / len(user_genres)
                match_score += genre_match * 0.4
                total_weight += 0.4
        
        # Year/decade matching
        if 'decade' in preferences and 'year' in movie:
            decade_match = self._check_decade_match(movie['year'], preferences['decade'])
            match_score += decade_match * 0.2
            total_weight += 0.2
        
        # Duration matching
        if 'duration' in preferences and 'duration_minutes' in movie:
            duration_match = self._check_duration_match(movie['duration_minutes'], preferences['duration'])
            match_score += duration_match * 0.1
            total_weight += 0.1
        
        # Language matching
        if 'language' in preferences and preferences['language'] != 'Any Language' and 'language' in movie:
            language_match = 1.0 if movie['language'] == preferences['language'] else 0.0
            match_score += language_match * 0.1
            total_weight += 0.1
        
        # Actor/Director matching
        if ('actors' in preferences and preferences['actors']) or ('directors' in preferences and preferences['directors']):
            text_match = self._check_person_match(movie, preferences)
            match_score += text_match * 0.2
            total_weight += 0.2
        
        return match_score / max(total_weight, 1.0)
    
    def _check_decade_match(self, year: int, decade_pref: str) -> float:
        """Check decade matching"""
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
        
        return 0.5  # Neutral for "No Preference"
    
    def _check_duration_match(self, duration_minutes: float, duration_pref: str) -> float:
        """Check duration matching"""
        duration_ranges = {
            'Short (< 90 min)': (0, 89),
            'Medium (90-120 min)': (90, 120),
            'Long (120-180 min)': (121, 180),
            'Epic (> 180 min)': (181, 999)
        }
        
        if duration_pref in duration_ranges:
            start, end = duration_ranges[duration_pref]
            return 1.0 if start <= duration_minutes <= end else 0.0
        
        return 0.5  # Neutral for "No Preference"
    
    def _check_person_match(self, movie: pd.Series, preferences: Dict[str, Any]) -> float:
        """Check actor/director matching"""
        movie_text = ' '.join([
            str(movie.get('actors', '')),
            str(movie.get('director', ''))
        ]).lower()
        
        match_count = 0
        total_count = 0
        
        if 'actors' in preferences and preferences['actors']:
            actors = [actor.strip().lower() for actor in preferences['actors'].split(',')]
            for actor in actors:
                if actor and actor in movie_text:
                    match_count += 1
                total_count += 1
        
        if 'directors' in preferences and preferences['directors']:
            directors = [director.strip().lower() for director in preferences['directors'].split(',')]
            for director in directors:
                if director and director in movie_text:
                    match_count += 1
                total_count += 1
        
        return match_count / max(total_count, 1)
    
    def _calculate_popularity_score(self, movie: pd.Series) -> float:
        """Calculate popularity score"""
        score = 0.0
        
        # Rating contribution
        if 'rating' in movie and pd.notna(movie['rating']):
            # Normalize rating (assuming 0-10 scale)
            score += (movie['rating'] / 10.0) * 0.6
        
        # Recency contribution
        if 'year' in movie and pd.notna(movie['year']):
            current_year = datetime.now().year
            years_old = current_year - movie['year']
            recency_score = max(0, 1 - years_old / 50)  # Decay over 50 years
            score += recency_score * 0.4
        
        return min(score, 1.0)
    
    def _calculate_diversity_penalty(self, movie: pd.Series, existing_recs: List[Dict[str, Any]]) -> float:
        """Calculate diversity penalty to avoid too similar recommendations"""
        if not existing_recs:
            return 0.0
        
        # Check genre diversity
        movie_genres = set(str(movie.get('genre', '')).split(', '))
        
        genre_overlap = 0
        for rec in existing_recs:
            rec_genres = set(str(rec.get('genre', '')).split(', '))
            overlap = len(movie_genres.intersection(rec_genres))
            genre_overlap += overlap
        
        # Penalize if too much genre overlap
        diversity_penalty = -min(genre_overlap / len(existing_recs), 0.5)
        
        return diversity_penalty
    
    def _generate_explanation(self, movie: pd.Series, preferences: Dict[str, Any], 
                            similarity_score: float) -> str:
        """Generate explanation for recommendation"""
        reasons = []
        
        # Genre match
        if 'genres' in preferences and preferences['genres'] and 'genre' in movie:
            user_genres = set(preferences['genres'])
            movie_genres = set(str(movie['genre']).split(', '))
            common_genres = user_genres.intersection(movie_genres)
            
            if common_genres:
                reasons.append(f"matches your interest in {', '.join(list(common_genres)[:2])}")
        
        # High rating
        if 'rating' in movie and movie['rating'] >= 8.0:
            reasons.append(f"highly rated ({movie['rating']}/10)")
        
        # Mood match
        if 'mood' in preferences:
            mood_keywords = self._get_mood_keywords(preferences['mood'])
            movie_text = ' '.join([
                str(movie.get('description', '')),
                str(movie.get('genre', ''))
            ]).lower()
            
            matching_keywords = [kw for kw in mood_keywords if kw in movie_text]
            if matching_keywords:
                reasons.append(f"fits your {preferences['mood'].lower()} mood")
        
        # Era preference
        if 'decade' in preferences and preferences['decade'] != 'No Preference' and 'year' in movie:
            if self._check_decade_match(movie['year'], preferences['decade']) > 0.5:
                reasons.append(f"from your preferred era ({preferences['decade']})")
        
        # Actor/Director match
        if 'actors' in preferences and preferences['actors'] and 'actors' in movie:
            reasons.append("features actors you like")
        
        if not reasons:
            if similarity_score > 0.7:
                reasons.append("highly similar to your preferences")
            else:
                reasons.append("popular and well-regarded")
        
        return f"Recommended because it {', '.join(reasons[:3])}"


class CollaborativeRecommender:
    """
    Collaborative filtering recommendation engine
    (Simplified implementation for demonstration)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.user_item_matrix = None
        self.item_similarity_matrix = None
        self.svd_model = None
        self.is_fitted = False
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'n_components': 50,
            'min_interactions': 5,
            'similarity_threshold': 0.1
        }
    
    def fit(self, user_ratings: pd.DataFrame) -> 'CollaborativeRecommender':
        """
        Train collaborative filtering model
        
        Args:
            user_ratings: DataFrame with columns ['user_id', 'movie_id', 'rating']
        """
        logger.info("Training collaborative filtering model...")
        
        # Create user-item matrix
        self.user_item_matrix = user_ratings.pivot(
            index='user_id', 
            columns='movie_id', 
            values='rating'
        ).fillna(0)
        
        # Train SVD model for dimensionality reduction
        self.svd_model = TruncatedSVD(
            n_components=self.config['n_components'],
            random_state=42
        )
        
        # Fit SVD on user-item matrix
        user_features = self.svd_model.fit_transform(self.user_item_matrix)
        
        # Compute item-item similarity matrix
        item_features = self.svd_model.components_.T
        self.item_similarity_matrix = cosine_similarity(item_features)
        
        self.is_fitted = True
        logger.info("Collaborative filtering training completed")
        
        return self
    
    def recommend(self, user_id: str, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Generate collaborative filtering recommendations"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        # This is a simplified implementation
        # In practice, you would implement more sophisticated CF algorithms
        recommendations = []
        
        # For now, return empty list (placeholder)
        logger.info(f"Collaborative filtering recommendations for user {user_id}: {len(recommendations)}")
        
        return recommendations


class HybridRecommendationEngine:
    """
    Hybrid recommendation engine combining multiple approaches
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        
        # Initialize recommenders
        self.content_recommender = ContentBasedRecommender(
            self.config.get('content_based', {})
        )
        self.collaborative_recommender = CollaborativeRecommender(
            self.config.get('collaborative', {})
        )
        
        # Caching
        self.recommendation_cache = {}
        self.cache_ttl = timedelta(hours=self.config['cache_ttl_hours'])
        
        # Performance tracking
        self.recommendation_stats = defaultdict(int)
        
        # Training state
        self.is_fitted = False
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'content_weight': 0.8,
            'collaborative_weight': 0.2,
            'diversity_boost': 0.1,
            'popularity_boost': 0.05,
            'cache_ttl_hours': 24,
            'min_score_threshold': 0.1,
            'max_cache_size': 1000,
            'enable_explanations': True,
            'content_based': {
                'tfidf_max_features': 5000,
                'n_neighbors': 50
            },
            'collaborative': {
                'n_components': 50
            }
        }
    
    def fit(self, movies_df: pd.DataFrame, user_ratings: pd.DataFrame = None) -> 'HybridRecommendationEngine':
        """Train the hybrid recommendation system"""
        logger.info("Training hybrid recommendation engine...")
        
        # Train content-based recommender
        self.content_recommender.fit(movies_df)
        
        # Train collaborative recommender if ratings available
        if user_ratings is not None and len(user_ratings) > 0:
            try:
                self.collaborative_recommender.fit(user_ratings)
                logger.info("Collaborative filtering enabled")
            except Exception as e:
                logger.warning(f"Collaborative filtering training failed: {e}")
        else:
            logger.info("No user ratings provided - using content-based only")
        
        self.is_fitted = True
        logger.info("Hybrid recommendation engine training completed")
        
        return self
    
    def recommend(self, user_preferences: Dict[str, Any], user_id: str = None,
                 n_recommendations: int = 10, exclude_movies: List[str] = None,
                 use_cache: bool = True) -> List[Dict[str, Any]]:
        """Generate hybrid recommendations"""
        if not self.is_fitted:
            raise ValueError("Recommendation engine not fitted")
        
        # Check cache first
        cache_key = self._generate_cache_key(user_preferences, user_id, n_recommendations)
        
        if use_cache and cache_key in self.recommendation_cache:
            cached_result = self.recommendation_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < self.cache_ttl:
                logger.info("Returning cached recommendations")
                self.recommendation_stats['cache_hits'] += 1
                return cached_result['recommendations']
        
        logger.info(f"Generating {n_recommendations} hybrid recommendations...")
        start_time = datetime.now()
        # Get content-based recommendations
        content_recs = self.content_recommender.recommend(
            user_preferences, 
            n_recommendations=n_recommendations * 2,  # Get more candidates
            exclude_movies=exclude_movies
        )
        
        # Get collaborative recommendations if available
        collaborative_recs = []
        if user_id and self.collaborative_recommender.is_fitted:
            try:
                collaborative_recs = self.collaborative_recommender.recommend(
                    user_id, 
                    n_recommendations=n_recommendations
                )
            except Exception as e:
                logger.warning(f"Collaborative filtering failed: {e}")
        
        # Combine recommendations
        hybrid_recs = self._combine_recommendations(
            content_recs, collaborative_recs, user_preferences, n_recommendations
        )
        
        # Apply post-processing
        final_recs = self._post_process_recommendations(hybrid_recs, user_preferences)
        
        # Cache results
        if use_cache:
            self._cache_recommendations(cache_key, final_recs)
        
        # Update stats
        processing_time = (datetime.now() - start_time).total_seconds()
        self.recommendation_stats['total_requests'] += 1
        self.recommendation_stats['avg_processing_time'] = (
            (self.recommendation_stats.get('avg_processing_time', 0) * 
             (self.recommendation_stats['total_requests'] - 1) + processing_time) / 
            self.recommendation_stats['total_requests']
        )
        
        logger.info(f"Generated {len(final_recs)} recommendations in {processing_time:.2f}s")
        
        return final_recs
    
    def _combine_recommendations(self, content_recs: List[Dict[str, Any]], 
                               collaborative_recs: List[Dict[str, Any]],
                               user_preferences: Dict[str, Any],
                               n_recommendations: int) -> List[Dict[str, Any]]:
        """Combine content-based and collaborative recommendations"""
        
        # Create movie score dictionary
        movie_scores = {}
        
        # Add content-based scores
        for i, rec in enumerate(content_recs):
            title = rec['title']
            content_score = rec['confidence_score']
            
            # Position-based decay
            position_weight = 1.0 - (i / len(content_recs)) * 0.3
            
            movie_scores[title] = {
                'recommendation': rec,
                'content_score': content_score * position_weight,
                'collaborative_score': 0.0,
                'sources': ['content']
            }
        
        # Add collaborative scores
        for i, rec in enumerate(collaborative_recs):
            title = rec['title']
            collab_score = rec.get('confidence_score', 0.5)
            
            position_weight = 1.0 - (i / len(collaborative_recs)) * 0.3
            
            if title in movie_scores:
                movie_scores[title]['collaborative_score'] = collab_score * position_weight
                movie_scores[title]['sources'].append('collaborative')
            else:
                # Add new movie from collaborative filtering
                movie_scores[title] = {
                    'recommendation': rec,
                    'content_score': 0.0,
                    'collaborative_score': collab_score * position_weight,
                    'sources': ['collaborative']
                }
        
        # Calculate hybrid scores
        hybrid_recommendations = []
        
        for title, scores in movie_scores.items():
            # Weighted combination
            hybrid_score = (
                scores['content_score'] * self.config['content_weight'] +
                scores['collaborative_score'] * self.config['collaborative_weight']
            )
            
            # Boost for movies found by multiple methods
            if len(scores['sources']) > 1:
                hybrid_score *= 1.1
            
            # Apply diversity and popularity boosts
            rec = scores['recommendation'].copy()
            rec['hybrid_score'] = hybrid_score
            rec['recommendation_sources'] = scores['sources']
            
            hybrid_recommendations.append(rec)
        
        # Sort by hybrid score
        hybrid_recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return hybrid_recommendations[:n_recommendations]
    
    def _post_process_recommendations(self, recommendations: List[Dict[str, Any]], 
                                    user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply post-processing to improve recommendation quality"""
        
        if not recommendations:
            return recommendations
        
        # Apply diversity filtering
        diverse_recs = self._apply_diversity_filter(recommendations)
        
        # Enhance with additional metadata
        enhanced_recs = self._enhance_recommendations(diverse_recs, user_preferences)
        
        # Filter by minimum score threshold
        filtered_recs = [
            rec for rec in enhanced_recs 
            if rec.get('hybrid_score', rec.get('confidence_score', 0)) >= self.config['min_score_threshold']
        ]
        
        return filtered_recs
    
    def _apply_diversity_filter(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity filtering to avoid too similar recommendations"""
        
        if len(recommendations) <= 3:
            return recommendations
        
        diverse_recs = [recommendations[0]]  # Always include top recommendation
        
        for rec in recommendations[1:]:
            # Check diversity against already selected recommendations
            is_diverse = True
            
            for selected_rec in diverse_recs:
                # Genre similarity check
                rec_genres = set(str(rec.get('genre', '')).split(', '))
                selected_genres = set(str(selected_rec.get('genre', '')).split(', '))
                
                genre_overlap = len(rec_genres.intersection(selected_genres))
                total_genres = len(rec_genres.union(selected_genres))
                
                if total_genres > 0 and genre_overlap / total_genres > 0.8:
                    # Check if they're from the same decade
                    if abs(rec.get('year', 0) - selected_rec.get('year', 0)) < 5:
                        is_diverse = False
                        break
            
            if is_diverse:
                diverse_recs.append(rec)
            
            # Stop if we have enough diverse recommendations
            if len(diverse_recs) >= len(recommendations):
                break
        
        return diverse_recs
    
    def _enhance_recommendations(self, recommendations: List[Dict[str, Any]], 
                               user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance recommendations with additional metadata and explanations"""
        
        enhanced_recs = []
        
        for i, rec in enumerate(recommendations):
            enhanced_rec = rec.copy()
            
            # Add ranking information
            enhanced_rec['rank'] = i + 1
            enhanced_rec['recommendation_id'] = self._generate_recommendation_id(rec)
            
            # Enhance explanation if enabled
            if self.config['enable_explanations']:
                enhanced_rec['explanation'] = self._generate_enhanced_explanation(rec, user_preferences)
            
            # Add confidence level
            score = rec.get('hybrid_score', rec.get('confidence_score', 0))
            enhanced_rec['confidence_level'] = self._get_confidence_level(score)
            
            # Add tags for better presentation
            enhanced_rec['tags'] = self._generate_presentation_tags(rec)
            
            enhanced_recs.append(enhanced_rec)
        
        return enhanced_recs
    
    def _generate_enhanced_explanation(self, rec: Dict[str, Any], 
                                     user_preferences: Dict[str, Any]) -> str:
        """Generate enhanced explanation for recommendation"""
        
        explanations = []
        
        # Source-based explanation
        sources = rec.get('recommendation_sources', ['content'])
        if 'collaborative' in sources and 'content' in sources:
            explanations.append("recommended by both content analysis and user behavior patterns")
        elif 'collaborative' in sources:
            explanations.append("recommended based on similar users' preferences")
        else:
            # Use existing content-based explanation
            existing_explanation = rec.get('recommendation_reason', '')
            if existing_explanation:
                explanations.append(existing_explanation.replace('Recommended because it ', ''))
        
        # Add confidence-based explanation
        score = rec.get('hybrid_score', rec.get('confidence_score', 0))
        if score > 0.8:
            explanations.append("highly confident match")
        elif score > 0.6:
            explanations.append("good match")
        
        # Add quality indicators
        if rec.get('rating', 0) >= 8.0:
            explanations.append(f"critically acclaimed ({rec['rating']}/10)")
        
        # Add recency if relevant
        current_year = datetime.now().year
        if rec.get('year', 0) >= current_year - 3:
            explanations.append("recent release")
        
        if explanations:
            return f"Recommended because it {', '.join(explanations[:3])}."
        else:
            return "Recommended based on your preferences."
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= 0.8:
            return "Very High"
        elif score >= 0.6:
            return "High"
        elif score >= 0.4:
            return "Medium"
        elif score >= 0.2:
            return "Low"
        else:
            return "Very Low"
    
    def _generate_presentation_tags(self, rec: Dict[str, Any]) -> List[str]:
        """Generate tags for better presentation"""
        tags = []
        
        # Rating-based tags
        rating = rec.get('rating', 0)
        if rating >= 9.0:
            tags.append("Masterpiece")
        elif rating >= 8.5:
            tags.append("Excellent")
        elif rating >= 8.0:
            tags.append("Great")
        
        # Year-based tags
        current_year = datetime.now().year
        year = rec.get('year', 0)
        
        if year >= current_year - 2:
            tags.append("New Release")
        elif year >= current_year - 5:
            tags.append("Recent")
        elif year <= 1980:
            tags.append("Classic")
        
        # Genre-based tags
        genre = rec.get('genre', '')
        if 'Action' in genre:
            tags.append("Action-Packed")
        if 'Comedy' in genre:
            tags.append("Feel-Good")
        if 'Drama' in genre and rating >= 8.0:
            tags.append("Powerful Drama")
        
        # Confidence-based tags
        score = rec.get('hybrid_score', rec.get('confidence_score', 0))
        if score >= 0.9:
            tags.append("Perfect Match")
        elif score >= 0.8:
            tags.append("Great Match")
        
        return tags[:3]  # Limit to 3 tags
    
    def _generate_cache_key(self, user_preferences: Dict[str, Any], 
                          user_id: str = None, n_recommendations: int = 10) -> str:
        """Generate cache key for recommendations"""
        
        # Create a string representation of preferences
        pref_str = json.dumps(user_preferences, sort_keys=True)
        
        # Include user_id if available
        if user_id:
            pref_str += f"_user_{user_id}"
        
        # Include number of recommendations
        pref_str += f"_n_{n_recommendations}"
        
        # Generate hash
        return hashlib.md5(pref_str.encode()).hexdigest()
    
    def _cache_recommendations(self, cache_key: str, recommendations: List[Dict[str, Any]]):
        """Cache recommendations with timestamp"""
        
        # Clear old cache entries if cache is full
        if len(self.recommendation_cache) >= self.config['max_cache_size']:
            # Remove oldest entries
            sorted_cache = sorted(
                self.recommendation_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            
            # Remove oldest 20% of entries
            remove_count = len(sorted_cache) // 5
            for old_key, _ in sorted_cache[:remove_count]:
                del self.recommendation_cache[old_key]
        
        # Add new cache entry
        self.recommendation_cache[cache_key] = {
            'recommendations': recommendations,
            'timestamp': datetime.now()
        }
    
    def _generate_recommendation_id(self, rec: Dict[str, Any]) -> str:
        """Generate unique ID for recommendation"""
        
        title = rec.get('title', 'unknown')
        year = rec.get('year', 0)
        
        # Create a simple hash-based ID
        id_str = f"{title}_{year}"
        return hashlib.md5(id_str.encode()).hexdigest()[:8]
    
    def get_similar_movies(self, movie_title: str, n_similar: int = 5) -> List[Dict[str, Any]]:
        """Get movies similar to a specific movie"""
        
        if not self.is_fitted:
            raise ValueError("Recommendation engine not fitted")
        
        # Find the movie in the dataset
        movies_df = self.content_recommender.movies_df
        movie_row = movies_df[movies_df['title'].str.contains(movie_title, case=False, na=False)]
        
        if movie_row.empty:
            logger.warning(f"Movie '{movie_title}' not found")
            return []
        
        movie = movie_row.iloc[0]
        
        # Create preferences based on the movie
        movie_preferences = {
            'genres': movie.get('genre', '').split(', '),
            'decade': self._year_to_decade(movie.get('year', 2000)),
            'mood': 'Excited & Energetic'  # Default mood
        }
        
        # Get recommendations
        similar_movies = self.content_recommender.recommend(
            movie_preferences,
            n_recommendations=n_similar + 1,  # +1 because original movie might be included
            exclude_movies=[movie_title]
        )
        
        return similar_movies[:n_similar]
    
    def _year_to_decade(self, year: int) -> str:
        """Convert year to decade string"""
        decade_map = {
            (2020, 2029): '2020s',
            (2010, 2019): '2010s',
            (2000, 2009): '2000s',
            (1990, 1999): '1990s',
            (1980, 1989): '1980s',
            (1970, 1979): '1970s'
        }
        
        for (start, end), decade in decade_map.items():
            if start <= year <= end:
                return decade
        
        return 'Classic (Before 1970)'
    
    def get_trending_movies(self, n_movies: int = 10) -> List[Dict[str, Any]]:
        """Get trending/popular movies"""
        
        if not self.is_fitted:
            raise ValueError("Recommendation engine not fitted")
        
        movies_df = self.content_recommender.movies_df
        
        # Calculate trending score based on rating and recency
        current_year = datetime.now().year
        
        trending_scores = []
        for _, movie in movies_df.iterrows():
            rating = movie.get('rating', 0)
            year = movie.get('year', 2000)
            
            # Recency boost (movies from last 5 years get boost)
            recency_boost = max(0, 1 - (current_year - year) / 20)
            
            # Quality boost
            quality_score = rating / 10.0
            
            # Combined trending score
            trending_score = quality_score * 0.7 + recency_boost * 0.3
            
            trending_scores.append({
                'movie': movie,
                'trending_score': trending_score
            })
        
        # Sort by trending score
        trending_scores.sort(key=lambda x: x['trending_score'], reverse=True)
        
        # Convert to recommendation format
        trending_movies = []
        for item in trending_scores[:n_movies]:
            movie = item['movie']
            rec = {
                'title': movie.get('title', 'Unknown'),
                'genre': movie.get('genre', ''),
                'description': movie.get('description', ''),
                'rating': float(movie.get('rating', 0)),
                'year': int(movie.get('year', 0)),
                'duration': movie.get('duration', ''),
                'director': movie.get('director', ''),
                'actors': movie.get('actors', ''),
                'poster_url': movie.get('poster_url', ''),
                'confidence_score': float(item['trending_score']),
                'explanation': f"Trending movie with {movie.get('rating', 0)}/10 rating",
                'tags': ['Trending', 'Popular']
            }
            trending_movies.append(rec)
        
        return trending_movies
    
    def get_recommendations_by_genre(self, genre: str, n_movies: int = 10) -> List[Dict[str, Any]]:
        """Get top movies by genre"""
        
        if not self.is_fitted:
            raise ValueError("Recommendation engine not fitted")
        
        # Create genre-specific preferences
        genre_preferences = {
            'genres': [genre],
            'mood': 'Excited & Energetic'  # Default
        }
        
        # Get recommendations
        genre_recs = self.content_recommender.recommend(
            genre_preferences,
            n_recommendations=n_movies
        )
        
        # Add genre-specific explanations
        for rec in genre_recs:
            rec['explanation'] = f"Top-rated {genre} movie with {rec['rating']}/10 rating"
            rec['tags'] = [genre, 'Top Rated']
        
        return genre_recs
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get recommendation engine statistics"""
        
        return {
            'total_requests': self.recommendation_stats['total_requests'],
            'cache_hits': self.recommendation_stats['cache_hits'],
            'cache_hit_rate': (
                self.recommendation_stats['cache_hits'] / 
                max(self.recommendation_stats['total_requests'], 1)
            ),
            'avg_processing_time': self.recommendation_stats.get('avg_processing_time', 0),
            'cache_size': len(self.recommendation_cache),
            'is_fitted': self.is_fitted,
            'content_recommender_fitted': self.content_recommender.is_fitted,
            'collaborative_recommender_fitted': self.collaborative_recommender.is_fitted
        }
    
    def clear_cache(self):
        """Clear recommendation cache"""
        self.recommendation_cache.clear()
        logger.info("Recommendation cache cleared")
    
    def save_model(self, model_path: str):
        """Save the trained recommendation engine"""
        
        model_path = Path(model_path)
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Save the entire engine
        engine_data = {
            'content_recommender': self.content_recommender,
            'collaborative_recommender': self.collaborative_recommender,
            'config': self.config,
            'is_fitted': self.is_fitted,
            'recommendation_stats': dict(self.recommendation_stats)
        }
        
        with open(model_path / 'recommendation_engine.pkl', 'wb') as f:
            pickle.dump(engine_data, f)
        
        logger.info(f"Recommendation engine saved to {model_path}")
    
    def load_model(self, model_path: str):
        """Load a trained recommendation engine"""
        
        model_path = Path(model_path)
        engine_file = model_path / 'recommendation_engine.pkl'
        
        if not engine_file.exists():
            raise FileNotFoundError(f"Engine file not found: {engine_file}")
        
        with open(engine_file, 'rb') as f:
            engine_data = pickle.load(f)
        
        self.content_recommender = engine_data['content_recommender']
        self.collaborative_recommender = engine_data['collaborative_recommender']
        self.config = engine_data['config']
        self.is_fitted = engine_data['is_fitted']
        self.recommendation_stats = defaultdict(int, engine_data['recommendation_stats'])
        
        logger.info(f"Recommendation engine loaded from {model_path}")


# Utility functions for external use
def create_recommendation_engine(movies_df: pd.DataFrame, 
                               user_ratings: pd.DataFrame = None,
                               config: Dict[str, Any] = None) -> HybridRecommendationEngine:
    """
    Create and train a recommendation engine
    
    Args:
        movies_df: DataFrame with movie information
        user_ratings: Optional DataFrame with user ratings
        config: Optional configuration dictionary
        
    Returns:
        Trained HybridRecommendationEngine
    """
    
    engine = HybridRecommendationEngine(config)
    engine.fit(movies_df, user_ratings)
    
    return engine


def generate_sample_user_ratings(movies_df: pd.DataFrame, 
                               n_users: int = 100,
                               n_ratings_per_user: int = 20) -> pd.DataFrame:
    """
    Generate sample user ratings for testing collaborative filtering
    
    Args:
        movies_df: DataFrame with movie information
        n_users: Number of users to generate
        n_ratings_per_user: Average ratings per user
        
    Returns:
        DataFrame with user ratings
    """
    
    np.random.seed(42)
    
    user_ratings = []
    movie_ids = movies_df.index.tolist()
    
    for user_id in range(n_users):
        # Random number of ratings for this user
        n_ratings = np.random.poisson(n_ratings_per_user)
        n_ratings = max(5, min(n_ratings, len(movie_ids)))  # Between 5 and total movies
        
        # Random movies for this user
        user_movies = np.random.choice(movie_ids, size=n_ratings, replace=False)
        
        for movie_id in user_movies:
            # Generate rating based on movie's actual rating with some noise
            actual_rating = movies_df.loc[movie_id, 'rating'] if 'rating' in movies_df.columns else 7.0
            
            # Add user preference bias and noise
            user_bias = np.random.normal(0, 1)  # User's general rating tendency
            noise = np.random.normal(0, 0.5)    # Random noise
            
            rating = actual_rating + user_bias + noise
            rating = max(1, min(10, rating))  # Clamp to 1-10 range
            
            user_ratings.append({
                'user_id': f'user_{user_id}',
                'movie_id': movie_id,
                'rating': round(rating, 1)
            })
    
    return pd.DataFrame(user_ratings)


if __name__ == "__main__":
    """Example usage and testing"""
    
    # Example: Load movie data and create recommendation engine
    try:
        # Load movie data (adjust path as needed)
        movies_df = pd.read_json('app/data/movies.json')
        if 'movies' in movies_df.columns:
            movies_df = pd.json_normalize(movies_df['movies'])
        
        logger.info(f"Loaded {len(movies_df)} movies")
        
        # Generate sample user ratings for collaborative filtering
        user_ratings = generate_sample_user_ratings(movies_df, n_users=50, n_ratings_per_user=15)
        logger.info(f"Generated {len(user_ratings)} user ratings")
        
        # Create and train recommendation engine
        config = {
            'content_weight': 0.8,
            'collaborative_weight': 0.2,
            'enable_explanations': True,
            'cache_ttl_hours': 24
        }
        
        engine = create_recommendation_engine(movies_df, user_ratings, config)
        
        # Test recommendations
        test_preferences = {
            'genres': ['Action', 'Sci-Fi'],
            'mood': 'Excited & Energetic',
            'decade': '2020s',
            'language': 'English'
        }
        
        recommendations = engine.recommend(test_preferences, n_recommendations=5)
        
        print(f"\nGenerated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['title']} ({rec['year']}) - {rec['rating']}/10")
            print(f"   {rec.get('explanation', 'No explanation')}")
            print(f"   Confidence: {rec.get('confidence_level', 'Unknown')}")
            print()
        
        # Test similar movies
        if len(movies_df) > 0:
            first_movie = movies_df.iloc[0]['title']
            similar = engine.get_similar_movies(first_movie, n_similar=3)
            
            print(f"\nMovies similar to '{first_movie}':")
            for rec in similar:
                print(f"- {rec['title']} ({rec['year']})")
        
        # Test trending movies
        trending = engine.get_trending_movies(n_movies=5)
        print(f"\nTrending movies:")
        for rec in trending:
            print(f"- {rec['title']} ({rec['year']}) - {rec['rating']}/10")
        
        # Get stats
        stats = engine.get_recommendation_stats()
        print(f"\nEngine Stats:")
        print(f"- Total requests: {stats['total_requests']}")
        print(f"- Cache hit rate: {stats['cache_hit_rate']:.2%}")
        print(f"- Avg processing time: {stats['avg_processing_time']:.3f}s")
        
        print("\nRecommendation engine test completed successfully!")
        
    except Exception as e:
        print(f"Error testing recommendation engine: {e}")
        logger.error(f"Test failed: {e}")