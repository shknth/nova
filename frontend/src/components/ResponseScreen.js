import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faChartBar, faRobot, faVolumeUp, faStop } from '@fortawesome/free-solid-svg-icons';
import { useTheme } from '../contexts/ThemeContext';
import ChatInput from './ChatInput';
import './ResponseScreen.css';

const ResponseScreen = ({ userQuery, aiResponse, statusCode, onViewDashboard, onNewQuery }) => {
  const { isDark } = useTheme();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synthRef = useRef(window.speechSynthesis);

  // Enable dashboard button only if status code is 200
  const isDashboardEnabled = statusCode === 200;

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  const handleTextToSpeech = () => {
    const synth = synthRef.current;

    if (isSpeaking) {
      // Stop speaking
      synth.cancel();
      setIsSpeaking(false);
    } else {
      // Start speaking
      if (!aiResponse) return;

      const utterance = new SpeechSynthesisUtterance(aiResponse);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Try to find British or Irish voice
      const voices = synth.getVoices();
      console.log('Available voices:', voices.map(v => `${v.name} (${v.lang})`));

      // Prioritize British English (en-GB) or Irish English (en-IE)
      const preferredVoice = voices.find(voice =>
        voice.lang === 'en-GB' || voice.lang === 'en-IE' ||
        voice.name.includes('British') || voice.name.includes('Irish') ||
        voice.name.includes('UK') || voice.name.includes('Daniel') ||
        voice.name.includes('Kate') || voice.name.includes('Serena')
      );

      if (preferredVoice) {
        utterance.voice = preferredVoice;
        console.log('Using voice:', preferredVoice.name);
      } else {
        console.log('No British/Irish voice found, using default');
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
      };

      synth.speak(utterance);
    }
  };

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
              <div className="ai-text-header">
                <p className="ai-text">{aiResponse || 'No response available'}</p>
                <button
                  className={`speaker-button ${isSpeaking ? 'speaking' : ''}`}
                  onClick={handleTextToSpeech}
                  title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
                >
                  <FontAwesomeIcon icon={isSpeaking ? faStop : faVolumeUp} />
                </button>
              </div>

              <motion.div
                className="action-buttons"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.5 }}
              >
                <button
                  className="dashboard-button primary"
                  onClick={onViewDashboard}
                  disabled={!isDashboardEnabled}
                  title={!isDashboardEnabled ? 'Dashboard unavailable - query processing failed' : 'View Dashboard'}
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