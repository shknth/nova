import { apiService } from './apiService';

// Configuration for development mode
const USE_MOCK_DATA = process.env.REACT_APP_USE_MOCK_DATA === 'true' || process.env.NODE_ENV === 'development';

// Mock Data Generators
const mockData = {
  // Generate AI response based on query
  generateAIResponse(query) {
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
  },

  // Generate current air quality data
  generateCurrentAirQuality() {
    return {
      current: {
        aqi: 42,
        category: 'Good',
        location: 'Current Location',
        timestamp: new Date().toISOString(),
        pollutants: {
          pm25: 10.2,
          pm10: 18.5,
          o3: 35.1,
          no2: 12.3,
          so2: 2.1,
          co: 0.8
        }
      }
    };
  },

  // Generate forecast data
  generateForecast(days = 7) {
    const forecast = [];
    const baseAqi = 42;
    
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      
      forecast.push({
        date: i === 0 ? 'Today' : i === 1 ? 'Tomorrow' : `Day ${i + 1}`,
        fullDate: date.toISOString().split('T')[0],
        aqi: baseAqi + Math.sin(i * 0.5) * 10 + Math.random() * 8,
        category: 'Good', // This would be calculated based on AQI
        temperature: 20 + Math.sin(i * 0.3) * 5,
        humidity: 60 + Math.sin(i * 0.2) * 15
      });
    }
    
    return { forecast };
  },

  // Generate query-specific data
  generateQuerySpecificData(query) {
    const queryString = query && typeof query === 'string' ? query.toLowerCase() : '';
    
    // Extract location from query
    const location = queryString.includes('maryland') ? 'Maryland Park' :
                    queryString.includes('dublin') ? 'Dublin' :
                    queryString.includes('cork') ? 'Cork' : 'Current Location';
    
    // Generate hourly data
    const timeData = [];
    for (let i = 12; i < 19; i++) {
      timeData.push({
        time: `${i}:00`,
        aqi: 38 + Math.sin(i * 0.3) * 8 + Math.random() * 4,
        pm25: 8 + Math.sin(i * 0.2) * 3 + Math.random() * 2
      });
    }

    return {
      location,
      currentAQI: 42,
      healthRisk: queryString.includes('asthma') ? 'Moderate Risk' : 'Low Risk',
      recommendation: queryString.includes('asthma') ? 
        'Consider indoor activities or wait for better air quality' :
        'Safe for outdoor activities',
      timeData,
      pollutants: {
        pm25: { value: 12.5, risk: queryString.includes('asthma') ? 'High' : 'Moderate' },
        pm10: { value: 18.2, risk: 'Low' },
        o3: { value: 35.8, risk: queryString.includes('asthma') ? 'Moderate' : 'Low' },
        no2: { value: 15.3, risk: 'Low' }
      },
      mapCenter: queryString.includes('dublin') ? [53.3498, -6.2603] : [39.8283, -98.5795]
    };
  },

  // Generate regional data
  generateRegionalData() {
    return [
      { id: 1, lat: 53.3498, lng: -6.2603, aqi: 42, location: 'Dublin', pm25: 12.5, pm10: 18.2, o3: 35.8, no2: 15.3 },
      { id: 2, lat: 53.2707, lng: -9.0568, aqi: 38, location: 'Galway', pm25: 10.1, pm10: 15.8, o3: 32.1, no2: 12.8 },
      { id: 3, lat: 52.6680, lng: -8.6305, aqi: 55, location: 'Limerick', pm25: 15.2, pm10: 22.1, o3: 42.3, no2: 18.7 },
      { id: 4, lat: 51.8985, lng: -8.4756, aqi: 48, location: 'Cork', pm25: 13.8, pm10: 19.5, o3: 38.9, no2: 16.2 }
    ];
  },

  // Generate advanced dashboard data
  generateAdvancedData() {
    const hourlyForecast = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i.toString().padStart(2, '0')}:00`,
      aqi: 35 + Math.sin(i * 0.3) * 15 + Math.random() * 10,
      pm25: 8 + Math.sin(i * 0.2) * 5 + Math.random() * 3,
      temperature: 18 + Math.sin(i * 0.26) * 8,
      humidity: 60 + Math.sin(i * 0.15) * 20
    }));

    const weeklyForecast = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => ({
      day,
      aqi: 40 + Math.sin(i * 0.5) * 12,
      pm25: 10 + Math.sin(i * 0.3) * 4,
      temperature: 20 + Math.sin(i * 0.4) * 6
    }));

    return {
      locations: this.generateRegionalData(),
      hourlyForecast,
      weeklyForecast,
      pollutantBreakdown: {
        pm25: 35,
        pm10: 25,
        o3: 20,
        no2: 15,
        so2: 3,
        co: 2
      },
      healthMetrics: {
        respiratoryRisk: 'Moderate',
        cardiovascularRisk: 'Low',
        sensitiveGroupsRisk: 'Moderate',
        overallHealthIndex: 72
      }
    };
  }
};

// Data Service Class
class DataService {
  // AI Chat
  async submitQuery(query) {
    if (USE_MOCK_DATA) {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      return { response: mockData.generateAIResponse(query) };
    }
    
    return await apiService.submitQuery(query);
  }

  // Current Air Quality
  async getCurrentAirQuality(location = null) {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 800));
      return mockData.generateCurrentAirQuality();
    }
    
    return await apiService.getCurrentAirQuality(location);
  }

  // Forecast Data
  async getAirQualityForecast(location = null, days = 7) {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      return mockData.generateForecast(days);
    }
    
    return await apiService.getAirQualityForecast(location, days);
  }

  // Query-specific Data
  async getQuerySpecificData(query) {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 1200));
      return mockData.generateQuerySpecificData(query);
    }
    
    return await apiService.getQuerySpecificData(query);
  }

  // Regional Data
  async getRegionalData(bounds = null) {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 900));
      return mockData.generateRegionalData();
    }
    
    return await apiService.getRegionalData(bounds);
  }

  // Advanced Dashboard Data
  async getAdvancedData() {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 1100));
      return mockData.generateAdvancedData();
    }
    
    // In real implementation, this might call multiple APIs
    const [locations, forecast, pollutants, health] = await Promise.all([
      apiService.getRegionalData(),
      apiService.getAirQualityForecast(null, 7),
      apiService.getPollutantData(),
      apiService.getHealthImpactData()
    ]);
    
    return { locations, forecast, pollutants, health };
  }

  // Health check
  async healthCheck() {
    if (USE_MOCK_DATA) {
      return { status: 'ok', message: 'Mock data service operational' };
    }
    
    return await apiService.healthCheck();
  }
}

// Export singleton instance
export const dataService = new DataService();
export default dataService;
