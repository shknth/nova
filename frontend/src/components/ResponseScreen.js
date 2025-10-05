import React from 'react';
import { motion } from 'framer-motion';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faChartBar, faRobot } from '@fortawesome/free-solid-svg-icons';
import { useTheme } from '../contexts/ThemeContext';
import ChatInput from './ChatInput';
import './ResponseScreen.css';

const ResponseScreen = ({ userQuery, aiResponse, onViewDashboard, onNewQuery }) => {
  const { isDark } = useTheme();

  return (
    <motion.div 
      className="response-screen"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      data-theme={isDark ? 'dark' : 'light'}
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
            <FontAwesomeIcon icon={faArrowLeft} />
            New Query
          </button>
          <h1 className="response-title">NOVA</h1>
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
              <FontAwesomeIcon icon={faRobot} />
            </div>
            <div className="message-content ai-content">
              <p className="ai-text">{aiResponse || 'No response available'}</p>
              
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
                  <FontAwesomeIcon icon={faChartBar} />
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