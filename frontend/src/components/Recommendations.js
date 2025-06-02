import React from 'react';
import MovieCard from './MovieCard';

const Recommendations = ({ movies, onRestart, preferences }) => {
  return (
    <div className="recommendations fade-in">
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h2 style={{ 
          fontSize: '2.5rem', 
          background: 'linear-gradient(45deg, #8b45c1, #d946ef)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '1rem'
        }}>
          Your Perfect Movie Matches
        </h2>
        
        <p style={{ 
          color: 'rgba(255, 255, 255, 0.7)', 
          fontSize: '1.1rem',
          marginBottom: '1rem'
        }}>
          Based on your preferences, here are {movies.length} personalized recommendations
        </p>
        
        <button 
          className="btn-primary" 
          onClick={onRestart}
          style={{ marginBottom: '2rem' }}
        >
          🔄 Get New Recommendations
        </button>
      </div>

      {movies.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '1.1rem' }}>
            No recommendations found. Please try different preferences.
          </p>
        </div>
      ) : (
        <div className="recommendations-grid">
          {movies.map((movie, index) => (
            <MovieCard key={index} movie={movie} />
          ))}
        </div>
      )}
      
      <div style={{ 
        textAlign: 'center', 
        marginTop: '3rem', 
        padding: '2rem',
        background: 'rgba(30, 13, 38, 0.6)',
        borderRadius: '15px',
        border: '1px solid rgba(139, 69, 193, 0.3)'
      }}>
        <h3 style={{ color: '#d946ef', marginBottom: '1rem' }}>
          💡 Pro Tip
        </h3>
        <p style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
          Not quite what you're looking for? Try adjusting your preferences 
          or explore different genres to discover new favorites!
        </p>
      </div>
    </div>
  );
};

export default Recommendations;