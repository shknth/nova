import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThermometerHalf, faWind, faTint, faLeaf } from '@fortawesome/free-solid-svg-icons';
import { useCurrentAirQuality } from '../hooks/useApi';
import './BasicMetrics.css';

const BasicMetrics = ({ location = null }) => {
  // 🎯 SUPER CLEAN API INTEGRATION - Just one line!
  const { data: airQualityData, loading, error } = useCurrentAirQuality(location);

  // Extract metrics from API response or use defaults
  const metrics = airQualityData?.current || {
    temperature: 22,
    aqi: 42,
    humidity: 65,
    windSpeed: 12
  };

  const getAQIStatus = (aqi) => {
    if (aqi <= 50) return { status: 'Good', color: '#10B981' };
    if (aqi <= 100) return { status: 'Moderate', color: '#FBBF24' };
    if (aqi <= 150) return { status: 'Unhealthy for Sensitive', color: '#F59E0B' };
    return { status: 'Unhealthy', color: '#EF4444' };
  };

  const aqiInfo = getAQIStatus(metrics.aqi);

  // Loading state
  if (loading) {
    return (
      <div className="basic-metrics">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="metric-card loading">
            <div className="metric-icon">⏳</div>
            <div className="metric-info">
              <span className="metric-value">--</span>
              <span className="metric-label">Loading...</span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="basic-metrics">
        <div className="metric-card error">
          <div className="metric-icon">⚠️</div>
          <div className="metric-info">
            <span className="metric-value">Error</span>
            <span className="metric-label">{error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="basic-metrics">
      <div className="metric-card">
        <div className="metric-icon">
          <FontAwesomeIcon icon={faThermometerHalf} />
        </div>
        <div className="metric-info">
          <span className="metric-value">{metrics.temperature}°C</span>
          <span className="metric-label">Temperature</span>
        </div>
      </div>

      <div className="metric-card aqi-card">
        <div className="metric-icon">
          <FontAwesomeIcon icon={faLeaf} />
        </div>
        <div className="metric-info">
          <span className="metric-value" style={{ color: aqiInfo.color }}>
            {metrics.aqi}
          </span>
          <span className="metric-label">{aqiInfo.status}</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">
          <FontAwesomeIcon icon={faTint} />
        </div>
        <div className="metric-info">
          <span className="metric-value">{metrics.humidity}%</span>
          <span className="metric-label">Humidity</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">
          <FontAwesomeIcon icon={faWind} />
        </div>
        <div className="metric-info">
          <span className="metric-value">{metrics.windSpeed} km/h</span>
          <span className="metric-label">Wind Speed</span>
        </div>
      </div>
    </div>
  );
};

export default BasicMetrics;
