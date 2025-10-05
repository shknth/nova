import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';
import LandingPage from './components/LandingPage';
import ResponseScreen from './components/ResponseScreen';
import QueryDashboard from './components/QueryDashboard';
import AdvancedDashboard from './components/AdvancedDashboard';
import { extractParameters } from './services/apiService';

function App() {
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [userQuery, setUserQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleQuerySubmit = async (query) => {
    // Validate query input
    if (!query || typeof query !== 'string' || query.trim() === '') {
      console.error('Invalid query provided:', query);
      return;
    }

    setIsLoading(true);
    setUserQuery(query.trim());

    try {
      // Call the actual API endpoint
      const response = await extractParameters(query.trim());

      // Extract display_text from the response
      const displayText = response.display_text || "I couldn't process your query. Please try again.";

      setAiResponse(displayText);
      setCurrentScreen('response');
    } catch (error) {
      console.error('Error submitting query:', error);
      setAiResponse("I'm sorry, I encountered an error processing your request. Please try again.");
      setCurrentScreen('response');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDashboard = () => {
    setCurrentScreen('query-dashboard');
  };

  const handleAdvancedDashboard = () => {
    setCurrentScreen('advanced-dashboard');
  };

  const handleNewQuery = (newQuery) => {
    if (newQuery && typeof newQuery === 'string' && newQuery.trim()) {
      handleQuerySubmit(newQuery);
    } else {
      // Reset to landing page
      setCurrentScreen('landing');
      setUserQuery('');
      setAiResponse('');
    }
  };

  const handleBack = () => {
    switch (currentScreen) {
      case 'response':
        setCurrentScreen('landing');
        break;
      case 'query-dashboard':
        setCurrentScreen('response');
        break;
      case 'advanced-dashboard':
        setCurrentScreen('query-dashboard');
        break;
      default:
        setCurrentScreen('landing');
    }
  };

  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'landing':
        return (
          <LandingPage 
            onQuerySubmit={handleQuerySubmit}
          />
        );
      case 'response':
        return (
          <ResponseScreen
            userQuery={userQuery}
            aiResponse={aiResponse}
            onViewDashboard={handleViewDashboard}
            onNewQuery={handleNewQuery}
          />
        );
      case 'query-dashboard':
        return (
          <QueryDashboard
            userQuery={userQuery}
            onAdvancedDashboard={handleAdvancedDashboard}
            onBack={handleBack}
          />
        );
      case 'advanced-dashboard':
        return (
          <AdvancedDashboard
            onBack={handleBack}
          />
        );
      default:
        return <LandingPage onQuerySubmit={handleQuerySubmit} />;
    }
  };

  return (
    <ThemeProvider>
      <div className="App">
        {isLoading && (
          <motion.div 
            className="loading-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="loading-content">
              <div className="loading-spinner"></div>
              <p>Analyzing air quality data...</p>
            </div>
          </motion.div>
        )}
        
        <AnimatePresence mode="wait">
          <motion.div
            key={`${currentScreen}-${userQuery}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {renderCurrentScreen()}
          </motion.div>
        </AnimatePresence>
      </div>
    </ThemeProvider>
  );
}

export default App;