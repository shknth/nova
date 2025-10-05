import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import { useTheme } from '../contexts/ThemeContext';
import './ChatInput.css';

const ChatInput = ({ onSubmit, placeholder, disabled = false }) => {
  const [query, setQuery] = useState('');
  const { isDark } = useTheme();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !disabled) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const textareaStyle = {
    color: isDark ? '#ffffff' : '#1e3a8a',
  };

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="input-container">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          className="chat-textarea"
          disabled={disabled}
          rows={3}
          style={textareaStyle}
        />
        <button 
          type="submit" 
          className={`submit-button ${!query.trim() || disabled ? 'disabled' : ''}`}
          disabled={!query.trim() || disabled}
        >
          <FontAwesomeIcon icon={faPaperPlane} />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;