import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Quote } from 'lucide-react';

const quotes = [
  {
    text: "The only way to do great work is to love what you do.",
    author: "Steve Jobs"
  },
  {
    text: "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    author: "Winston Churchill"
  },
  {
    text: "The future belongs to those who believe in the beauty of their dreams.",
    author: "Eleanor Roosevelt"
  },
  {
    text: "It is during our darkest moments that we must focus to see the light.",
    author: "Aristotle"
  },
  {
    text: "The only impossible journey is the one you never begin.",
    author: "Tony Robbins"
  },
  {
    text: "In the middle of difficulty lies opportunity.",
    author: "Albert Einstein"
  },
  {
    text: "Believe you can and you're halfway there.",
    author: "Theodore Roosevelt"
  },
  {
    text: "The way to get started is to quit talking and begin doing.",
    author: "Walt Disney"
  }
];

const QuoteCard = ({ autoRotate = true, rotateInterval = 10000 }) => {
  const [currentQuoteIndex, setCurrentQuoteIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (!autoRotate) return;

    const interval = setInterval(() => {
      setIsVisible(false);
      setTimeout(() => {
        setCurrentQuoteIndex((prev) => (prev + 1) % quotes.length);
        setIsVisible(true);
      }, 300);
    }, rotateInterval);

    return () => clearInterval(interval);
  }, [autoRotate, rotateInterval]);

  const currentQuote = quotes[currentQuoteIndex];

  const nextQuote = () => {
    setIsVisible(false);
    setTimeout(() => {
      setCurrentQuoteIndex((prev) => (prev + 1) % quotes.length);
      setIsVisible(true);
    }, 300);
  };

  return (
    <motion.div
      className="bg-gradient-to-br from-soft-white to-card-light dark:from-gray-800 dark:to-gray-700 
                 rounded-2xl p-6 shadow-soft hover:shadow-warm transition-all duration-300 
                 border border-gray-100 dark:border-gray-600 cursor-pointer group"
      onClick={nextQuote}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-start space-x-3">
        <motion.div
          className="flex-shrink-0 p-2 bg-warm-brown/10 dark:bg-dark-accent/10 rounded-full"
          whileHover={{ rotate: 15 }}
          transition={{ duration: 0.2 }}
        >
          <Quote className="w-5 h-5 text-warm-brown dark:text-dark-accent" />
        </motion.div>
        
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            {isVisible && (
              <motion.div
                key={currentQuoteIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
              >
                <blockquote className="text-sm font-medium text-gray-700 dark:text-gray-200 leading-relaxed mb-3">
                  "{currentQuote.text}"
                </blockquote>
                <cite className="text-xs text-warm-brown dark:text-dark-accent font-semibold">
                  — {currentQuote.author}
                </cite>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      
      {/* Progress indicator */}
      <div className="flex justify-center mt-4 space-x-1">
        {quotes.map((_, index) => (
          <motion.div
            key={index}
            className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${
              index === currentQuoteIndex 
                ? 'bg-warm-brown dark:bg-dark-accent' 
                : 'bg-gray-300 dark:bg-gray-600'
            }`}
            whileHover={{ scale: 1.2 }}
          />
        ))}
      </div>
      
      {/* Hover hint */}
      <motion.p
        className="text-xs text-center text-gray-400 dark:text-gray-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
      >
        Click for next quote
      </motion.p>
    </motion.div>
  );
};

export default QuoteCard;