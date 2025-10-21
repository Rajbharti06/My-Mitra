import React, { useState, useEffect } from 'react';
import './MoodRing.css';

/**
 * MoodRing component - Displays user's emotional state as a visual ring
 * 
 * @param {Object} props
 * @param {string} props.emotion - Primary emotion (happy, sad, neutral, stressed, motivated)
 * @param {string} props.intensity - Intensity level (low, medium, high)
 * @param {number} props.size - Size of the mood ring in pixels
 * @param {boolean} props.animate - Whether to animate the mood ring
 * @param {boolean} props.showLabel - Whether to show the emotion label
 */
const MoodRing = ({ 
  emotion = 'neutral', 
  intensity = 'medium', 
  size = 60, 
  animate = true,
  showLabel = true
}) => {
  const [ringColor, setRingColor] = useState('#7A7A7A');
  const [pulseSpeed, setPulseSpeed] = useState('3s');
  
  // Map emotions to colors
  const emotionColors = {
    happy: '#FFD700',      // Gold
    sad: '#4169E1',        // Royal Blue
    neutral: '#7A7A7A',    // Gray
    stressed: '#FF4500',   // Red-Orange
    motivated: '#32CD32',  // Lime Green
    anxious: '#9932CC',    // Dark Orchid
    calm: '#48D1CC',       // Turquoise
    excited: '#FF1493',    // Deep Pink
    tired: '#8B4513',      // Saddle Brown
    focused: '#1E90FF'     // Dodger Blue
  };
  
  // Map intensity to pulse speed and color intensity
  const intensityMap = {
    low: { pulse: '4s', factor: 0.7 },
    medium: { pulse: '3s', factor: 1 },
    high: { pulse: '1.5s', factor: 1.3 }
  };
  
  // Adjust color based on intensity
  const adjustColorIntensity = (hexColor, factor) => {
    // Convert hex to RGB
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    // Adjust intensity (clamping to valid RGB values)
    const adjustR = Math.min(255, Math.max(0, Math.round(r * factor)));
    const adjustG = Math.min(255, Math.max(0, Math.round(g * factor)));
    const adjustB = Math.min(255, Math.max(0, Math.round(b * factor)));
    
    // Convert back to hex
    return `#${adjustR.toString(16).padStart(2, '0')}${adjustG.toString(16).padStart(2, '0')}${adjustB.toString(16).padStart(2, '0')}`;
  };
  
  useEffect(() => {
    // Set color based on emotion
    const baseColor = emotionColors[emotion] || emotionColors.neutral;
    const intensitySettings = intensityMap[intensity] || intensityMap.medium;
    
    // Adjust color based on intensity
    const adjustedColor = adjustColorIntensity(baseColor, intensitySettings.factor);
    
    setRingColor(adjustedColor);
    setPulseSpeed(intensitySettings.pulse);
  }, [emotion, intensity]);
  
  return (
    <div className="mood-ring-container" style={{ width: size, height: size }}>
      <div 
        className={`mood-ring ${animate ? 'pulse' : ''}`} 
        style={{ 
          backgroundColor: ringColor,
          width: size,
          height: size,
          animationDuration: pulseSpeed
        }}
      />
      {showLabel && (
        <div className="mood-label">
          <span className="emotion-text">{emotion}</span>
          <span className="intensity-dot" style={{ backgroundColor: ringColor }}></span>
        </div>
      )}
    </div>
  );
};

export default MoodRing;