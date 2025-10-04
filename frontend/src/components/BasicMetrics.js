import React from 'react';
import './BasicMetrics.css';

const BasicMetrics = () => {
  // Mock data - will be replaced with real API data
  const metrics = {
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

  return (
    <div className="basic-metrics">
      <div className="metric-card">
        <div className="metric-icon">🌡️</div>
        <div className="metric-info">
          <span className="metric-value">{metrics.temperature}°C</span>
          <span className="metric-label">Temperature</span>
        </div>
      </div>

      <div className="metric-card aqi-card">
        <div className="metric-icon">🌬️</div>
        <div className="metric-info">
          <span className="metric-value" style={{ color: aqiInfo.color }}>
            {metrics.aqi}
          </span>
          <span className="metric-label">{aqiInfo.status}</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">💧</div>
        <div className="metric-info">
          <span className="metric-value">{metrics.humidity}%</span>
          <span className="metric-label">Humidity</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">💨</div>
        <div className="metric-info">
          <span className="metric-value">{metrics.windSpeed} km/h</span>
          <span className="metric-label">Wind Speed</span>
        </div>
      </div>
    </div>
  );
};

export default BasicMetrics;
