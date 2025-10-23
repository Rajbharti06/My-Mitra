import React, { useState, useEffect } from 'react';
import './EmotionDashboard.css';
import MoodRing from './MoodRing';

/**
 * EmotionDashboard component - Displays user's emotional trends and insights
 * 
 * @param {Object} props
 * @param {string} props.userId - User ID for fetching emotion data
 */
const EmotionDashboard = ({ userId }) => {
  const [emotionHistory, setEmotionHistory] = useState([]);
  const [emotionInsights, setEmotionInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('week');
  
  useEffect(() => {
    // Fetch emotion history and insights when component mounts or timeRange changes
    const fetchEmotionData = async () => {
      setIsLoading(true);
      try {
        // Fetch emotion history
        const historyResponse = await fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1'}/emotions/history?time_range=${timeRange}`);
        const historyData = await historyResponse.json();
        setEmotionHistory(historyData.records || []);
        
        // Fetch emotion insights
        const insightsResponse = await fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1'}/emotions/insights?time_range=${timeRange}`);
        const insightsData = await insightsResponse.json();
        setEmotionInsights(insightsData);
      } catch (error) {
        console.error('Error fetching emotion data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchEmotionData();
  }, [timeRange, userId]);
  
  // Calculate emotion distribution for visualization
  const getEmotionDistribution = () => {
    if (!emotionHistory.length) return {};
    
    const distribution = {};
    emotionHistory.forEach(record => {
      const emotion = record.primary_emotion;
      distribution[emotion] = (distribution[emotion] || 0) + 1;
    });
    
    return distribution;
  };
  
  const renderEmotionDistribution = () => {
    const distribution = getEmotionDistribution();
    const emotions = Object.keys(distribution);
    
    if (!emotions.length) return <p>No emotion data available</p>;
    
    return (
      <div className="emotion-distribution">
        {emotions.map(emotion => (
          <div key={emotion} className="emotion-bar">
            <div className="emotion-label">
              <MoodRing emotion={emotion} size={24} showLabel={true} />
            </div>
            <div className="bar-container">
              <div 
                className="bar-fill" 
                style={{ 
                  width: `${(distribution[emotion] / emotionHistory.length) * 100}%`,
                  backgroundColor: getEmotionColor(emotion)
                }}
              />
            </div>
            <div className="bar-value">{distribution[emotion]}</div>
          </div>
        ))}
      </div>
    );
  };
  
  // Helper function to get color for emotion
  const getEmotionColor = (emotion) => {
    const colors = {
      happy: '#FFD700',
      sad: '#4169E1',
      neutral: '#7A7A7A',
      stressed: '#FF4500',
      motivated: '#32CD32',
      anxious: '#9932CC',
      calm: '#48D1CC',
      excited: '#FF1493',
      tired: '#8B4513',
      focused: '#1E90FF'
    };
    
    return colors[emotion] || '#7A7A7A';
  };
  
  return (
    <div className="emotion-dashboard">
      <div className="dashboard-header">
        <h2>Emotion Insights</h2>
        <div className="time-range-selector">
          <button 
            className={timeRange === 'day' ? 'active' : ''} 
            onClick={() => setTimeRange('day')}
          >
            Today
          </button>
          <button 
            className={timeRange === 'week' ? 'active' : ''} 
            onClick={() => setTimeRange('week')}
          >
            Week
          </button>
          <button 
            className={timeRange === 'month' ? 'active' : ''} 
            onClick={() => setTimeRange('month')}
          >
            Month
          </button>
        </div>
      </div>
      
      {isLoading ? (
        <div className="loading">Loading emotion data...</div>
      ) : (
        <div className="dashboard-content">
          {emotionInsights && (
            <div className="insight-card">
              <h3>Emotional Insight</h3>
              <p>{emotionInsights.insight_text}</p>
              {emotionInsights.dominant_emotion && (
                <div className="dominant-emotion">
                  <span>Dominant emotion:</span>
                  <MoodRing 
                    emotion={emotionInsights.dominant_emotion} 
                    size={32} 
                    showLabel={true}
                  />
                </div>
              )}
            </div>
          )}
          
          <div className="emotion-trends">
            <h3>Emotion Distribution</h3>
            {renderEmotionDistribution()}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmotionDashboard;