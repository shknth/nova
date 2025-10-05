import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faArrowLeft, 
  faChartBar, 
  faChartLine, 
  faFlask, 
  faHeart, 
  faMapMarkerAlt 
} from '@fortawesome/free-solid-svg-icons';
import { Line, Bar, Doughnut, Scatter } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement,
  ArcElement,
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './AdvancedDashboard.css';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AdvancedDashboard = ({ apiData, onBack }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Extract data from API using useMemo to recalculate when apiData changes
  const { currentAQI, currentLocation, mapCenter } = React.useMemo(() => {
    let center = [53.0, -7.5]; // Default center (Ireland)
    let aqi = apiData.dashboard_details.aqi; // Default AQI
    let location = 'Unknown';

    console.log('🔍 Advanced Dashboard API Data:', apiData);

    if (apiData) {
      // Try to extract AQI from multiple sources
      if (apiData.dashboard_details && apiData.dashboard_details.aqi) {
        aqi = Math.round(apiData.dashboard_details.aqi);
        console.log('📊 AQI fromadvanced dashboard_details:', apiData.dashboard_details.aqi, '→ rounded:', aqi);
      } else if (apiData.metadata && apiData.metadata.analysis && apiData.metadata.analysis.results && apiData.metadata.analysis.results.aqi) {
        aqi = Math.round(apiData.metadata.analysis.results.aqi.value);
        console.log('📊 AQI from metadata.analysis:', aqi);
      }

      // Extract location
      if (apiData.dashboard_details && apiData.dashboard_details.location) {
        location = apiData.dashboard_details.location;
      } else if (apiData.metadata && apiData.metadata.context && apiData.metadata.context.original_prompt) {
        // Try to extract location from prompt
        const locationMatch = apiData.metadata.context.original_prompt.match(/in ([A-Za-z\s]+)/);
        location = locationMatch ? locationMatch[1] : 'Unknown';
      }

      // Extract coordinates
      if (apiData.dashboard_details && apiData.dashboard_details.visualizations) {
        const mapViz = apiData.dashboard_details.visualizations.find(viz => viz.type === 'map' && viz.data && viz.data.lat && viz.data.lon);
        if (mapViz) {
          center = [mapViz.data.lat, mapViz.data.lon];
          console.log('📍 Coordinates from visualization:', center);
        }
      }
    }

    console.log('✅ Final AQI:', aqi, 'Location:', location);

    return { currentAQI: aqi, currentLocation: location, mapCenter: center };
  }, [apiData]);

  // Use real data from API, with fallback to mock data
  const data = {
    locations: [
      { id: 1, lat: mapCenter[0], lng: mapCenter[1], aqi: currentAQI, location: currentLocation, pm25: 12.5, pm10: 18.2, o3: 35.8, no2: 15.3 }
    ],
    hourlyForecast: Array.from({ length: 24 }, (_, i) => ({
      hour: `${i.toString().padStart(2, '0')}:00`,
      aqi: currentAQI + Math.sin(i * 0.3) * 10 + Math.random() * 8 - 4,
      pm25: 8 + Math.sin(i * 0.2) * 5 + Math.random() * 3,
      temperature: 18 + Math.sin(i * 0.26) * 8,
      humidity: 60 + Math.sin(i * 0.15) * 20
    })),
    weeklyForecast: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => ({
      day,
      aqi: currentAQI + Math.sin(i * 0.5) * 10 + (Math.random() * 6 - 3),
      pm25: 10 + Math.sin(i * 0.3) * 4,
      temperature: 20 + Math.sin(i * 0.4) * 6
    })),
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

  const tabs = [
    { id: 'overview', label: 'Overview', icon: faChartBar },
    { id: 'forecasts', label: 'Forecasts', icon: faChartLine },
    { id: 'pollutants', label: 'Pollutants', icon: faFlask },
    { id: 'health', label: 'Health Impact', icon: faHeart },
    { id: 'map', label: 'Regional Map', icon: faMapMarkerAlt }
  ];

  const renderOverview = () => {
    const overviewChartData = {
      labels: data.hourlyForecast.slice(0, 12).map(d => d.hour),
      datasets: [
        {
          label: 'AQI',
          data: data.hourlyForecast.slice(0, 12).map(d => d.aqi),
          borderColor: '#1e3a8a',
          backgroundColor: 'rgba(30, 58, 138, 0.1)',
          yAxisID: 'y'
        },
        {
          label: 'PM2.5',
          data: data.hourlyForecast.slice(0, 12).map(d => d.pm25),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          yAxisID: 'y1'
        }
      ]
    };

    return (
      <div className="tab-content">
        <div className="metrics-grid">
          <div className="metric-card large">
            <h3>Current Air Quality Index</h3>
            <div className="large-metric">
              <span className="value">{currentAQI}</span>
              <span className="label">Good</span>
            </div>
          </div>
          <div className="metric-card">
            <h4>PM2.5</h4>
            <span className="value">12.5 μg/m³</span>
          </div>
          <div className="metric-card">
            <h4>PM10</h4>
            <span className="value">18.2 μg/m³</span>
          </div>
          <div className="metric-card">
            <h4>Ozone</h4>
            <span className="value">35.8 ppb</span>
          </div>
        </div>
        <div className="chart-container">
          <h3>12-Hour Trend</h3>
          <div style={{ height: '300px' }}>
            <Line
              key="overview-chart"
              data={overviewChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    labels: {
                      color: '#ffffff'
                    }
                  }
                },
                scales: {
                  x: {
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                  },
                  y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                  },
                  y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: '#ffffff' },
                    grid: { drawOnChartArea: false, color: 'rgba(255, 255, 255, 0.1)' }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderForecasts = () => {
    const weeklyChartData = {
      labels: data.weeklyForecast.map(d => d.day),
      datasets: [{
        label: 'Weekly AQI Forecast',
        data: data.weeklyForecast.map(d => d.aqi),
        backgroundColor: 'rgba(30, 58, 138, 0.8)',
        borderColor: '#1e3a8a',
        borderWidth: 2
      }]
    };

    return (
      <div className="tab-content">
        <div className="forecast-grid">
          <div className="chart-container">
            <h3>7-Day AQI Forecast</h3>
            <div style={{ height: '300px' }}>
              <Bar key="weekly-forecast" data={weeklyChartData} options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    labels: {
                      color: '#ffffff'
                    }
                  }
                },
                scales: {
                  x: {
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                  },
                  y: {
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                  }
                }
              }} />
            </div>
          </div>
          <div className="forecast-details">
            <h3 className="forecast-heading">Detailed Forecast</h3>
            {data.weeklyForecast.map((day, index) => (
              <div key={index} className="forecast-item">
                <span className="day">{day.day}</span>
                <span className="aqi">AQI: {Math.round(day.aqi)}</span>
                <span className="temp">{Math.round(day.temperature)}°C</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPollutants = () => {
    const pollutantChartData = {
      labels: Object.keys(data.pollutantBreakdown),
      datasets: [{
        data: Object.values(data.pollutantBreakdown),
        backgroundColor: [
          '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'
        ]
      }]
    };

    return (
      <div className="tab-content">
        <div className="pollutant-grid">
          <div className="chart-container">
            <h3>Pollutant Composition</h3>
            <div style={{ height: '300px' }}>
              <Doughnut key="pollutant-doughnut" data={pollutantChartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="pollutant-details">
  <h3 className="pollutant-heading">Pollutant Levels</h3>
            {Object.entries(data.pollutantBreakdown).map(([pollutant, percentage]) => (
              <div key={pollutant} className="pollutant-item">
                <span className="name">{pollutant.toUpperCase()}</span>
                <div className="bar">
                  <div className="fill" style={{ width: `${percentage}%` }}></div>
                </div>
                <span className="percentage">{percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderHealth = () => (
    <div className="tab-content">
      <div className="health-grid">
        <div className="health-overview">
          <h3 className="health-heading">Health Impact Assessment</h3>
          <div className="health-score">
            <div className="score-circle">
              <span className="score">{data.healthMetrics.overallHealthIndex}</span>
              <span className="label">Health Index</span>
            </div>
          </div>
        </div>
        <div className="health-risks">
          <h3 className="health-heading">Risk Categories</h3>
          <div className="risk-item">
            <span className="category">Respiratory Risk</span>
            <span className={`risk ${data.healthMetrics.respiratoryRisk.toLowerCase()}`}>
              {data.healthMetrics.respiratoryRisk}
            </span>
          </div>
          <div className="risk-item">
            <span className="category">Cardiovascular Risk</span>
            <span className={`risk ${data.healthMetrics.cardiovascularRisk.toLowerCase()}`}>
              {data.healthMetrics.cardiovascularRisk}
            </span>
          </div>
          <div className="risk-item">
            <span className="category">Sensitive Groups</span>
            <span className={`risk ${data.healthMetrics.sensitiveGroupsRisk.toLowerCase()}`}>
              {data.healthMetrics.sensitiveGroupsRisk}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMap = () => (
    <div className="tab-content">
      <div className="map-container-advanced">
        <h3 className="map-heading">Regional Air Quality</h3>
        <MapContainer
        center={mapCenter}
        zoom={10}
        style={{ height: '500px', width: '100%' }}
        maxBounds={[[-90, -180], [90, 180]]} 
        minZoom={2} 
        maxBoundsViscosity={1.0}
      >
          <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
          noWrap={true} // Prevent tile repetition
          bounds={[[-90, -180], [90, 180]]} // Set tile bounds
        />
          {data.locations.map(location => (
            <React.Fragment key={location.id}>
              <Circle
                center={[location.lat, location.lng]}
                radius={20000}
                pathOptions={{
                  fillColor: location.aqi <= 50 ? '#10B981' : location.aqi <= 100 ? '#FBBF24' : '#EF4444',
                  fillOpacity: 0.5,
                  color: location.aqi <= 50 ? '#10B981' : location.aqi <= 100 ? '#FBBF24' : '#EF4444',
                  weight: 2
                }}
              />
              <Marker position={[location.lat, location.lng]}>
                <Popup>
                  <div className="popup-content">
                    <h4>{location.location}</h4>
                    <p><strong>AQI:</strong> {location.aqi}</p>
                    <p><strong>PM2.5:</strong> {location.pm25} μg/m³</p>
                    <p><strong>PM10:</strong> {location.pm10} μg/m³</p>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          ))}
        </MapContainer>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverview();
      case 'forecasts': return renderForecasts();
      case 'pollutants': return renderPollutants();
      case 'health': return renderHealth();
      case 'map': return renderMap();
      default: return renderOverview();
    }
  };

  return (
    <motion.div 
      className="advanced-dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="advanced-container">
        <motion.div 
          className="advanced-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <button className="back-button" onClick={onBack}>
            <FontAwesomeIcon icon={faArrowLeft} />
            Back
          </button>
          <h1>Advanced Air Quality Dashboard</h1>
        </motion.div>

        <motion.div 
          className="tab-navigation"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">
                <FontAwesomeIcon icon={tab.icon} />
              </span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </motion.div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderTabContent()}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default AdvancedDashboard;
