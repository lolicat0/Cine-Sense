import pandas as pd
import numpy as np
import json
import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import train_test_split
import unicodedata
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieDataPreprocessor:
    """
    Comprehensive data preprocessing for movie recommendation system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize preprocessor with configuration"""
        self.config = config or self._get_default_config()
        
        # Initialize preprocessors
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.genre_encoder = LabelEncoder()
        self.language_encoder = LabelEncoder()
        self.mpaa_encoder = LabelEncoder()
        
        # Text processors
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.config['tfidf_max_features'],
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        self.count_vectorizer = CountVectorizer(
            max_features=self.config['count_max_features'],
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 1)
        )
        
        # Data storage
        self.processed_data = {}
        self.feature_names = []
        self.genre_mapping = {}
        self.is_fitted = False
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default preprocessing configuration"""
        return {
            'tfidf_max_features': 5000,
            'count_max_features': 1000,
            'min_rating': 0.0,
            'max_rating': 10.0,
            'min_year': 1900,
            'max_year': 2030,
            'text_fields': ['description', 'tags', 'genre', 'actors', 'director'],
            'numerical_fields': ['rating', 'year', 'duration_minutes'],
            'categorical_fields': ['language', 'mpaa_rating', 'country'],
            'validation_rules': {
                'required_fields': ['title', 'genre', 'description', 'rating', 'year'],
                'max_title_length': 200,
                'max_description_length': 2000,
                'min_description_length': 10
            }
        }
    
    def load_and_preprocess(self, data_path: Union[str, Path, List[Dict]]) -> pd.DataFrame:
        """
        Load and preprocess movie data from file or list
        
        Args:
            data_path: Path to JSON file or list of movie dictionaries
            
        Returns:
            Preprocessed pandas DataFrame
        """
        try:
            # Load data
            if isinstance(data_path, (str, Path)):
                raw_data = self._load_from_file(data_path)
            elif isinstance(data_path, list):
                raw_data = data_path
            else:
                raise ValueError("data_path must be file path or list of dictionaries")
            
            logger.info(f"Loaded {len(raw_data)} movies for preprocessing")
            
            # Convert to DataFrame
            df = pd.DataFrame(raw_data)
            
            # Preprocessing pipeline
            df = self._validate_data(df)
            df = self._clean_data(df)
            df = self._extract_features(df)
            df = self._normalize_features(df)
            df = self._create_text_features(df)
            
            # Store processed data
            self.processed_data = df.to_dict('records')
            self.is_fitted = True
            
            logger.info(f"Successfully preprocessed {len(df)} movies")
            return df
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {e}")
            raise
    
    def _load_from_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, dict):
                if 'movies' in data:
                    return data['movies']
                elif 'data' in data:
                    return data['data']
                else:
                    # Assume the dict itself is the data
                    return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Invalid JSON structure")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate data quality and completeness"""
        logger.info("Validating data...")
        
        initial_count = len(df)
        rules = self.config['validation_rules']
        
        # Check required fields
        for field in rules['required_fields']:
            if field not in df.columns:
                raise ValueError(f"Required field missing: {field}")
            
            # Remove rows with missing required fields
            df = df[df[field].notna()]
        
        # Validate title length
        if 'title' in df.columns:
            df = df[df['title'].str.len() <= rules['max_title_length']]
        
        # Validate description
        if 'description' in df.columns:
            df = df[
                (df['description'].str.len() >= rules['min_description_length']) &
                (df['description'].str.len() <= rules['max_description_length'])
            ]
        
        # Validate ratings
        if 'rating' in df.columns:
            df = df[
                (df['rating'] >= self.config['min_rating']) &
                (df['rating'] <= self.config['max_rating'])
            ]
        
        # Validate years
        if 'year' in df.columns:
            df = df[
                (df['year'] >= self.config['min_year']) &
                (df['year'] <= self.config['max_year'])
            ]
        
        # Remove duplicates based on title and year
        df = df.drop_duplicates(subset=['title', 'year'], keep='first')
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} invalid records during validation")
        
        return df.reset_index(drop=True)
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data"""
        logger.info("Cleaning data...")
        
        df = df.copy()
        
        # Clean text fields
        text_fields = ['title', 'description', 'actors', 'director', 'genre']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].apply(self._clean_text)
        
        # Clean and standardize genres
        if 'genre' in df.columns:
            df['genre'] = df['genre'].apply(self._standardize_genres)
        
        # Clean duration and convert to minutes
        if 'duration' in df.columns:
            df['duration_minutes'] = df['duration'].apply(self._extract_duration_minutes)
        
        # Clean and standardize languages
        if 'language' in df.columns:
            df['language'] = df['language'].apply(self._standardize_language)
        
        # Clean and standardize countries
        if 'country' in df.columns:
            df['country'] = df['country'].apply(self._standardize_country)
        
        # Clean MPAA ratings
        if 'mpaa_rating' in df.columns:
            df['mpaa_rating'] = df['mpaa_rating'].apply(self._standardize_mpaa_rating)
        
        # Process tags
        if 'tags' in df.columns:
            df['tags_processed'] = df['tags'].apply(self._process_tags)
            df['tags_string'] = df['tags_processed'].apply(lambda x: ' '.join(x) if x else '')
        
        return df
    
    def _clean_text(self, text: Any) -> str:
        """Clean and normalize text"""
        if pd.isna(text) or text is None:
            return ""
        
        text = str(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        
        return text.strip()
    
    def _standardize_genres(self, genre_str: Any) -> str:
        """Standardize genre formatting"""
        if pd.isna(genre_str) or genre_str is None:
            return ""
        
        # Known genre mappings
        genre_mapping = {
            'sci-fi': 'Sci-Fi',
            'science fiction': 'Sci-Fi',
            'scifi': 'Sci-Fi',
            'superhero': 'Action',  # Could also be its own category
            'documentary': 'Documentary',
            'doc': 'Documentary',
            'anime': 'Animation',
            'cartoon': 'Animation',
            'musical': 'Music',
            'biography': 'Drama',
            'bio': 'Drama',
            'biopic': 'Drama'
        }
        
        genres = []
        for genre in str(genre_str).split(','):
            genre = genre.strip().lower()
            
            # Apply mappings
            if genre in genre_mapping:
                genre = genre_mapping[genre]
            else:
                # Capitalize first letter
                genre = genre.capitalize()
            
            if genre and genre not in genres:
                genres.append(genre)
        
        return ', '.join(genres)
    
    def _extract_duration_minutes(self, duration_str: Any) -> int:
        """Extract duration in minutes from various formats"""
        if pd.isna(duration_str) or duration_str is None:
            return 120  # Default duration
        
        duration_str = str(duration_str).lower()
        
        # Look for patterns like "120 min", "2h 30min", "1:45", etc.
        
        # Pattern: "XXX min"
        match = re.search(r'(\d+)\s*min', duration_str)
        if match:
            return int(match.group(1))
        
        # Pattern: "Xh Ymin" or "X hours Y minutes"
        hours_match = re.search(r'(\d+)\s*h', duration_str)
        mins_match = re.search(r'(\d+)\s*m', duration_str)
        
        if hours_match:
            hours = int(hours_match.group(1))
            minutes = int(mins_match.group(1)) if mins_match else 0
            return hours * 60 + minutes
        
        # Pattern: "X:YY" (hours:minutes)
        time_match = re.search(r'(\d+):(\d+)', duration_str)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            return hours * 60 + minutes
        
        # Just a number (assume minutes)
        number_match = re.search(r'(\d+)', duration_str)
        if number_match:
            num = int(number_match.group(1))
            # If number is too small, might be hours
            if num < 10:
                return num * 60
            return num
        
        return 120  # Default fallback
    
    def _standardize_language(self, language: Any) -> str:
        """Standardize language names"""
        if pd.isna(language) or language is None:
            return "English"
        
        language = str(language).strip().lower()
        
        language_mapping = {
            'en': 'English',
            'english': 'English',
            'eng': 'English',
            'es': 'Spanish',
            'spanish': 'Spanish',
            'esp': 'Spanish',
            'fr': 'French',
            'french': 'French',
            'fra': 'French',
            'de': 'German',
            'german': 'German',
            'deu': 'German',
            'it': 'Italian',
            'italian': 'Italian',
            'ita': 'Italian',
            'ja': 'Japanese',
            'japanese': 'Japanese',
            'jpn': 'Japanese',
            'ko': 'Korean',
            'korean': 'Korean',
            'kor': 'Korean',
            'zh': 'Mandarin',
            'chinese': 'Mandarin',
            'mandarin': 'Mandarin',
            'hi': 'Hindi',
            'hindi': 'Hindi',
            'any': 'Any Language',
            'multiple': 'Multiple Languages'
        }
        
        return language_mapping.get(language, language.capitalize())
    
    def _standardize_country(self, country: Any) -> str:
        """Standardize country names"""
        if pd.isna(country) or country is None:
            return "USA"
        
        country = str(country).strip().lower()
        
        country_mapping = {
            'us': 'USA',
            'usa': 'USA',
            'united states': 'USA',
            'america': 'USA',
            'uk': 'UK',
            'united kingdom': 'UK',
            'britain': 'UK',
            'great britain': 'UK',
            'england': 'UK',
            'france': 'France',
            'germany': 'Germany',
            'japan': 'Japan',
            'south korea': 'South Korea',
            'korea': 'South Korea',
            'china': 'China',
            'italy': 'Italy',
            'spain': 'Spain',
            'australia': 'Australia',
            'canada': 'Canada',
            'new zealand': 'New Zealand'
        }
        
        return country_mapping.get(country, country.title())
    
    def _standardize_mpaa_rating(self, rating: Any) -> str:
        """Standardize MPAA ratings"""
        if pd.isna(rating) or rating is None:
            return "Not Rated"
        
        rating = str(rating).strip().upper()
        
        rating_mapping = {
            'G': 'G',
            'PG': 'PG', 
            'PG-13': 'PG-13',
            'PG13': 'PG-13',
            'R': 'R',
            'NC-17': 'NC-17',
            'NC17': 'NC-17',
            'NR': 'Not Rated',
            'NOT RATED': 'Not Rated',
            'UNRATED': 'Not Rated'
        }
        
        return rating_mapping.get(rating, 'Not Rated')
    
    def _process_tags(self, tags: Any) -> List[str]:
        """Process and clean tags"""
        if pd.isna(tags) or tags is None:
            return []
        
        if isinstance(tags, str):
            # Split by common delimiters
            tags = re.split(r'[,;|]', tags)
        elif not isinstance(tags, list):
            tags = [str(tags)]
        
        processed_tags = []
        for tag in tags:
            tag = self._clean_text(tag).lower().strip()
            if tag and len(tag) > 1:  # Filter out single characters
                processed_tags.append(tag)
        
        return list(set(processed_tags))  # Remove duplicates
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and engineer features"""
        logger.info("Extracting features...")
        
        df = df.copy()
        
        # Decade feature
        if 'year' in df.columns:
            df['decade'] = (df['year'] // 10) * 10
            df['is_modern'] = (df['year'] >= 2000).astype(int)
            df['is_recent'] = (df['year'] >= 2010).astype(int)
            df['is_classic'] = (df['year'] <= 1980).astype(int)
        
        # Rating features
        if 'rating' in df.columns:
            df['rating_category'] = pd.cut(
                df['rating'], 
                bins=[0, 6.0, 7.0, 8.0, 9.0, 10.0],
                labels=['Poor', 'Fair', 'Good', 'Great', 'Excellent']
            )
            df['is_highly_rated'] = (df['rating'] >= 8.0).astype(int)
        
        # Duration features
        if 'duration_minutes' in df.columns:
            df['duration_category'] = pd.cut(
                df['duration_minutes'],
                bins=[0, 90, 120, 180, 300],
                labels=['Short', 'Medium', 'Long', 'Epic']
            )
            df['is_long_movie'] = (df['duration_minutes'] > 150).astype(int)
        
        # Genre features
        if 'genre' in df.columns:
            # Create binary features for major genres
            major_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller']
            for genre in major_genres:
                df[f'is_{genre.lower()}'] = df['genre'].str.contains(genre, case=False, na=False).astype(int)
            
            # Count number of genres
            df['genre_count'] = df['genre'].str.split(',').str.len()
        
        # Text length features
        text_fields = ['description', 'title']
        for field in text_fields:
            if field in df.columns:
                df[f'{field}_length'] = df[field].str.len()
                df[f'{field}_word_count'] = df[field].str.split().str.len()
        
        # Actor/Director features
        if 'actors' in df.columns:
            df['actor_count'] = df['actors'].str.split(',').str.len()
        
        # Create popularity score (synthetic)
        if 'rating' in df.columns and 'year' in df.columns:
            # Higher rating + more recent = higher popularity
            year_weight = (df['year'] - df['year'].min()) / (df['year'].max() - df['year'].min())
            rating_weight = (df['rating'] - df['rating'].min()) / (df['rating'].max() - df['rating'].min())
            df['popularity_score'] = (year_weight * 0.3 + rating_weight * 0.7)
        
        return df
    
    def _normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical features"""
        logger.info("Normalizing features...")
        
        df = df.copy()
        
        # Numerical features to normalize
        numerical_features = []
        for field in self.config['numerical_fields']:
            if field in df.columns:
                numerical_features.append(field)
        
        # Add engineered numerical features
        additional_numerical = [
            'duration_minutes', 'genre_count', 'description_length', 
            'description_word_count', 'title_length', 'title_word_count',
            'actor_count', 'popularity_score'
        ]
        
        for field in additional_numerical:
            if field in df.columns:
                numerical_features.append(field)
        
        # Normalize using MinMax scaling (0-1 range)
        if numerical_features:
            df[numerical_features] = self.minmax_scaler.fit_transform(df[numerical_features])
        
        return df
    
    def _create_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create text-based features using TF-IDF"""
        logger.info("Creating text features...")
        
        df = df.copy()
        
        # Combine text fields for content analysis
        text_columns = []
        for field in ['description', 'genre', 'tags_string', 'actors', 'director']:
            if field in df.columns:
                text_columns.append(field)
        
        if text_columns:
            # Create combined text feature
            df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)
            df['combined_text'] = df['combined_text'].apply(self._clean_text)
        
        # Create TF-IDF features for descriptions
        if 'description' in df.columns:
            descriptions = df['description'].fillna('')
            
            try:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)
                
                # Store feature names for later use
                self.feature_names.extend([
                    f'tfidf_{feature}' for feature in self.tfidf_vectorizer.get_feature_names_out()
                ])
                
                # Add top TF-IDF features to dataframe (limit to prevent memory issues)
                top_features = min(100, tfidf_matrix.shape[1])
                tfidf_df = pd.DataFrame(
                    tfidf_matrix[:, :top_features].toarray(),
                    columns=[f'tfidf_{i}' for i in range(top_features)]
                )
                
                df = pd.concat([df.reset_index(drop=True), tfidf_df], axis=1)
                
            except Exception as e:
                logger.warning(f"Error creating TF-IDF features: {e}")
        
        return df
    
    def get_feature_importance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate feature importance scores"""
        feature_importance = {}
        
        # Rating correlation for numerical features
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        if 'rating' in df.columns:
            correlations = df[numerical_cols].corrwith(df['rating']).abs().sort_values(ascending=False)
            for col, corr in correlations.items():
                if not pd.isna(corr) and col != 'rating':
                    feature_importance[col] = float(corr)
        
        return feature_importance
    
    def create_training_splits(self, df: pd.DataFrame, test_size: float = 0.2, 
                              random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create training and testing splits"""
        logger.info(f"Creating train/test splits with test_size={test_size}")
        
        # Stratify by rating category if available
        stratify = None
        if 'rating_category' in df.columns:
            stratify = df['rating_category']
        
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state,
            stratify=stratify
        )
        
        logger.info(f"Training set: {len(train_df)} samples")
        logger.info(f"Test set: {len(test_df)} samples")
        
        return train_df, test_df
    
    def save_preprocessed_data(self, df: pd.DataFrame, output_path: Union[str, Path]):
        """Save preprocessed data to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as parquet for efficiency
        if output_path.suffix == '.parquet':
            df.to_parquet(output_path, index=False)
        # Save as CSV
        elif output_path.suffix == '.csv':
            df.to_csv(output_path, index=False)
        # Save as JSON
        elif output_path.suffix == '.json':
            df.to_json(output_path, orient='records', indent=2)
        else:
            # Default to parquet
            output_path = output_path.with_suffix('.parquet')
            df.to_parquet(output_path, index=False)
        
        logger.info(f"Preprocessed data saved to: {output_path}")
    
    def generate_preprocessing_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive preprocessing report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'dataset_info': {
                'total_movies': len(df),
                'total_features': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'data_quality': {
                'missing_values': df.isnull().sum().to_dict(),
                'duplicate_rows': df.duplicated().sum(),
                'data_types': df.dtypes.astype(str).to_dict()
            },
            'feature_statistics': {},
            'text_features': {
                'tfidf_features': len([col for col in df.columns if col.startswith('tfidf_')]),
                'vocabulary_size': getattr(self.tfidf_vectorizer, 'vocabulary_', {})
            }
        }
        
        # Add statistics for numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            if col in df.columns:
                report['feature_statistics'][col] = {
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'missing_count': int(df[col].isnull().sum())
                }
        
        # Add categorical statistics
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if col in df.columns:
                report['feature_statistics'][col] = {
                    'unique_values': int(df[col].nunique()),
                    'top_value': str(df[col].mode().iloc[0]) if not df[col].mode().empty else 'N/A',
                    'missing_count': int(df[col].isnull().sum())
                }
        
        return report


# Utility functions for external use
def preprocess_movie_data(data_path: Union[str, Path, List[Dict]], 
                         config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Convenience function to preprocess movie data
    
    Args:
        data_path: Path to data file or list of movie dictionaries
        config: Optional preprocessing configuration
        
    Returns:
        Preprocessed DataFrame
    """
    preprocessor = MovieDataPreprocessor(config)
    return preprocessor.load_and_preprocess(data_path)


def create_ml_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extract ML-ready feature matrix from preprocessed DataFrame
    
    Args:
        df: Preprocessed movie DataFrame
        
    Returns:
        Tuple of (feature_matrix, feature_names)
    """
    # Select numerical features for ML
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    
    # Exclude target variables and IDs
    exclude_cols = ['rating', 'imdb_id', 'poster_url']
    feature_cols = [col for col in numerical_cols if col not in exclude_cols]
    
    X = df[feature_cols].fillna(0).values
    feature_names = feature_cols.tolist()
    
    return X, feature_names


if __name__ == "__main__":
    """Example usage and testing"""
    
    # Example configuration
    config = {
        'tfidf_max_features': 1000,
        'count_max_features': 500,
        'min_rating': 1.0,
        'max_rating': 10.0
    }
    
    # Initialize preprocessor
    preprocessor = MovieDataPreprocessor(config)
    
    # Example data path (adjust for your setup)
    data_path = "app/data/movies.json"
    
    try:
        # Preprocess data
        processed_df = preprocessor.load_and_preprocess(data_path)
        
        # Generate report
        report = preprocessor.generate_preprocessing_report(processed_df)
        
        # Create training splits
        train_df, test_df = preprocessor.create_training_splits(processed_df)
        
        # Get ML features
        X, feature_names = create_ml_features(processed_df)
        
        print(f"Preprocessing completed successfully!")
        print(f"Processed {len(processed_df)} movies")
        print(f"Created {len(feature_names)} ML features")
        print(f"Training set: {len(train_df)} samples")
        print(f"Test set: {len(test_df)} samples")
        
    except Exception as e:
        print(f"Error during preprocessing: {e}")