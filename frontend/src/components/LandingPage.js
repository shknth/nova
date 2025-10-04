import React from 'react';
import { motion } from 'framer-motion';
import BasicMetrics from './BasicMetrics';
import ChatInput from './ChatInput';
import './LandingPage.css';

const LandingPage = ({ onQuerySubmit }) => {
  const handleQuerySubmit = (query) => {
    onQuerySubmit(query);
  };

  return (
    <motion.div 
      className="landing-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="landing-container">
        <motion.div 
          className="landing-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <h1 className="landing-title">StratoSense</h1>
          <p className="landing-subtitle">
            Ask me anything about air quality and health recommendations
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <BasicMetrics />
        </motion.div>

        <motion.div 
          className="chat-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <div className="example-queries">
            <p className="example-label">Try asking:</p>
            <div className="example-items">
              <span className="example-item">
                "My son has asthma and wants to play in Maryland park at 2:00pm today. Is it okay?"
              </span>
              <span className="example-item">
                "Is it safe to go jogging this evening in downtown Dublin?"
              </span>
              <span className="example-item">
                "What's the air quality forecast for tomorrow morning?"
              </span>
            </div>
          </div>

          <ChatInput
            onSubmit={handleQuerySubmit}
            placeholder="Ask about air quality, health recommendations, or outdoor activities..."
          />
        </motion.div>

        <motion.div 
          className="landing-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <p>Powered by NASA Earth observation data and AI</p>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default LandingPage;
