import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const FloatingLeaves = ({ count = 5, enabled = true }) => {
  const [leaves, setLeaves] = useState([]);

  useEffect(() => {
    if (!enabled) return;

    const generateLeaves = () => {
      const newLeaves = [];
      for (let i = 0; i < count; i++) {
        newLeaves.push({
          id: i,
          x: Math.random() * window.innerWidth,
          delay: Math.random() * 10,
          duration: 15 + Math.random() * 10,
          size: 20 + Math.random() * 15,
          rotation: Math.random() * 360,
          opacity: 0.3 + Math.random() * 0.4,
          leaf: ['🍂', '🍃', '🍁'][Math.floor(Math.random() * 3)]
        });
      }
      setLeaves(newLeaves);
    };

    generateLeaves();
    
    // Regenerate leaves periodically
    const interval = setInterval(generateLeaves, 30000);
    return () => clearInterval(interval);
  }, [count, enabled]);

  if (!enabled) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {leaves.map((leaf) => (
        <motion.div
          key={leaf.id}
          className="absolute text-2xl select-none"
          style={{
            left: leaf.x,
            fontSize: `${leaf.size}px`,
            opacity: leaf.opacity,
          }}
          initial={{
            y: -50,
            rotate: leaf.rotation,
          }}
          animate={{
            y: window.innerHeight + 50,
            rotate: leaf.rotation + 360,
            x: leaf.x + (Math.sin(leaf.id) * 100),
          }}
          transition={{
            duration: leaf.duration,
            delay: leaf.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          {leaf.leaf}
        </motion.div>
      ))}
    </div>
  );
};

export default FloatingLeaves;