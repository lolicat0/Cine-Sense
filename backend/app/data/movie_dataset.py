import json
import pandas as pd
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MovieDatabase:
    """Movie database manager with synthetic and real movie data"""
    
    def __init__(self):
        self.movies = []
        self.genres = set()
        self.data_file = Path(__file__).parent / "movies.json"
        
    async def initialize(self):
        """Initialize the movie database"""
        try:
            # Try to load from file first
            if self.data_file.exists():
                await self._load_from_file()
            else:
                # Generate synthetic data if no file exists
                await self._generate_synthetic_data()
                await self._save_to_file()
                
            logger.info(f"Movie database initialized with {len(self.movies)} movies")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            # Fallback to minimal synthetic data
            await self._generate_minimal_data()
    
    async def _load_from_file(self):
        """Load movies from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.movies = data.get('movies', [])
                self._extract_genres()
                
        except Exception as e:
            logger.error(f"Error loading from file: {e}")
            await self._generate_synthetic_data()
    
    async def _save_to_file(self):
        """Save movies to JSON file"""
        try:
            data = {
                'movies': self.movies,
                'metadata': {
                    'total_count': len(self.movies),
                    'genres': list(self.genres),
                    'last_updated': pd.Timestamp.now().isoformat()
                }
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
    
    def _extract_genres(self):
        """Extract unique genres from movies"""
        for movie in self.movies:
            if movie.get('genre'):
                genres = [g.strip() for g in movie['genre'].split(',')]
                self.genres.update(genres)
    
    async def _generate_synthetic_data(self):
        """Generate comprehensive synthetic movie data"""
        self.movies = [
            # Popular Recent Movies
            {
                "title": "Dune: Part One",
                "genre": "Sci-Fi, Adventure",
                "description": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
                "rating": 8.0,
                "year": 2021,
                "duration": "155 min",
                "director": "Denis Villeneuve",
                "actors": "Timothée Chalamet, Rebecca Ferguson, Oscar Isaac",
                "tags": ["epic", "visual spectacle", "book adaptation"]
            },
            {
                "title": "Spider-Man: No Way Home",
                "genre": "Action, Superhero",
                "description": "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help. When a spell goes wrong, dangerous foes from other worlds start to appear.",
                "rating": 8.4,
                "year": 2021,
                "duration": "148 min",
                "director": "Jon Watts",
                "actors": "Tom Holland, Zendaya, Benedict Cumberbatch",
                "tags": ["multiverse", "superhero", "action-packed"]
            },
            {
                "title": "Everything Everywhere All at Once",
                "genre": "Comedy, Sci-Fi, Drama",
                "description": "An aging Chinese immigrant is swept up in an insane adventure, where she alone can save what's important to her by connecting with the lives she could have led.",
                "rating": 7.8,
                "year": 2022,
                "duration": "139 min",
                "director": "Daniels",
                "actors": "Michelle Yeoh, Stephanie Hsu, Ke Huy Quan",
                "tags": ["multiverse", "family", "mind-bending"]
            },
            {
                "title": "Top Gun: Maverick",
                "genre": "Action, Drama",
                "description": "After thirty years, Maverick is still pushing the envelope as a top naval aviator, but must confront ghosts of his past when he leads TOP GUN's elite graduates on a mission.",
                "rating": 8.3,
                "year": 2022,
                "duration": "130 min",
                "director": "Joseph Kosinski",
                "actors": "Tom Cruise, Miles Teller, Jennifer Connelly",
                "tags": ["sequel", "action", "aviation"]
            },
            {
                "title": "The Batman",
                "genre": "Action, Crime, Drama",
                "description": "When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate the city's hidden corruption.",
                "rating": 7.8,
                "year": 2022,
                "duration": "176 min",
                "director": "Matt Reeves",
                "actors": "Robert Pattinson, Zoë Kravitz, Jeffrey Wright",
                "tags": ["dark", "detective", "superhero"]
            },
            
            # Classic Movies
            {
                "title": "The Godfather",
                "genre": "Crime, Drama",
                "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                "rating": 9.2,
                "year": 1972,
                "duration": "175 min",
                "director": "Francis Ford Coppola",
                "actors": "Marlon Brando, Al Pacino, James Caan",
                "tags": ["classic", "crime family", "masterpiece"]
            },
            {
                "title": "Casablanca",
                "genre": "Drama, Romance",
                "description": "A cynical American expatriate struggles to decide whether or not he should help his former lover and her fugitive husband escape French Morocco.",
                "rating": 8.5,
                "year": 1942,
                "duration": "102 min",
                "director": "Michael Curtiz",
                "actors": "Humphrey Bogart, Ingrid Bergman, Paul Henreid",
                "tags": ["classic", "romance", "wartime"]
            },
            {
                "title": "Pulp Fiction",
                "genre": "Crime, Drama",
                "description": "The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.",
                "rating": 8.9,
                "year": 1994,
                "duration": "154 min",
                "director": "Quentin Tarantino",
                "actors": "John Travolta, Uma Thurman, Samuel L. Jackson",
                "tags": ["nonlinear", "cult classic", "dialogue-driven"]
            },
            
            # Comedy Movies
            {
                "title": "Knives Out",
                "genre": "Comedy, Mystery",
                "description": "A detective investigates the death of a patriarch of an eccentric, combative family.",
                "rating": 7.9,
                "year": 2019,
                "duration": "130 min",
                "director": "Rian Johnson",
                "actors": "Daniel Craig, Chris Evans, Ana de Armas",
                "tags": ["whodunit", "ensemble cast", "clever"]
            },
            {
                "title": "The Grand Budapest Hotel",
                "genre": "Comedy, Drama",
                "description": "A writer encounters the owner of an aging high-class hotel, who tells him of his early years serving as a lobby boy.",
                "rating": 8.1,
                "year": 2014,
                "duration": "99 min",
                "director": "Wes Anderson",
                "actors": "Ralph Fiennes, F. Murray Abraham, Mathieu Amalric",
                "tags": ["whimsical", "visual style", "quirky"]
            },
            {
                "title": "Parasite",
                "genre": "Comedy, Drama, Thriller",
                "description": "A poor family schemes to become employed by a wealthy family and infiltrate their household by posing as unrelated, highly qualified individuals.",
                "rating": 8.6,
                "year": 2019,
                "duration": "132 min",
                "director": "Bong Joon-ho",
                "actors": "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong",
                "tags": ["social commentary", "dark comedy", "foreign"]
            },
            
            # Horror Movies
            {
                "title": "Hereditary",
                "genre": "Horror, Drama",
                "description": "A grieving family is haunted by tragedy and disturbing secrets.",
                "rating": 7.3,
                "year": 2018,
                "duration": "127 min",
                "director": "Ari Aster",
                "actors": "Toni Collette, Milly Shapiro, Gabriel Byrne",
                "tags": ["psychological horror", "family trauma", "disturbing"]
            },
            {
                "title": "Get Out",
                "genre": "Horror, Thriller",
                "description": "A young African-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness becomes a nightmare.",
                "rating": 7.7,
                "year": 2017,
                "duration": "104 min",
                "director": "Jordan Peele",
                "actors": "Daniel Kaluuya, Allison Williams, Bradley Whitford",
                "tags": ["social thriller", "psychological", "suspenseful"]
            },
            
            # Romance Movies
            {
                "title": "Lady Bird",
                "genre": "Comedy, Drama",
                "description": "In 2002, an artistically inclined seventeen-year-old girl comes of age in Sacramento, California.",
                "rating": 7.4,
                "year": 2017,
                "duration": "94 min",
                "director": "Greta Gerwig",
                "actors": "Saoirse Ronan, Laurie Metcalf, Tracy Letts",
                "tags": ["coming-of-age", "mother-daughter", "heartfelt"]
            },
            {
                "title": "Call Me By Your Name",
                "genre": "Romance, Drama",
                "description": "In 1980s Italy, romance blossoms between a seventeen-year-old student and the older man hired as his father's research assistant.",
                "rating": 7.9,
                "year": 2017,
                "duration": "132 min",
                "director": "Luca Guadagnino",
                "actors": "Timothée Chalamet, Armie Hammer, Michael Stuhlbarg",
                "tags": ["coming-of-age", "first love", "beautiful"]
            },
            
            # Animation Movies
            {
                "title": "Soul",
                "genre": "Animation, Comedy, Family",
                "description": "A musician who has lost his passion for music is transported out of his body and must find his way back with the help of an infant soul learning about herself.",
                "rating": 8.0,
                "year": 2020,
                "duration": "100 min",
                "director": "Pete Docter",
                "actors": "Jamie Foxx, Tina Fey, Graham Norton",
                "tags": ["philosophical", "music", "pixar"]
            },
            {
                "title": "Spider-Man: Into the Spider-Verse",
                "genre": "Animation, Action, Adventure",
                "description": "Teen Miles Morales becomes Spider-Man of his reality, crossing his path with five counterparts from other dimensions.",
                "rating": 8.4,
                "year": 2018,
                "duration": "117 min",
                "director": "Bob Persichetti, Peter Ramsey",
                "actors": "Shameik Moore, Jake Johnson, Hailee Steinfeld",
                "tags": ["groundbreaking animation", "multiverse", "superhero"]
            },
            
            # Action Movies
            {
                "title": "Mad Max: Fury Road",
                "genre": "Action, Adventure",
                "description": "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of a group of female prisoners.",
                "rating": 8.1,
                "year": 2015,
                "duration": "120 min",
                "director": "George Miller",
                "actors": "Tom Hardy, Charlize Theron, Nicholas Hoult",
                "tags": ["post-apocalyptic", "practical effects", "intense"]
            },
            {
                "title": "John Wick",
                "genre": "Action, Crime, Thriller",
                "description": "An ex-hit-man comes out of retirement to track down the gangsters that took everything from him.",
                "rating": 7.4,
                "year": 2014,
                "duration": "101 min",
                "director": "Chad Stahelski",
                "actors": "Keanu Reeves, Michael Nyqvist, Alfie Allen",
                "tags": ["revenge", "stylized action", "gun-fu"]
            },
            
            # Sci-Fi Movies
            {
                "title": "Blade Runner 2049",
                "genre": "Sci-Fi, Drama",
                "description": "Young Blade Runner K's discovery of a long-buried secret leads him to track down former Blade Runner Rick Deckard.",
                "rating": 8.0,
                "year": 2017,
                "duration": "164 min",
                "director": "Denis Villeneuve",
                "actors": "Ryan Gosling, Harrison Ford, Ana de Armas",
                "tags": ["cyberpunk", "philosophical", "visual masterpiece"]
            },
            {
                "title": "Arrival",
                "genre": "Sci-Fi, Drama",
                "description": "A linguist works with the military to communicate with alien lifeforms after twelve mysterious spacecraft appear around the world.",
                "rating": 7.9,
                "year": 2016,
                "duration": "116 min",
                "director": "Denis Villeneuve",
                "actors": "Amy Adams, Jeremy Renner, Forest Whitaker",
                "tags": ["first contact", "linguistics", "thought-provoking"]
            },
            
            # Drama Movies
            {
                "title": "Moonlight",
                "genre": "Drama",
                "description": "A young African-American man grapples with his identity and sexuality while experiencing the everyday struggles of childhood, adolescence, and burgeoning adulthood.",
                "rating": 7.4,
                "year": 2016,
                "duration": "111 min",
                "director": "Barry Jenkins",
                "actors": "Mahershala Ali, Naomie Harris, Trevante Rhodes",
                "tags": ["coming-of-age", "identity", "powerful"]
            },
            {
                "title": "1917",
                "genre": "Drama, War",
                "description": "Two British soldiers are tasked with delivering a critical message to call off a doomed offensive attack.",
                "rating": 8.3,
                "year": 2019,
                "duration": "119 min",
                "director": "Sam Mendes",
                "actors": "George MacKay, Dean-Charles Chapman, Mark Strong",
                "tags": ["one-shot", "war", "technical achievement"]
            },
            
            # Thriller Movies
            {
                "title": "Gone Girl",
                "genre": "Thriller, Drama",
                "description": "With his wife's disappearance having become the focus of an intense media circus, a man sees the spotlight turned on him when it's suspected that he may not be innocent.",
                "rating": 8.1,
                "year": 2014,
                "duration": "149 min",
                "director": "David Fincher",
                "actors": "Ben Affleck, Rosamund Pike, Neil Patrick Harris",
                "tags": ["psychological thriller", "marriage", "unreliable narrator"]
            },
            {
                "title": "Shutter Island",
                "genre": "Thriller, Mystery",
                "description": "In 1954, a U.S. Marshal investigates the disappearance of a murderer who escaped from a hospital for the criminally insane.",
                "rating": 8.2,
                "year": 2010,
                "duration": "138 min",
                "director": "Martin Scorsese",
                "actors": "Leonardo DiCaprio, Mark Ruffalo, Ben Kingsley",
                "tags": ["psychological thriller", "plot twist", "atmospheric"]
            }
        ]
        
        self._extract_genres()
        
    async def _generate_minimal_data(self):
        """Generate minimal fallback data"""
        self.movies = [
            {
                "title": "The Matrix",
                "genre": "Action, Sci-Fi",
                "description": "A computer programmer discovers reality as he knows it is a simulation.",
                "rating": 8.7,
                "year": 1999,
                "duration": "136 min",
                "director": "The Wachowskis",
                "actors": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
                "tags": ["cyberpunk", "philosophical", "groundbreaking"]
            }
        ]
        self._extract_genres()
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        """Get data formatted for ML training"""
        return self.movies.copy()
    
    def filter_movies(self, genre: str = None, year: int = None, 
                     rating_min: float = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Filter movies based on criteria"""
        filtered = self.movies.copy()
        
        if genre:
            filtered = [m for m in filtered if genre.lower() in m.get('genre', '').lower()]
        
        if year:
            filtered = [m for m in filtered if m.get('year') == year]
        
        if rating_min:
            filtered = [m for m in filtered if m.get('rating', 0) >= rating_min]
        
        return filtered[:limit]
    
    def get_genres(self) -> List[str]:
        """Get all available genres"""
        return sorted(list(self.genres))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.movies:
            return {"total_movies": 0}
        
        df = pd.DataFrame(self.movies)
        
        return {
            "total_movies": len(self.movies),
            "genres": len(self.genres),
            "year_range": {
                "min": int(df['year'].min()) if 'year' in df else 0,
                "max": int(df['year'].max()) if 'year' in df else 0
            },
            "rating_stats": {
                "average": float(df['rating'].mean()) if 'rating' in df else 0,
                "min": float(df['rating'].min()) if 'rating' in df else 0,
                "max": float(df['rating'].max()) if 'rating' in df else 0
            },
            "top_genres": list(self.genres)[:10]
        }