// Environment Configuration
export const config = {
  // API Configuration
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  useMockData: process.env.REACT_APP_USE_MOCK_DATA === 'true' || process.env.NODE_ENV === 'development',
  
  // Development settings
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  
  // API Keys (if needed)
  nasaApiKey: process.env.REACT_APP_NASA_API_KEY,
  openaiApiKey: process.env.REACT_APP_OPENAI_API_KEY,
  
  // App settings
  appName: 'StratoSense',
  version: process.env.REACT_APP_VERSION || '1.0.0',
  
  // Timeouts and limits
  apiTimeout: 10000, // 10 seconds
  retryAttempts: 3,
  
  // Feature flags
  features: {
    darkMode: true,
    advancedDashboard: true,
    realTimeUpdates: false, // Enable when WebSocket is ready
    notifications: false    // Enable when push notifications are ready
  }
};

export default config;
