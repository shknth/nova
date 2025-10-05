import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';
import LandingPage from './components/LandingPage';
import ResponseScreen from './components/ResponseScreen';
import QueryDashboard from './components/QueryDashboard';
import AdvancedDashboard from './components/AdvancedDashboard';

function App() {
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [userQuery, setUserQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Mock AI response generator - will be replaced with actual API call
  const generateAIResponse = (query) => {
    // Ensure query is a string
    if (!query || typeof query !== 'string') {
      return "I'm sorry, I didn't receive a valid question. Please try asking again.";
    }

    const responses = {
      asthma: "Based on current air quality conditions, the PM2.5 and ozone levels are moderately elevated in your area. For individuals with asthma, I recommend avoiding outdoor activities during peak pollution hours (2-4 PM). Consider indoor activities or wait until evening when air quality typically improves.",
      jogging: "The current air quality is good for outdoor exercise. PM2.5 levels are within safe ranges, and ozone concentrations are low. This is an excellent time for jogging or other outdoor activities.",
      children: "Air quality conditions are currently suitable for children's outdoor play. However, I recommend monitoring sensitive individuals and limiting strenuous activities if they show any respiratory discomfort.",
      default: "Based on current air quality data, conditions are generally acceptable for most outdoor activities. However, sensitive individuals should monitor their symptoms and consider limiting prolonged outdoor exposure during peak pollution hours."
    };

    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('asthma')) return responses.asthma;
    if (lowerQuery.includes('jog') || lowerQuery.includes('run')) return responses.jogging;
    if (lowerQuery.includes('child') || lowerQuery.includes('kid') || lowerQuery.includes('son') || lowerQuery.includes('daughter')) return responses.children;
    return responses.default;
  };

  const handleQuerySubmit = async (query) => {
    // Validate query input
    if (!query || typeof query !== 'string' || query.trim() === '') {
      console.error('Invalid query provided:', query);
      return;
    }

    setIsLoading(true);
    setUserQuery(query.trim());
    
    // Simulate API call delay
    setTimeout(() => {
      const response = generateAIResponse(query.trim());
      setAiResponse(response);
      setCurrentScreen('response');
      setIsLoading(false);
    }, 1500);
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
        {/* Atmospheric particles for enhanced depth */}
        <div className="atmospheric-particles"></div>
        
        {/* Temporary test element to verify changes are loading */}
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          background: 'rgba(255, 0, 0, 0.8)',
          color: 'white',
          padding: '5px 10px',
          borderRadius: '5px',
          fontSize: '12px',
          zIndex: 9999
        }}>
          ✨ Cloudy UI Active
        </div>
        
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