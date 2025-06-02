import React, { useState } from 'react';

const Questionnaire = ({ onComplete }) => {
  const [answers, setAnswers] = useState({
    genres: [],
    mood: '',
    language: '',
    decade: '',
    duration: '',
    rating: '',
    actors: '',
    directors: '',
    keywords: ''
  });

  const [currentQuestion, setCurrentQuestion] = useState(0);

  const questions = [
    {
      id: 'genres',
      title: 'What genres do you enjoy? (Select multiple)',
      type: 'multiple',
      options: [
        'Action', 'Adventure', 'Comedy', 'Drama', 'Horror', 'Romance',
        'Sci-Fi', 'Fantasy', 'Thriller', 'Mystery', 'Documentary', 'Animation'
      ]
    },
    {
      id: 'mood',
      title: 'What\'s your current mood?',
      type: 'single',
      options: [
        'Excited & Energetic', 'Relaxed & Chill', 'Thoughtful & Deep',
        'Romantic & Emotional', 'Adventurous & Bold', 'Nostalgic & Warm'
      ]
    },
    {
      id: 'language',
      title: 'Preferred language?',
      type: 'single',
      options: [
        'English', 'Spanish', 'French', 'Japanese', 'Korean', 'Hindi',
        'Mandarin', 'Italian', 'German', 'Any Language'
      ]
    },
    {
      id: 'decade',
      title: 'Preferred time period?',
      type: 'single',
      options: [
        '2020s', '2010s', '2000s', '1990s', '1980s', '1970s',
        'Classic (Before 1970)', 'No Preference'
      ]
    },
    {
      id: 'duration',
      title: 'How much time do you have?',
      type: 'single',
      options: [
        'Short (< 90 min)', 'Medium (90-120 min)', 'Long (120-180 min)',
        'Epic (> 180 min)', 'No Preference'
      ]
    },
    {
      id: 'rating',
      title: 'Content rating preference?',
      type: 'single',
      options: ['G', 'PG', 'PG-13', 'R', 'No Preference']
    },
    {
      id: 'actors',
      title: 'Favorite actors? (Optional)',
      type: 'text',
      placeholder: 'e.g., Leonardo DiCaprio, Meryl Streep'
    },
    {
      id: 'directors',
      title: 'Favorite directors? (Optional)',
      type: 'text',
      placeholder: 'e.g., Christopher Nolan, Greta Gerwig'
    },
    {
      id: 'keywords',
      title: 'Any specific themes or keywords?',
      type: 'text',
      placeholder: 'e.g., space exploration, family drama, superhero'
    }
  ];

  const handleAnswer = (questionId, value) => {
    if (questions[currentQuestion].type === 'multiple') {
      const currentValues = answers[questionId] || [];
      const newValues = currentValues.includes(value)
        ? currentValues.filter(v => v !== value)
        : [...currentValues, value];
      
      setAnswers(prev => ({
        ...prev,
        [questionId]: newValues
      }));
    } else {
      setAnswers(prev => ({
        ...prev,
        [questionId]: value
      }));
    }
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      onComplete(answers);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const isAnswered = () => {
    const question = questions[currentQuestion];
    const answer = answers[question.id];
    
    if (question.type === 'multiple') {
      return answer && answer.length > 0;
    } else if (question.type === 'text') {
      return true; // Text questions are optional
    } else {
      return answer && answer.length > 0;
    }
  };

  const question = questions[currentQuestion];

  return (
    <div className="questionnaire fade-in">
      <div className="question-progress" style={{ marginBottom: '2rem' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '1rem'
        }}>
          <h2 style={{ color: '#d946ef', fontSize: '1.5rem' }}>
            Question {currentQuestion + 1} of {questions.length}
          </h2>
          <div style={{ 
            background: 'rgba(139, 69, 193, 0.2)', 
            padding: '0.5rem 1rem', 
            borderRadius: '20px',
            fontSize: '0.9rem'
          }}>
            {Math.round(((currentQuestion + 1) / questions.length) * 100)}% Complete
          </div>
        </div>
        
        <div style={{ 
          background: 'rgba(139, 69, 193, 0.2)', 
          height: '4px', 
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{ 
            background: 'linear-gradient(45deg, #8b45c1, #d946ef)',
            height: '100%',
            width: `${((currentQuestion + 1) / questions.length) * 100}%`,
            transition: 'width 0.3s ease'
          }}></div>
        </div>
      </div>

      <div className="question-card">
        <h3 className="question-title">{question.title}</h3>
        
        {question.type === 'text' ? (
          <input
            type="text"
            className="input-field"
            placeholder={question.placeholder}
            value={answers[question.id] || ''}
            onChange={(e) => handleAnswer(question.id, e.target.value)}
          />
        ) : (
          <div className="question-options">
            {question.options.map((option) => {
              const isSelected = question.type === 'multiple' 
                ? (answers[question.id] || []).includes(option)
                : answers[question.id] === option;
                
              return (
                <button
                  key={option}
                  className={`option-button ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleAnswer(question.id, option)}
                >
                  {option}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        marginTop: '2rem' 
      }}>
        <button
          className="btn-primary"
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
          style={{ 
            opacity: currentQuestion === 0 ? 0.5 : 1,
            background: currentQuestion === 0 ? 'rgba(139, 69, 193, 0.3)' : undefined
          }}
        >
          Previous
        </button>
        
        <button
          className="btn-primary"
          onClick={handleNext}
          disabled={!isAnswered() && question.type !== 'text'}
        >
          {currentQuestion === questions.length - 1 ? 'Get Recommendations' : 'Next'}
        </button>
      </div>
    </div>
  );
};

export default Questionnaire;