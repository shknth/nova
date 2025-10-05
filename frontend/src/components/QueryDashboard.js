import React from 'react';
import { motion } from 'framer-motion';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faChartBar } from '@fortawesome/free-solid-svg-icons';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './QueryDashboard.css';
import L from 'leaflet';
import DynamicVisualization from './DynamicVisualization';
import { useTheme } from '../contexts/ThemeContext';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const QueryDashboard = ({ userQuery, apiData, onAdvancedDashboard, onBack }) => {
  const { isDark } = useTheme();

  // Extract time from user query (e.g., "2:00pm", "14:00", "2pm")
  const extractTimeFromQuery = (query) => {
    if (!query) return null;

    const timePatterns = [
      /(\d{1,2}):(\d{2})\s*(am|pm)/i,  // "2:00pm"
      /(\d{1,2})\s*(am|pm)/i,           // "2pm"
      /(\d{1,2}):(\d{2})/,               // "14:00"
    ];

    for (const pattern of timePatterns) {
      const match = query.match(pattern);
      if (match) {
        let hour = parseInt(match[1]);
        const minute = match[2] ? parseInt(match[2]) : 0;
        const meridiem = match[3] || match[2];

        if (meridiem && meridiem.toLowerCase() === 'pm' && hour !== 12) {
          hour += 12;
        } else if (meridiem && meridiem.toLowerCase() === 'am' && hour === 12) {
          hour = 0;
        }

        return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
      }
    }
    return null;
  };

  // Generate hourly forecast around the extracted time
  const generateHourlyForecast = (baseAQI, targetTime) => {
    const baseHour = targetTime ? parseInt(targetTime.split(':')[0]) : 14;
    const forecast = [];

    // Generate 7 hours of data (3 before, target hour, 3 after)
    for (let i = -3; i <= 3; i++) {
      const hour = (baseHour + i + 24) % 24;
      const timeStr = `${hour.toString().padStart(2, '0')}:00`;

      // Add some variance (±3) but make target time exact
      let aqiValue = baseAQI;
      if (i !== 0) {
        const variance = (Math.random() * 6) - 3; // Random value between -3 and +3
        aqiValue = Math.round(baseAQI + variance);
      }

      forecast.push({ time: timeStr, aqi: aqiValue });
    }

    return forecast;
  };

  const generateQuerySpecificData = () => {
    const queryString = userQuery && typeof userQuery === 'string' ? userQuery.toLowerCase() : '';

    // Use API data if available
    if (apiData && apiData.metadata && apiData.metadata.analysis) {
      console.log('🗺️ Full API Data:', apiData);

      const analysis = apiData.metadata.analysis;
      const results = analysis.results || {};
      const context = apiData.metadata.context || {};
      const dashboardDetails = apiData.dashboard_details || {};

      const aqiData = results.aqi || {};
      const currentAQI = aqiData.value || dashboardDetails.aqi || 42;

      // Extract coordinates from first map visualization
      let mapCenter = [39.8283, -98.5795]; // Default
      let location = dashboardDetails.location || 'Current Location';

      if (dashboardDetails.visualizations && dashboardDetails.visualizations.length > 0) {
        console.log('📊 Visualizations:', dashboardDetails.visualizations);
        // Find first map visualization with coordinates
        const mapViz = dashboardDetails.visualizations.find(viz => viz.type === 'map' && viz.data && viz.data.lat && viz.data.lon);
        if (mapViz) {
          mapCenter = [mapViz.data.lat, mapViz.data.lon];
          console.log('📍 Map coordinates from visualization:', mapCenter);
        }
      }

      // Extract time from query
      const extractedTime = extractTimeFromQuery(userQuery);

      // Check for time series visualization data
      let timeData = [];
      let timeSeriesViz = null;

      if (dashboardDetails.visualizations && dashboardDetails.visualizations.length > 0) {
        timeSeriesViz = dashboardDetails.visualizations.find(viz => viz.type === 'line');

        if (timeSeriesViz && timeSeriesViz.data && timeSeriesViz.data.timestamp && timeSeriesViz.data.value) {
          // Extract the single point from time series
          const timestamp = timeSeriesViz.data.timestamp;
          const value = timeSeriesViz.data.value;

          console.log('📈 Time series data found:', { timestamp, value });

          // Parse the timestamp to get hour
          const targetHour = new Date(timestamp).getHours();

          // Generate ±3 hours around this point
          timeData = generateHourlyForecast(value, `${targetHour.toString().padStart(2, '0')}:00`);
        } else {
          // Fallback to generating from current AQI
          timeData = generateHourlyForecast(currentAQI, extractedTime);
        }
      } else {
        // Fallback to generating from current AQI
        timeData = generateHourlyForecast(currentAQI, extractedTime);
      }

      // Build pollutants object from API data (only actual pollutants, not weather data)
      const pollutants = {};
      if (results.pm25) {
        pollutants['PM2.5'] = { value: results.pm25.value, risk: results.pm25.status };
      }
      if (results.o3) {
        pollutants['O3'] = { value: results.o3.value, risk: results.o3.status };
      }
      if (results.no2) {
        pollutants['NO2'] = { value: results.no2.value, risk: results.no2.status };
      }
      if (results.ch2o) {
        pollutants['CH2O'] = { value: results.ch2o.value, risk: results.ch2o.status };
      }
      if (results.co) {
        pollutants['CO'] = { value: results.co.value, risk: results.co.status };
      }
      if (results.aod) {
        pollutants['AOD'] = { value: results.aod.value, risk: results.aod.status };
      }

      // Extract temperature and wind speed for display
      const temperature = results.temperature ? results.temperature.value : null;
      const windSpeed = results.wind_speed ? results.wind_speed.value : null;

      // Filter out time series from visualizations to avoid duplicate
      // Also remove duplicate visualizations (same type and title)
      let filteredVisualizations = [];
      if (dashboardDetails.visualizations) {
        const seen = new Set();
        filteredVisualizations = dashboardDetails.visualizations.filter(viz => {
          // Skip line charts (already handled in Hourly Forecast)
          if (viz.type === 'line') return false;

          // Skip "Pollutant Comparison" as it duplicates Key Pollutants chart
          if (viz.title && viz.title.toLowerCase().includes('pollutant comparison')) return false;

          // Create unique key from type and title
          const key = `${viz.type}-${viz.title}`;

          // If we've seen this combination before, skip it
          if (seen.has(key)) return false;

          // Otherwise, mark as seen and include it
          seen.add(key);
          return true;
        });
      }

      return {
        location,
        currentAQI: Math.round(currentAQI),
        healthRisk: aqiData.status || 'Unknown',
        recommendation: analysis.recommendations?.[0] || 'No specific recommendations',
        recommendations: analysis.recommendations || [],
        timeData,
        pollutants,
        mapCenter,
        temperature,
        windSpeed,
        visualizations: filteredVisualizations
      };
    }

    // Fallback to mock data
    const location = queryString.includes('maryland') ? 'Maryland Park' :
                    queryString.includes('dublin') ? 'Dublin' :
                    queryString.includes('cork') ? 'Cork' : 'Current Location';

    return {
      location,
      currentAQI: 42,
      healthRisk: queryString.includes('asthma') ? 'Moderate Risk' : 'Low Risk',
      recommendation: queryString.includes('asthma') ?
        'Consider indoor activities or wait for better air quality' :
        'Safe for outdoor activities',
      recommendations: ['No API data available'],
      timeData: [
        { time: '12:00', aqi: 38 },
        { time: '13:00', aqi: 42 },
        { time: '14:00', aqi: 45 },
        { time: '15:00', aqi: 48 },
        { time: '16:00', aqi: 44 },
        { time: '17:00', aqi: 40 },
        { time: '18:00', aqi: 36 }
      ],
      pollutants: {
        'PM2.5': { value: 12.5, risk: queryString.includes('asthma') ? 'High' : 'Moderate' },
        'O3': { value: 35.8, risk: queryString.includes('asthma') ? 'Moderate' : 'Low' },
      },
      mapCenter: queryString.includes('dublin') ? [53.3498, -6.2603] : [39.8283, -98.5795]
    };
  };

  const data = generateQuerySpecificData();

  const timeChartData = {
    labels: data.timeData.map(d => d.time),
    datasets: [{
      label: 'AQI Forecast',
      data: data.timeData.map(d => d.aqi),
      borderColor: '#ef4444',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      fill: true,
      tension: 0.4,
      borderWidth: 3
    }]
  };

  const pollutantChartData = {
    labels: Object.keys(data.pollutants),
    datasets: [{
      label: 'Concentration (μg/m³)',
      data: Object.values(data.pollutants).map(p => p.value),
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(59, 130, 246, 0.8)'
      ],
      borderColor: [
        'rgb(239, 68, 68)',
        'rgb(245, 158, 11)',
        'rgb(16, 185, 129)',
        'rgb(59, 130, 246)'
      ],
      borderWidth: 2
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#ffffff'
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    }
  };

  return (
    <motion.div 
      className="query-dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="dashboard-container">
        <motion.div 
          className="dashboard-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <button className="back-button" onClick={onBack}>
            <FontAwesomeIcon icon={faArrowLeft} />
            Back
          </button>
          <div className="header-content">
            <h1>Query Analysis</h1>
            <p className="query-text">"{userQuery || 'No query provided'}"</p>
          </div>
        </motion.div>

        <div className="dashboard-grid">
          <motion.div 
            className="summary-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <h3>Air Quality Index</h3>
            <div className="summary-content">
              <div className="aqi-display">
                <span className="aqi-value">{data.currentAQI}</span>
                <span className="aqi-label">AQI</span>
              </div>
              <div className="health-info">
                <div className="health-risk">
                  <span className="label">Health Risk</span>
                  <span className={`value ${data.healthRisk.toLowerCase().replace(' ', '-')}`}>
                    {data.healthRisk}
                  </span>
                </div>
                {data.temperature && (
                  <div className="weather-info">
                    <span className="label">Temperature</span>
                    <span className="value">{Math.round(data.temperature)}°C</span>
                  </div>
                )}
                {data.windSpeed && (
                  <div className="weather-info">
                    <span className="label">Wind Speed</span>
                    <span className="value">{Math.round(data.windSpeed)} m/s</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          <motion.div
            className="recommendations-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <h3>Recommendations</h3>
            <div className="recommendations-content">
              {data.recommendations && data.recommendations.length > 0 ? (
                <ul className="recommendations-list">
                  {data.recommendations.map((recommendation, index) => (
                    <li key={index} className="recommendation-item">
                      <span className="recommendation-bullet">•</span>
                      <span className="recommendation-text">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="no-recommendations">No specific recommendations available.</p>
              )}
            </div>
          </motion.div>

          <motion.div
            className="chart-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <h3>Hourly Forecast</h3>
            <div style={{ height: '300px' }}>
              <Line key="hourly-forecast" data={timeChartData} options={chartOptions} />
            </div>
          </motion.div>

          <motion.div
            className="chart-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7, duration: 0.5 }}
          >
            <h3>Key Pollutants</h3>
            <div style={{ height: '300px' }}>
              <Bar key="pollutants-chart" data={pollutantChartData} options={chartOptions} />
            </div>
          </motion.div>

          <motion.div
            className="map-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8, duration: 0.5 }}
          >
            <h3>Location View - {data.location}</h3>
            <MapContainer
              center={data.mapCenter}
              zoom={data.mapCenter[0] === 53.3498 ? 12 : 4}
              style={{ height: '300px', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              <Circle
                center={data.mapCenter}
                radius={5000}
                pathOptions={{
                  fillColor: data.currentAQI <= 50 ? '#10B981' : '#FBBF24',
                  fillOpacity: 0.5,
                  color: data.currentAQI <= 50 ? '#10B981' : '#FBBF24',
                  weight: 2
                }}
              />
              <Marker position={data.mapCenter}>
                <Popup>
                  <div>
                    <h4>{data.location}</h4>
                    <p>AQI: {data.currentAQI}</p>
                    <p>Risk: {data.healthRisk}</p>
                  </div>
                </Popup>
              </Marker>
            </MapContainer>
          </motion.div>

          {/* Dynamic Visualizations from API */}
          {data.visualizations && data.visualizations.length > 0 && data.visualizations.map((viz, index) => (
            <motion.div
              key={`viz-${index}`}
              className="chart-card"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.9 + (index * 0.1), duration: 0.5 }}
            >
              <DynamicVisualization visualization={viz} index={index} isDark={isDark} />
            </motion.div>
          ))}
        </div>

        <motion.div
          className="advanced-button-container"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.5 }}
        >
          <button 
            className="advanced-dashboard-button"
            onClick={onAdvancedDashboard}
          >
            <FontAwesomeIcon icon={faChartBar} />
            View Advanced Dashboard
          </button>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default QueryDashboard;
