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

const QueryDashboard = ({ userQuery, onAdvancedDashboard, onBack }) => {
  // Mock data based on query - in real app, this would come from backend
  const generateQuerySpecificData = () => {
    // Ensure userQuery is a string and handle null/undefined cases
    const queryString = userQuery && typeof userQuery === 'string' ? userQuery.toLowerCase() : '';
    
    // Extract location from query if possible
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
        pm25: { value: 12.5, risk: queryString.includes('asthma') ? 'High' : 'Moderate' },
        pm10: { value: 18.2, risk: 'Low' },
        o3: { value: 35.8, risk: queryString.includes('asthma') ? 'Moderate' : 'Low' },
        no2: { value: 15.3, risk: 'Low' }
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
      borderColor: '#1e3a8a',
      backgroundColor: 'rgba(30, 58, 138, 0.1)',
      fill: true,
      tension: 0.4
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
      }
    },
    scales: {
      y: {
        beginAtZero: true
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
            <h3>Current Conditions - {data.location}</h3>
            <div className="summary-content">
              <div className="aqi-display">
                <span className="aqi-value">{data.currentAQI}</span>
                <span className="aqi-label">AQI</span>
              </div>
              <div className="health-info">
                <div className="health-risk">
                  <span className="label">Health Risk:</span>
                  <span className={`value ${data.healthRisk.toLowerCase().replace(' ', '-')}`}>
                    {data.healthRisk}
                  </span>
                </div>
                <div className="recommendation">
                  <span className="label">Recommendation:</span>
                  <span className="value">{data.recommendation}</span>
                </div>
              </div>
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
            transition={{ delay: 0.8, duration: 0.5 }}
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
            transition={{ delay: 1, duration: 0.5 }}
          >
            <h3>Location View</h3>
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
