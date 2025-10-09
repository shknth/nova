import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for AI processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens, etc.
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // Handle common error cases
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      // Redirect to login if needed
    }
    
    return Promise.reject(error);
  }
);

// API Service Class
class ApiService {
  // Health check
  async healthCheck() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('API health check failed');
    }
  }

  // AI Chat API
  async submitQuery(query) {
    try {
      const response = await apiClient.post('/chat/query', { query });
      return response.data;
    } catch (error) {
      throw new Error('Failed to process query');
    }
  }

  // Air Quality Data APIs
  async getCurrentAirQuality(location = null) {
    try {
      const params = location ? { location } : {};
      const response = await apiClient.get('/air-quality/current', { params });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch current air quality data');
    }
  }

  async getAirQualityForecast(location = null, days = 7) {
    try {
      const params = { days };
      if (location) params.location = location;
      
      const response = await apiClient.get('/air-quality/forecast', { params });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch air quality forecast');
    }
  }

  async getQuerySpecificData(query) {
    try {
      const response = await apiClient.post('/air-quality/query-analysis', { query });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch query-specific data');
    }
  }

  // Pollutant Data APIs
  async getPollutantData(location = null) {
    try {
      const params = location ? { location } : {};
      const response = await apiClient.get('/pollutants', { params });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch pollutant data');
    }
  }

  // Health Impact APIs
  async getHealthImpactData(location = null, conditions = []) {
    try {
      const response = await apiClient.post('/health/impact', { 
        location, 
        conditions 
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch health impact data');
    }
  }

  // Regional Data APIs
  async getRegionalData(bounds = null) {
    try {
      const params = bounds ? { bounds } : {};
      const response = await apiClient.get('/air-quality/regional', { params });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch regional data');
    }
  }

  // Model Prediction APIs
  async getPredictions(features) {
    try {
      const response = await apiClient.post('/model/predict', { features });
      return response.data;
    } catch (error) {
      throw new Error('Failed to get model predictions');
    }
  }

  async getModelInfo() {
    try {
      const response = await apiClient.get('/model/info');
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch model information');
    }
  }

  // Weather Metrics API for frontend
  async getWeatherMetrics(location = null) {
    try {
      const params = location ? { location } : {};
      const response = await apiClient.get('/weather-metrics', { params });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch weather metrics');
    }
  }

  // Extract Parameters API - main query endpoint
  async extractParameters(prompt) {
    try {
      const response = await apiClient.post('/extract-parameters', { prompt });
      // Return both data and status code
      return {
        ...response.data,
        statusCode: response.status
      };
    } catch (error) {
      throw new Error('Failed to extract parameters from query');
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export individual methods for convenience
export const {
  healthCheck,
  submitQuery,
  getCurrentAirQuality,
  getAirQualityForecast,
  getQuerySpecificData,
  getPollutantData,
  getHealthImpactData,
  getRegionalData,
  getPredictions,
  getModelInfo,
  getWeatherMetrics,
  extractParameters
} = apiService;

export default apiService;
