import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const Dashboard = () => {
  const [aqiData, setAqiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // In a real app, this would fetch from your backend API
    // For now, we'll use placeholder data
    const fetchData = async () => {
      try {
        // This will be replaced with actual API call once backend is ready
        // const response = await axios.get('http://localhost:5000/api/data');
        // setAqiData(response.data);
        
        // Placeholder data
        setAqiData({
          current: {
            aqi: 42,
            category: 'Good',
            pollutants: {
              pm25: 10.2,
              pm10: 18.5,
              o3: 35.1,
              no2: 12.3
            }
          },
          forecast: [
            { date: 'Today', aqi: 42 },
            { date: 'Tomorrow', aqi: 45 },
            { date: 'Day 3', aqi: 52 },
            { date: 'Day 4', aqi: 48 },
            { date: 'Day 5', aqi: 38 },
            { date: 'Day 6', aqi: 35 },
            { date: 'Day 7', aqi: 40 }
          ]
        });
        setLoading(false);
      } catch (err) {
        setError('Failed to load air quality data');
        setLoading(false);
        console.error('Error fetching data:', err);
      }
    };

    fetchData();
  }, []);

  const chartData = {
    labels: aqiData?.forecast.map(day => day.date) || [],
    datasets: [
      {
        label: 'Air Quality Index (AQI)',
        data: aqiData?.forecast.map(day => day.aqi) || [],
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: '7-Day AQI Forecast',
      },
    },
  };

  if (loading) return <div className="loading">Loading air quality data...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Air Quality Dashboard</h2>
        <p>Real-time air quality monitoring and predictions</p>
      </div>
      
      <div className="dashboard-grid">
        <div className="card current-aqi">
          <h3>Current AQI</h3>
          <div className="aqi-value">{aqiData.current.aqi}</div>
          <div className={`aqi-category ${aqiData.current.category.toLowerCase()}`}>
            {aqiData.current.category}
          </div>
        </div>
        
        <div className="card pollutants">
          <h3>Pollutants</h3>
          <div className="pollutant-grid">
            <div className="pollutant">
              <span className="pollutant-name">PM2.5</span>
              <span className="pollutant-value">{aqiData.current.pollutants.pm25} μg/m³</span>
            </div>
            <div className="pollutant">
              <span className="pollutant-name">PM10</span>
              <span className="pollutant-value">{aqiData.current.pollutants.pm10} μg/m³</span>
            </div>
            <div className="pollutant">
              <span className="pollutant-name">O₃</span>
              <span className="pollutant-value">{aqiData.current.pollutants.o3} ppb</span>
            </div>
            <div className="pollutant">
              <span className="pollutant-name">NO₂</span>
              <span className="pollutant-value">{aqiData.current.pollutants.no2} ppb</span>
            </div>
          </div>
        </div>
        
        <div className="card forecast-chart">
          <Line options={chartOptions} data={chartData} />
        </div>
        
        <div className="card recommendations">
          <h3>Recommendations</h3>
          <ul>
            <li>Air quality is good - ideal for outdoor activities</li>
            <li>No special precautions needed for sensitive groups</li>
            <li>Continue monitoring for changes in air quality</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
