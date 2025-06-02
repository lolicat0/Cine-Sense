import React from 'react';

const MovieCard = ({ movie }) => {
  const {
    title,
    genre,
    description,
    rating,
    year,
    duration,
    director,
    actors,
    poster_url,
    confidence_score
  } = movie;

  return (
    <div className="movie-card slide-up">
      <div className="movie-poster">
        {poster_url ? (
          <img 
            src={poster_url} 
            alt={title}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <div style={{ 
            background: 'linear-gradient(45deg, #8b45c1, #d946ef)',
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '3rem'
          }}>
            🎬
          </div>
        )}
      </div>
      
      <div className="movie-info">
        <h3 className="movie-title">{title}</h3>
        
        <div className="movie-genre">
          {genre} • {year} • {duration}
        </div>
        
        {director && (
          <div style={{ 
            color: 'rgba(255, 255, 255, 0.6)', 
            fontSize: '0.8rem', 
            marginBottom: '0.5rem' 
          }}>
            Directed by {director}
          </div>
        )}
        
        <p className="movie-description">{description}</p>
        
        {actors && (
          <div style={{ 
            color: 'rgba(255, 255, 255, 0.7)', 
            fontSize: '0.8rem', 
            marginBottom: '1rem' 
          }}>
            <strong>Stars:</strong> {actors}
          </div>
        )}
        
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <div className="movie-rating">
            <span>⭐</span>
            <span>{rating}/10</span>
          </div>
          
          {confidence_score && (
            <div style={{ 
              background: 'rgba(139, 69, 193, 0.3)', 
              padding: '0.2rem 0.5rem', 
              borderRadius: '10px',
              fontSize: '0.8rem',
              color: '#d946ef'
            }}>
              {Math.round(confidence_score * 100)}% Match
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MovieCard;