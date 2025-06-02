# CineSense API Documentation

> **Version:** 1.0.0  
> **Base URL:** `https://your-api-domain.com`  
> **Development URL:** `http://localhost:8000`

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Recommendations](#recommendations)
  - [Movies](#movies)
  - [Genres](#genres)
  - [Statistics](#statistics)
- [Data Models](#data-models)
- [Examples](#examples)
- [SDKs](#sdks)
- [Changelog](#changelog)

## 🎯 Overview

The CineSense API provides AI-powered movie recommendations based on user preferences. It combines content-based filtering, collaborative filtering, and machine learning to deliver personalized movie suggestions with explanations.

### Key Features
- **Personalized Recommendations**: ML-powered suggestions based on user preferences
- **Multiple Recommendation Types**: Personal, trending, similar movies, genre-based
- **Rich Movie Data**: Comprehensive movie information with ratings, cast, directors
- **Confidence Scoring**: Reliability scores for each recommendation
- **Explanation Engine**: AI-generated reasons for each recommendation
- **Real-time Processing**: Fast response times with intelligent caching
- **RESTful Design**: Standard HTTP methods and status codes

## 🔐 Authentication

**Current Version**: No authentication required (development)

**Production Version**: JWT-based authentication (planned)

```http
Authorization: Bearer <your-jwt-token>
```

## 🌐 Base URLs

| Environment | URL |
|------------|-----|
| **Production** | `https://cinesense-api.onrender.com` |
| **Staging** | `https://cinesense-staging.onrender.com` |
| **Development** | `http://localhost:8000` |

## 📦 Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "status": "success",
  "data": {
    // Response data here
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "request_id": "req_123456789"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid genre specified",
    "details": {
      "field": "genres",
      "provided": "InvalidGenre",
      "allowed": ["Action", "Comedy", "Drama", ...]
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "request_id": "req_123456789"
  }
}
```

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| **200** | OK | Request successful |
| **201** | Created | Resource created successfully |
| **400** | Bad Request | Invalid request parameters |
| **401** | Unauthorized | Authentication required |
| **403** | Forbidden | Insufficient permissions |
| **404** | Not Found | Resource not found |
| **422** | Unprocessable Entity | Validation error |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server error |
| **503** | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `NOT_FOUND` | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `MODEL_NOT_READY` | ML model not trained/loaded |
| `PROCESSING_ERROR` | Error processing recommendation |
| `INVALID_PREFERENCES` | Invalid user preferences |

## ⏱️ Rate Limiting

- **Development**: 100 requests per minute
- **Production**: 60 requests per minute per IP
- **Authenticated**: 200 requests per minute per user

Rate limit headers included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642262400
```

## 🛣️ Endpoints

### Health Check

#### `GET /`
Basic health check endpoint.

**Response:**
```json
{
  "status": "success",
  "data": {
    "message": "CineSense API is running!",
    "status": "healthy"
  }
}
```

#### `GET /api/health`
Detailed health check with system information.

**Response:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "database_size": 50,
    "model_trained": true,
    "uptime": "2 days, 3 hours",
    "memory_usage": "245 MB",
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

---

### Recommendations

#### `POST /api/recommendations`
Get personalized movie recommendations based on user preferences.

**Request Body:**
```json
{
  "genres": ["Action", "Sci-Fi"],
  "mood": "Excited & Energetic",
  "language": "English",
  "decade": "2020s",
  "duration": "Medium (90-120 min)",
  "rating": "PG-13",
  "actors": "Tom Cruise, Leonardo DiCaprio",
  "directors": "Christopher Nolan",
  "keywords": "space adventure",
  "user_id": "user_123",
  "n_recommendations": 10,
  "exclude_movies": ["Movie Title 1", "Movie Title 2"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `genres` | `string[]` | ✅ | List of preferred genres |
| `mood` | `string` | ✅ | Current mood/feeling |
| `language` | `string` | ✅ | Preferred language |
| `decade` | `string` | ✅ | Preferred time period |
| `duration` | `string` | ✅ | Preferred movie length |
| `rating` | `string` | ✅ | Content rating preference |
| `actors` | `string` | ❌ | Favorite actors (comma-separated) |
| `directors` | `string` | ❌ | Favorite directors (comma-separated) |
| `keywords` | `string` | ❌ | Keywords or themes |
| `user_id` | `string` | ❌ | User ID for collaborative filtering |
| `n_recommendations` | `integer` | ❌ | Number of recommendations (default: 10, max: 50) |
| `exclude_movies` | `string[]` | ❌ | Movies to exclude from results |

**Valid Values:**

**Genres:**
`Action`, `Adventure`, `Animation`, `Comedy`, `Crime`, `Drama`, `Family`, `Fantasy`, `History`, `Horror`, `Music`, `Mystery`, `Romance`, `Sci-Fi`, `Superhero`, `Thriller`, `War`

**Moods:**
- `Excited & Energetic`
- `Relaxed & Chill`
- `Thoughtful & Deep`
- `Romantic & Emotional`
- `Adventurous & Bold`
- `Nostalgic & Warm`

**Languages:**
`English`, `Spanish`, `French`, `Japanese`, `Korean`, `Hindi`, `Mandarin`, `Italian`, `German`, `Any Language`

**Decades:**
`2020s`, `2010s`, `2000s`, `1990s`, `1980s`, `1970s`, `Classic (Before 1970)`, `No Preference`

**Durations:**
`Short (< 90 min)`, `Medium (90-120 min)`, `Long (120-180 min)`, `Epic (> 180 min)`, `No Preference`

**Ratings:**
`G`, `PG`, `PG-13`, `R`, `No Preference`

**Response:**
```json
{
  "status": "success",
  "data": {
    "recommendations": [
      {
        "title": "Dune: Part One",
        "genre": "Sci-Fi, Adventure",
        "description": "Paul Atreides, a brilliant and gifted young man...",
        "rating": 8.0,
        "year": 2021,
        "duration": "155 min",
        "director": "Denis Villeneuve",
        "actors": "Timothée Chalamet, Rebecca Ferguson, Oscar Isaac",
        "poster_url": "https://image.tmdb.org/t/p/w500/...",
        "confidence_score": 0.92,
        "confidence_level": "Very High",
        "similarity_score": 0.87,
        "preference_match": 0.94,
        "explanation": "Recommended because it matches your interest in Sci-Fi and your excited mood",
        "tags": ["Perfect Match", "Great", "Recent"],
        "rank": 1,
        "recommendation_sources": ["content", "collaborative"],
        "recommendation_id": "rec_abc123"
      }
    ],
    "total_count": 10,
    "preferences_summary": "Genres: Action, Sci-Fi | Mood: Excited & Energetic | Era: 2020s",
    "processing_time": 0.245,
    "model_version": "1.0.0"
  }
}
```

#### `GET /api/recommendations/similar/{movie_title}`
Get movies similar to a specific movie.

**Parameters:**
- `movie_title` (path): Title of the reference movie
- `n_similar` (query): Number of similar movies (default: 5, max: 20)

**Example:**
```http
GET /api/recommendations/similar/Inception?n_similar=5
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "reference_movie": "Inception",
    "similar_movies": [
      {
        "title": "Interstellar",
        "similarity_score": 0.89,
        "explanation": "Similar complex sci-fi themes and Christopher Nolan direction"
      }
    ]
  }
}
```

#### `GET /api/recommendations/trending`
Get trending/popular movies.

**Parameters:**
- `n_movies` (query): Number of trending movies (default: 10, max: 50)
- `time_period` (query): Trending period - `day`, `week`, `month`, `year` (default: `month`)

**Response:**
```json
{
  "status": "success",
  "data": {
    "trending_movies": [
      {
        "title": "Top Gun: Maverick",
        "trending_score": 0.94,
        "explanation": "Trending due to high ratings and recent popularity"
      }
    ],
    "time_period": "month"
  }
}
```

#### `GET /api/recommendations/genre/{genre}`
Get top movies by genre.

**Parameters:**
- `genre` (path): Genre name
- `n_movies` (query): Number of movies (default: 10, max: 50)
- `sort_by` (query): Sort criteria - `rating`, `year`, `popularity` (default: `rating`)

**Example:**
```http
GET /api/recommendations/genre/Action?n_movies=10&sort_by=rating
```

---

### Movies

#### `GET /api/movies`
Get movies with optional filtering.

**Parameters:**
- `genre` (query): Filter by genre
- `year` (query): Filter by specific year
- `year_min` (query): Minimum year
- `year_max` (query): Maximum year
- `rating_min` (query): Minimum rating (0-10)
- `rating_max` (query): Maximum rating (0-10)
- `language` (query): Filter by language
- `duration_min` (query): Minimum duration in minutes
- `duration_max` (query): Maximum duration in minutes
- `search` (query): Search in title, description, actors, director
- `sort_by` (query): Sort by `rating`, `year`, `title`, `popularity` (default: `rating`)
- `sort_order` (query): `asc` or `desc` (default: `desc`)
- `limit` (query): Number of results (default: 20, max: 100)
- `offset` (query): Pagination offset (default: 0)

**Example:**
```http
GET /api/movies?genre=Action&year_min=2020&rating_min=7.0&limit=10
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "movies": [
      {
        "title": "Top Gun: Maverick",
        "genre": "Action, Drama",
        "rating": 8.3,
        "year": 2022,
        "duration": "130 min",
        "language": "English",
        "director": "Joseph Kosinski",
        "actors": "Tom Cruise, Miles Teller, Jennifer Connelly",
        "description": "After thirty years, Maverick is still pushing...",
        "poster_url": "https://image.tmdb.org/t/p/w500/...",
        "imdb_id": "tt1745960",
        "tags": ["sequel", "action", "aviation"]
      }
    ],
    "total_count": 25,
    "filtered_count": 10,
    "filters_applied": {
      "genre": "Action",
      "year_min": 2020,
      "rating_min": 7.0
    },
    "pagination": {
      "limit": 10,
      "offset": 0,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### `GET /api/movies/{movie_id}`
Get detailed information about a specific movie.

**Parameters:**
- `movie_id` (path): Movie ID or title

**Response:**
```json
{
  "status": "success",
  "data": {
    "movie": {
      "id": "mv_123",
      "title": "Inception",
      "genre": "Sci-Fi, Thriller",
      "description": "A thief who steals corporate secrets...",
      "rating": 8.8,
      "year": 2010,
      "duration": "148 min",
      "director": "Christopher Nolan",
      "actors": "Leonardo DiCaprio, Marion Cotillard, Tom Hardy",
      "language": "English",
      "country": "USA",
      "mpaa_rating": "PG-13",
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "imdb_id": "tt1375666",
      "tags": ["mind-bending", "complex plot", "visual effects"],
      "box_office": "$836.8 million",
      "budget": "$160 million",
      "awards": ["4 Academy Awards", "8 nominations"],
      "similar_movies": ["Interstellar", "The Matrix", "Shutter Island"]
    }
  }
}
```

---

### Genres

#### `GET /api/genres`
Get all available movie genres.

**Response:**
```json
{
  "status": "success",
  "data": {
    "genres": [
      {
        "name": "Action",
        "count": 18,
        "description": "High-energy movies with physical feats, chases, and combat"
      },
      {
        "name": "Comedy",
        "count": 12,
        "description": "Movies designed to amuse and entertain through humor"
      }
    ],
    "total_genres": 17
  }
}
```

#### `GET /api/genres/{genre}/stats`
Get statistics for a specific genre.

**Response:**
```json
{
  "status": "success",
  "data": {
    "genre": "Action",
    "statistics": {
      "total_movies": 18,
      "average_rating": 7.8,
      "year_range": {
        "min": 1977,
        "max": 2022
      },
      "top_rated": [
        {
          "title": "The Dark Knight",
          "rating": 9.0,
          "year": 2008
        }
      ],
      "most_recent": [
        {
          "title": "Top Gun: Maverick",
          "rating": 8.3,
          "year": 2022
        }
      ]
    }
  }
}
```

---

### Statistics

#### `GET /api/stats`
Get comprehensive database and API statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "database_stats": {
      "total_movies": 50,
      "total_genres": 17,
      "year_range": {
        "min": 1942,
        "max": 2022
      },
      "rating_distribution": {
        "9.0+": 6,
        "8.5-8.9": 11,
        "8.0-8.4": 19,
        "7.5-7.9": 11,
        "7.0-7.4": 3
      },
      "decade_distribution": {
        "2020s": 12,
        "2010s": 15,
        "2000s": 8,
        "1990s": 10,
        "1980s": 2,
        "1970s": 2,
        "1940s": 1
      },
      "language_distribution": {
        "English": 45,
        "Japanese": 1,
        "French": 1,
        "Korean": 1,
        "Mixed": 2
      }
    },
    "api_stats": {
      "total_requests": 1234,
      "avg_response_time": 0.245,
      "cache_hit_rate": 0.68,
      "popular_endpoints": [
        {
          "endpoint": "/api/recommendations",
          "requests": 856
        }
      ],
      "model_info": {
        "version": "1.0.0",
        "last_trained": "2024-01-15T10:30:00Z",
        "accuracy": 0.87
      }
    }
  }
}
```

#### `GET /api/stats/recommendations`
Get recommendation engine statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "recommendation_stats": {
      "total_requests": 856,
      "avg_processing_time": 0.245,
      "cache_hit_rate": 0.68,
      "confidence_distribution": {
        "Very High": 234,
        "High": 345,
        "Medium": 201,
        "Low": 76
      },
      "popular_genres": [
        {
          "genre": "Action",
          "requests": 234
        }
      ],
      "popular_moods": [
        {
          "mood": "Excited & Energetic",
          "requests": 189
        }
      ]
    }
  }
}
```

---

## 📋 Data Models

### UserPreferences
```json
{
  "genres": ["string"],
  "mood": "string",
  "language": "string", 
  "decade": "string",
  "duration": "string",
  "rating": "string",
  "actors": "string",
  "directors": "string",
  "keywords": "string"
}
```

### MovieResponse
```json
{
  "title": "string",
  "genre": "string",
  "description": "string",
  "rating": "number",
  "year": "integer",
  "duration": "string",
  "director": "string",
  "actors": "string",
  "poster_url": "string",
  "confidence_score": "number",
  "imdb_id": "string",
  "tags": ["string"]
}
```

### RecommendationResponse
```json
{
  "recommendations": ["MovieResponse"],
  "total_count": "integer",
  "preferences_summary": "string",
  "processing_time": "number",
  "model_version": "string"
}
```

---

## 💡 Examples

### Get Personalized Recommendations

```bash
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "genres": ["Action", "Sci-Fi"],
    "mood": "Excited & Energetic",
    "language": "English",
    "decade": "2020s",
    "duration": "Medium (90-120 min)",
    "rating": "PG-13"
  }'
```

### Search Movies

```bash
curl "http://localhost:8000/api/movies?search=inception&limit=5"
```

### Get Genre Statistics

```bash
curl "http://localhost:8000/api/genres/Action/stats"
```

### JavaScript/Fetch Example

```javascript
const getRecommendations = async (preferences) => {
  try {
    const response = await fetch('/api/recommendations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(preferences)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data.recommendations;
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    throw error;
  }
};

// Usage
const preferences = {
  genres: ['Comedy', 'Romance'],
  mood: 'Relaxed & Chill',
  language: 'English',
  decade: '2010s',
  duration: 'Medium (90-120 min)',
  rating: 'PG-13'
};

getRecommendations(preferences)
  .then(recommendations => {
    console.log('Got recommendations:', recommendations);
  })
  .catch(error => {
    console.error('Failed to get recommendations:', error);
  });
```

### Python Example

```python
import requests
import json

def get_recommendations(preferences):
    url = "http://localhost:8000/api/recommendations"
    
    try:
        response = requests.post(url, json=preferences)
        response.raise_for_status()
        
        data = response.json()
        return data['data']['recommendations']
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Usage
preferences = {
    "genres": ["Drama", "Thriller"],
    "mood": "Thoughtful & Deep",
    "language": "English",
    "decade": "2000s",
    "duration": "Long (120-180 min)",
    "rating": "R"
}

recommendations = get_recommendations(preferences)
if recommendations:
    for rec in recommendations:
        print(f"{rec['title']} ({rec['year']}) - {rec['rating']}/10")
        print(f"  {rec['explanation']}")
```

---

## 🔧 SDKs

### JavaScript/TypeScript SDK

```typescript
interface CineSenseAPI {
  getRecommendations(preferences: UserPreferences): Promise<RecommendationResponse>;
  getMovies(filters?: MovieFilters): Promise<MovieResponse[]>;
  getSimilarMovies(title: string, count?: number): Promise<MovieResponse[]>;
  getTrendingMovies(count?: number): Promise<MovieResponse[]>;
}

class CineSenseClient implements CineSenseAPI {
  constructor(private baseURL: string, private apiKey?: string) {}
  
  async getRecommendations(preferences: UserPreferences): Promise<RecommendationResponse> {
    // Implementation
  }
}
```

### Python SDK

```python
class CineSenseClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
    
    def get_recommendations(self, preferences: dict) -> dict:
        """Get personalized movie recommendations"""
        # Implementation
    
    def get_movies(self, **filters) -> list:
        """Get movies with filtering"""
        # Implementation
```

---

## 📝 Changelog

### Version 1.0.0 (2024-01-15)
- Initial API release
- Personalized recommendations endpoint
- Movie search and filtering
- Genre and statistics endpoints
- Comprehensive error handling
- Rate limiting implementation
- Full documentation

### Planned Features (v1.1.0)
- User authentication and profiles
- Recommendation history
- Movie ratings and reviews
- Advanced filtering options
- Webhook support
- GraphQL endpoint

---

## 📞 Support

- **Documentation**: [docs.cinesense.ai](https://docs.cinesense.ai)
- **Support Email**: support@cinesense.ai
- **GitHub Issues**: [github.com/cinesense/api/issues](https://github.com/cinesense/api/issues)
- **Status Page**: [status.cinesense.ai](https://status.cinesense.ai)

---

**Last Updated**: January 15, 2024  
**API Version**: 1.0.0