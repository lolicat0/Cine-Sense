import React, { useState } from 'react';
import Header from './components/Header';
import Questionnaire from './components/Questionnaire';
import Recommendations from './components/Recommendations';
import './styles/globals.css';

function App() {
  const [currentStep, setCurrentStep] = useState('questionnaire');
  const [recommendations, setRecommendations] = useState([]);
  const [userPreferences, setUserPreferences] = useState({});
  const [loading, setLoading] = useState(false);

  const handleQuestionnaireComplete = async (preferences) => {
    setLoading(true);
    setUserPreferences(preferences);
    
    try {
      // Call backend API for recommendations
      const response = await fetch('/api/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.recommendations);
        setCurrentStep('recommendations');
      } else {
        console.error('Failed to get recommendations');
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = () => {
    setCurrentStep('questionnaire');
    setRecommendations([]);
    setUserPreferences({});
  };

  return (
    <div className="App">
      <Header />
      <div className="container">
        <main className="main-content">
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p style={{ marginTop: '1rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                Finding perfect movies for you...
              </p>
            </div>
          )}
          
          {!loading && currentStep === 'questionnaire' && (
            <Questionnaire onComplete={handleQuestionnaireComplete} />
          )}
          
          {!loading && currentStep === 'recommendations' && (
            <Recommendations 
              movies={recommendations} 
              onRestart={handleRestart}
              preferences={userPreferences}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;