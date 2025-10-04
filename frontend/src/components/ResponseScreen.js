import React from 'react';
import { motion } from 'framer-motion';
import ChatInput from './ChatInput';
import './ResponseScreen.css';

const ResponseScreen = ({ userQuery, aiResponse, onViewDashboard, onNewQuery }) => {
  return (
    <motion.div 
      className="response-screen"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="response-container">
        <motion.div 
          className="response-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <button 
            className="back-button"
            onClick={onNewQuery}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19 12H5M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            New Query
          </button>
          <h1 className="response-title">StratoSense</h1>
        </motion.div>

        <div className="chat-conversation">
          <motion.div 
            className="message user-message"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <div className="message-avatar user-avatar">
              <span>You</span>
            </div>
            <div className="message-content">
              <p>{userQuery || 'No query provided'}</p>
            </div>
          </motion.div>

          <motion.div 
            className="message ai-message"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <div className="message-avatar ai-avatar">
              <span>🤖</span>
            </div>
            <div className="message-content">
              <p>{aiResponse || 'No response available'}</p>
              
              <motion.div 
                className="action-buttons"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.5 }}
              >
                <button 
                  className="dashboard-button primary"
                  onClick={onViewDashboard}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2"/>
                    <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2"/>
                    <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2"/>
                    <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  View Dashboard
                </button>
              </motion.div>
            </div>
          </motion.div>
        </div>

        <motion.div 
          className="new-query-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.5 }}
        >
          <p className="new-query-label">Ask another question:</p>
          <ChatInput
            onSubmit={onNewQuery}
            placeholder="Ask about air quality, health recommendations, or outdoor activities..."
          />
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ResponseScreen;
