import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThermometerHalf, faWind, faTint, faLeaf, faSpinner, faSnowflake, faSun, faCloud } from '@fortawesome/free-solid-svg-icons';
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

  // Enhanced status functions with animation classes
  const getTemperatureStatus = (temp) => {
    if (temp <= 0) return { status: 'Freezing', color: '#3B82F6', icon: faSnowflake, class: 'freezing' };
    if (temp <= 10) return { status: 'Cold', color: '#60A5FA', icon: faSnowflake, class: 'cold' };
    if (temp <= 20) return { status: 'Cool', color: '#34D399', icon: faCloud, class: 'cool' };
    if (temp <= 30) return { status: 'Warm', color: '#FBBF24', icon: faSun, class: 'warm' };
    return { status: 'Hot', color: '#EF4444', icon: faSun, class: 'hot' };
  };

  const getAQIStatus = (aqi) => {
    if (aqi <= 50) return { status: 'Good', color: '#10B981', class: 'good' };
    if (aqi <= 100) return { status: 'Moderate', color: '#FBBF24', class: 'moderate' };
    if (aqi <= 150) return { status: 'Unhealthy for Sensitive', color: '#F59E0B', class: 'unhealthy-sensitive' };
    return { status: 'Unhealthy', color: '#EF4444', class: 'unhealthy' };
  };

  const getHumidityStatus = (humidity) => {
    if (humidity <= 30) return { status: 'Dry', class: 'dry' };
    if (humidity <= 60) return { status: 'Comfortable', class: 'comfortable' };
    return { status: 'Humid', class: 'humid' };
  };

  const getWindStatus = (windSpeed) => {
    if (windSpeed <= 5) return { status: 'Calm', class: 'calm' };
    if (windSpeed <= 15) return { status: 'Light Breeze', class: 'light' };
    if (windSpeed <= 30) return { status: 'Moderate Wind', class: 'moderate' };
    return { status: 'Strong Wind', class: 'strong' };
  };

  const tempInfo = getTemperatureStatus(metrics.temperature);
  const aqiInfo = getAQIStatus(metrics.aqi);
  const humidityInfo = getHumidityStatus(metrics.humidity);
  const windInfo = getWindStatus(metrics.windSpeed);

  // Generate animated particles with better positioning
  const generateParticles = (count, type) => {
    return Array.from({ length: count }, (_, i) => {
      const baseDelay = Math.random() * 2;
      const baseDuration = 2 + Math.random() * 3;
      
      // Better positioning based on particle type
      let leftPosition = Math.random() * 100;
      let topPosition = Math.random() * 100;
      
      if (type === 'wind-particle') {
        topPosition = 30 + Math.random() * 40; // Middle area for wind
        leftPosition = Math.random() * 20; // Start from left side
      } else if (type === 'water-drop') {
        topPosition = 0; // Start from top for rain
        leftPosition = 10 + Math.random() * 80; // Avoid edges
      } else if (type === 'heat-wave') {
        topPosition = 70 + Math.random() * 30; // Start from bottom for heat
        leftPosition = 20 + Math.random() * 60;
      }
      
      return (
        <div key={i} className={`particle ${type}`} style={{
          left: `${leftPosition}%`,
          top: type === 'wind-particle' || type === 'water-drop' || type === 'heat-wave' ? `${topPosition}%` : undefined,
          animationDelay: `${baseDelay}s`,
          animationDuration: `${baseDuration}s`
        }} />
      );
    });
  };

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
      
      {/* Temperature Card */}
      <div className={`metric-card temperature-card ${tempInfo.class}`}>
        <div className="card-background">
          {tempInfo.class === 'hot' && generateParticles(8, 'heat-wave')}
          {tempInfo.class === 'freezing' && generateParticles(12, 'snowflake')}
          {tempInfo.class === 'cold' && generateParticles(6, 'frost')}
        </div>
        <div className="metric-icon">
          <FontAwesomeIcon icon={tempInfo.icon} />
        </div>
        <div className="metric-info">
          <span className="metric-value" style={{ color: tempInfo.color }}>
            {metrics.temperature}°C
          </span>
          <span className="metric-label">{tempInfo.status}</span>
        </div>
      </div>

      {/* AQI Card */}
      <div className={`metric-card aqi-card ${aqiInfo.class}`}>
        <div className="card-background">
          {aqiInfo.class === 'good' && generateParticles(6, 'clean-air')}
          {(aqiInfo.class === 'unhealthy' || aqiInfo.class === 'unhealthy-sensitive') && 
           generateParticles(10, 'pollution')}
        </div>
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

      {/* Humidity Card */}
      <div className={`metric-card humidity-card ${humidityInfo.class}`}>
        <div className="card-background">
          {humidityInfo.class === 'humid' && generateParticles(8, 'water-drop')}
          {humidityInfo.class === 'dry' && generateParticles(4, 'dust')}
        </div>
        <div className="metric-icon">
          <FontAwesomeIcon icon={faTint} />
        </div>
        <div className="metric-info">
          <span className="metric-value">{metrics.humidity}%</span>
          <span className="metric-label">{humidityInfo.status}</span>
        </div>
      </div>

      {/* Wind Card */}
      <div className={`metric-card wind-card ${windInfo.class}`}>
        <div className="card-background">
          {windInfo.class !== 'calm' && generateParticles(12, 'wind-particle')}
          <div className="wind-lines">
            <div className="wind-line"></div>
            <div className="wind-line"></div>
            <div className="wind-line"></div>
          </div>
        </div>
        <div className="metric-icon">
          <FontAwesomeIcon icon={faWind} />
        </div>
        <div className="metric-info">
          <span className="metric-value">{metrics.windSpeed} km/h</span>
          <span className="metric-label">{windInfo.status}</span>
        </div>
      </div>
    </div>
  );
};

export default BasicMetrics;
