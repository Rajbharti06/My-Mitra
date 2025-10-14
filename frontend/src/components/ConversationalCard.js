import React from 'react';
import './ConversationalCard.css'; // We'll create this CSS file next

const ConversationalCard = ({ type, data }) => {
  switch (type) {
    case 'habit_suggestion':
      return (
        <div className="conversational-card habit-suggestion-card">
          <h3>New Habit Idea!</h3>
          <p>{data.title}</p>
          <p className="description">{data.description}</p>
          <button className="card-button">Add Habit</button>
        </div>
      );
    case 'journal_prompt':
      return (
        <div className="conversational-card journal-prompt-card">
          <h3>Journal Prompt</h3>
          <p>{data.prompt}</p>
          <button className="card-button">Write Entry</button>
        </div>
      );
    case 'insight_summary':
      return (
        <div className="conversational-card insight-summary-card">
          <h3>Your Insight</h3>
          <p>{data.summary}</p>
          <button className="card-button">View Details</button>
        </div>
      );
    case 'mood_tracker':
      return (
        <div className="conversational-card mood-tracker-card">
          <h3>How are you feeling today?</h3>
          <div className="mood-options">
            {['😊 Happy', '😐 Neutral', '😔 Sad', '😠 Angry', '😟 Anxious'].map(mood => (
              <button key={mood} className="mood-button">{mood}</button>
            ))}
          </div>
        </div>
      );
    default:
      return null;
  }
};

export default ConversationalCard;