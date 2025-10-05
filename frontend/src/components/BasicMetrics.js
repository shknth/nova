import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThermometerHalf, faWind, faTint, faLeaf, faSpinner } from '@fortawesome/free-solid-svg-icons';
import { getWeatherMetrics } from '../services/apiService';
import './BasicMetrics.css';

const BasicMetrics = () => {
  const [metrics, setMetrics] = useState({
    temperature: 22,
    aqi: 42,
    humidity: 65,
    windSpeed: 12
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWeatherMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch real weather metrics from your trained model
        const response = await getWeatherMetrics();
        
        if (response.status === 'success' && response.metrics) {
          setMetrics({
            temperature: response.metrics.temperature,
            aqi: response.metrics.aqi,
            humidity: response.metrics.humidity,
            windSpeed: response.metrics.windSpeed
          });
        }
      } catch (err) {
        console.error('Failed to fetch weather metrics:', err);
        setError('Failed to load weather data');
        // Keep default values on error
      } finally {
        setLoading(false);
      }
    };

    fetchWeatherMetrics();
    
    // Refresh data every 5 minutes
    const interval = setInterval(fetchWeatherMetrics, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const getAQIStatus = (aqi) => {
    if (aqi <= 50) return { status: 'Good', color: '#10B981' };
    if (aqi <= 100) return { status: 'Moderate', color: '#FBBF24' };
    if (aqi <= 150) return { status: 'Unhealthy for Sensitive', color: '#F59E0B' };
    return { status: 'Unhealthy', color: '#EF4444' };
  };

  const aqiInfo = getAQIStatus(metrics.aqi);

  // Show loading state
  if (loading) {
    return (
      <div className="basic-metrics loading">
        <div className="loading-indicator">
          <FontAwesomeIcon icon={faSpinner} spin />
          <span>Loading weather data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="basic-metrics">
      {error && (
        <div className="error-indicator">
          <small>⚠️ {error} - Showing cached data</small>
        </div>
      )}
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
