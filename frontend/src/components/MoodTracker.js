import React, { useState } from 'react';
import { motion } from 'framer-motion';

const moodEmojis = {
  'very_happy': { emoji: '😄', color: '#4caf50', label: 'Very Happy' },
  'happy': { emoji: '🙂', color: '#8bc34a', label: 'Happy' },
  'neutral': { emoji: '😐', color: '#ffc107', label: 'Neutral' },
  'sad': { emoji: '😔', color: '#ff9800', label: 'Sad' },
  'very_sad': { emoji: '😢', color: '#f44336', label: 'Very Sad' },
};

const questions = [
  {
    id: 'sleep',
    question: 'How well did you sleep last night?',
    options: [
      { value: 5, label: 'Very well' },
      { value: 4, label: 'Well' },
      { value: 3, label: 'Average' },
      { value: 2, label: 'Poorly' },
      { value: 1, label: 'Very poorly' },
    ]
  },
  {
    id: 'stress',
    question: 'How would you rate your stress level today?',
    options: [
      { value: 1, label: 'Very high' },
      { value: 2, label: 'High' },
      { value: 3, label: 'Moderate' },
      { value: 4, label: 'Low' },
      { value: 5, label: 'Very low' },
    ]
  },
  {
    id: 'energy',
    question: 'How is your energy level today?',
    options: [
      { value: 5, label: 'Very energetic' },
      { value: 4, label: 'Energetic' },
      { value: 3, label: 'Average' },
      { value: 2, label: 'Tired' },
      { value: 1, label: 'Very tired' },
    ]
  },
  {
    id: 'social',
    question: 'How satisfied are you with your social interactions today?',
    options: [
      { value: 5, label: 'Very satisfied' },
      { value: 4, label: 'Satisfied' },
      { value: 3, label: 'Neutral' },
      { value: 2, label: 'Dissatisfied' },
      { value: 1, label: 'Very dissatisfied' },
    ]
  },
  {
    id: 'productivity',
    question: 'How productive do you feel today?',
    options: [
      { value: 5, label: 'Very productive' },
      { value: 4, label: 'Productive' },
      { value: 3, label: 'Average' },
      { value: 2, label: 'Unproductive' },
      { value: 1, label: 'Very unproductive' },
    ]
  }
];

function MoodTracker({ onSubmit }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [mood, setMood] = useState(null);
  const [showResults, setShowResults] = useState(false);

  const handleMoodSelect = (moodKey) => {
    setMood(moodKey);
    setStep(1);
  };

  const analyzeMood = (finalAnswers) => {
    const usedAnswers = finalAnswers || answers;
    const { avgScore, feedback, suggestions } = getMoodAnalysis(usedAnswers);

    const results = {
      mood,
      answers: usedAnswers,
      avgScore,
      feedback,
      suggestions,
      timestamp: new Date().toISOString()
    };

    if (onSubmit) {
      onSubmit(results);
    }

    // ensure latest answers are in state before showing results
    setAnswers(usedAnswers);
    setShowResults(true);
  };

  const handleAnswer = (questionId, value) => {
    const nextAnswers = { ...answers, [questionId]: value };
    setAnswers(nextAnswers);

    if (step < questions.length) {
      setStep(step + 1);
    } else {
      analyzeMood(nextAnswers);
    }
  };

  const resetTracker = () => {
    setStep(0);
    setAnswers({});
    setMood(null);
    setShowResults(false);
  };

  if (showResults) {
    const { avgScore, feedback, suggestions } = getMoodAnalysis(answers);
    let moodResult;

    if (avgScore >= 4.5) moodResult = 'very_happy';
    else if (avgScore >= 3.5) moodResult = 'happy';
    else if (avgScore >= 2.5) moodResult = 'neutral';
    else if (avgScore >= 1.5) moodResult = 'sad';
    else moodResult = 'very_sad';

    return (
      <div style={containerStyle}>
        <h2 style={{ color: '#204b72', marginBottom: 20 }}>Your Mood Analysis</h2>

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ 
            fontSize: 48, 
            marginRight: 16, 
            backgroundColor: moodEmojis[moodResult].color,
            width: 80,
            height: 80,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%'
          }}>
            {moodEmojis[moodResult].emoji}
          </div>
          <div>
            <h3 style={{ margin: 0 }}>Today you're feeling: {moodEmojis[moodResult].label}</h3>
            <p style={{ margin: '8px 0 0 0' }}>Score: {avgScore.toFixed(1)} / 5</p>
          </div>
        </div>

        <div style={{ 
          padding: 16, 
          backgroundColor: '#f5f7fa', 
          borderRadius: 12, 
          marginBottom: 20 
        }}>
          <h3 style={{ marginTop: 0 }}>Feedback</h3>
          <p>{feedback}</p>
        </div>

        <div style={{ marginBottom: 20 }}>
          <h3>Suggestions to improve your day:</h3>
          <ul style={{ paddingLeft: 20 }}>
            {suggestions.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </div>

        <button 
          onClick={resetTracker}
          style={{
            padding: '10px 16px',
            backgroundColor: '#3a6ea5',
            color: 'white',
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Track New Mood
        </button>
      </div>
    );
  }

  if (step === 0) {
    return (
      <div style={containerStyle}>
        <h2 style={{ color: '#204b72', marginBottom: 20 }}>How are you feeling today?</h2>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 30 }}>
          {Object.entries(moodEmojis).map(([key, { emoji, color, label }]) => (
            <button
              key={key}
              onClick={() => handleMoodSelect(key)}
              style={{
                fontSize: 32,
                backgroundColor: color,
                width: 60,
                height: 60,
                borderRadius: '50%',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              {emoji}
            </button>
          ))}
        </div>
        <div style={{ textAlign: 'center', fontSize: 14, color: '#666' }}>
          Select an emoji that best represents your mood
        </div>
      </div>
    );
  }

  const currentQuestion = questions[step - 1];
  
  return (
    <div style={containerStyle}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ color: '#666', fontSize: 14 }}>Question {step} of {questions.length}</span>
          <span style={{ color: '#666', fontSize: 14 }}>
            {Math.round((step / questions.length) * 100)}% complete
          </span>
        </div>
        <div style={{ 
          height: 6, 
          backgroundColor: '#e0e0e0', 
          borderRadius: 3, 
          overflow: 'hidden' 
        }}>
          <div style={{ 
            height: '100%', 
            width: `${(step / questions.length) * 100}%`, 
            backgroundColor: '#3a6ea5',
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>
      
      <h3 style={{ color: '#204b72', marginBottom: 20 }}>{currentQuestion.question}</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {currentQuestion.options.map((option) => (
          <button
            key={option.value}
            onClick={() => handleAnswer(currentQuestion.id, option.value)}
            style={{
              padding: '12px 16px',
              backgroundColor: 'white',
              border: '1px solid #cdd6e1',
              borderRadius: 8,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'background-color 0.2s',
              display: 'flex',
              alignItems: 'center'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f7fa'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'white'}
          >
            <div style={{ 
              width: 20, 
              height: 20, 
              borderRadius: '50%', 
              border: '2px solid #3a6ea5',
              marginRight: 12,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {answers[currentQuestion.id] === option.value && (
                <div style={{ 
                  width: 12, 
                  height: 12, 
                  borderRadius: '50%', 
                  backgroundColor: '#3a6ea5' 
                }} />
              )}
            </div>
            {option.label}
          </button>
        ))}
      </div>
      
      {step > 1 && (
        <button
          onClick={() => setStep(step - 1)}
          style={{
            marginTop: 20,
            padding: '8px 16px',
            backgroundColor: 'transparent',
            color: '#3a6ea5',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          ← Previous Question
        </button>
      )}
      
      {step === questions.length && (
        <button
          onClick={() => analyzeMood()}
          style={{
            marginTop: 20,
            padding: '10px 16px',
            backgroundColor: '#3a6ea5',
            color: 'white',
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            fontWeight: 'bold',
            float: 'right'
          }}
        >
          Complete & View Results
        </button>
      )}
    </div>
  );
}

const containerStyle = {
  maxWidth: 600,
  margin: '0 auto',
  padding: 24,
  backgroundColor: 'white',
  borderRadius: 16,
  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
  border: '1px solid #e6e9ef'
};

export default MoodTracker;

// Add dynamic feedback generator based on answers
const getMoodAnalysis = (answers) => {
  const keys = ['sleepQuality','stressLevel','energyLevel','socialInteraction','productivity'];
  const vals = keys.map(k => answers[k]).filter(v => typeof v === 'number');
  const avg = vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : 0;
  const avgScore = Number(avg.toFixed(1));
  // Find lowest dimension for targeted tip
  let lowestKey = null; let lowestVal = Infinity;
  keys.forEach(k => { const v = answers[k]; if (typeof v === 'number' && v < lowestVal) { lowestVal = v; lowestKey = k; } });
  const labelMap = {
    sleepQuality: 'sleep', stressLevel: 'stress', energyLevel: 'energy', socialInteraction: 'social', productivity: 'productivity'
  };
  let feedback = '';
  let suggestions = [];
  if (avgScore >= 4.5) {
    feedback = "You're on a great streak today — keep it up!";
    suggestions = ["Maintain routines that work for you","Consider sharing your wins in Journal"];
  } else if (avgScore >= 3.5) {
    feedback = "Overall good day with a few areas to polish.";
    suggestions = ["Pick one small improvement for tomorrow","Plan a 10-minute reset if needed"];
  } else if (avgScore >= 2.5) {
    feedback = "Mixed signals — take a moment to rebalance.";
    suggestions = ["Try a short walk or breathing exercise","Write a quick reflection in Journal"];
  } else {
    feedback = "Tough day — be kind to yourself and rest.";
    suggestions = ["Reach out to someone you trust","Prioritize sleep and hydration"];
  }
  if (lowestKey) {
    const area = labelMap[lowestKey];
    suggestions.unshift(`Focus gently on ${area} — it's lowest today`);
  }
  return { avgScore, feedback, suggestions };
};