"""
Data Management and Movie Database
"""

from .movie_dataset import MovieDatabase

__all__ = ["MovieDatabase"]

# Data constants
SUPPORTED_GENRES = [
    'Action', 'Adventure', 'Comedy', 'Drama', 'Horror', 'Romance',
    'Sci-Fi', 'Fantasy', 'Thriller', 'Mystery', 'Documentary', 'Animation'
]

MOOD_MAPPINGS = {
    'Excited & Energetic': ['action', 'adventure', 'fast-paced', 'thrilling'],
    'Relaxed & Chill': ['comedy', 'romantic', 'feel-good', 'light'],
    'Thoughtful & Deep': ['drama', 'philosophical', 'meaningful', 'complex'],
    'Romantic & Emotional': ['romance', 'emotional', 'love', 'heartwarming'],
    'Adventurous & Bold': ['adventure', 'epic', 'journey', 'exploration'],
    'Nostalgic & Warm': ['family', 'nostalgic', 'classic', 'heartwarming']
}

DECADE_RANGES = {
    '2020s': (2020, 2029),
    '2010s': (2010, 2019),
    '2000s': (2000, 2009),
    '1990s': (1990, 1999),
    '1980s': (1980, 1989),
    '1970s': (1970, 1979),
    'Classic (Before 1970)': (1900, 1969)
}

DURATION_RANGES = {
    'Short (< 90 min)': (0, 89),
    'Medium (90-120 min)': (90, 120),
    'Long (120-180 min)': (121, 180),
    'Epic (> 180 min)': (181, 999)
}