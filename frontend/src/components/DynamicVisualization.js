import React from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import HeatmapLayer from './HeatmapLayer';
import './DynamicVisualization.css';

const DynamicVisualization = ({ visualization, index, isDark }) => {
  if (!visualization || !visualization.type) {
    return null;
  }

  const { type, title, description, data, config } = visualization;

  // Check if this is a pollution concentration map
  const isPollutionMap = type === 'map' && title && title.toLowerCase().includes('pollutant concentration');

  // Dark mode tile layer URL - only for pollution concentration maps
  const tileLayerUrl = (isPollutionMap && isDark)
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  const renderVisualization = () => {
    switch (type) {
      case 'line':
        return renderLineChart();
      case 'bar':
        return renderBarChart();
      case 'map':
        return renderMap();
      default:
        return <p className="unsupported-viz">Visualization type "{type}" not supported yet.</p>;
    }
  };

  const renderLineChart = () => {
    // For line charts, we expect data to have timestamps and values
    if (!data || Object.keys(data).length === 0) {
      return <p className="no-data">No data available for this chart</p>;
    }

    const chartData = {
      labels: data.labels || [],
      datasets: [{
        label: title || 'Data',
        data: data.values || [],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 3
      }]
    };

    const options = {
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
      <div style={{ height: '300px' }}>
        <Line data={chartData} options={options} />
      </div>
    );
  };

  const renderBarChart = () => {
    if (!data || Object.keys(data).length === 0) {
      return <p className="no-data">No data available for this chart</p>;
    }

    const chartData = {
      labels: data.labels || [],
      datasets: [{
        label: title || 'Data',
        data: data.values || [],
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

    const options = {
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
      <div style={{ height: '300px' }}>
        <Bar data={chartData} options={options} />
      </div>
    );
  };

  const generateHeatmapPoints = (centerLat, centerLon, centerValue) => {
    const points = [];

    // Add center point with value from API
    const centerIntensity = Math.min(1.0, centerValue / 100); // Normalize to 0-1
    points.push([centerLat, centerLon, centerIntensity]);

    // Generate random surrounding points
    // Distance variance: 20 (spread over ~2.2km radius)
    // Value variance: ±10 from center value
    const numPoints = 30;
    const maxDistance = 0.02; // ~2.2km radius (distance variance of 20)

    for (let i = 0; i < numPoints; i++) {
      // Random distance from center (0 to maxDistance)
      const distance = Math.random() * maxDistance;
      // Random angle
      const angle = Math.random() * 2 * Math.PI;

      // Calculate lat/lon offset
      const latOffset = distance * Math.cos(angle);
      const lonOffset = distance * Math.sin(angle);

      // Generate random value with ±10 variance from center value
      const valueVariance = (Math.random() * 20) - 10; // Random between -10 and +10
      const pointValue = Math.max(0, centerValue + valueVariance);

      // Convert to intensity (0-1 scale)
      const intensity = Math.min(1.0, pointValue / 100);

      points.push([
        centerLat + latOffset,
        centerLon + lonOffset,
        intensity
      ]);
    }

    return points;
  };

  const renderMap = () => {
    if (!data || !data.lat || !data.lon) {
      return <p className="no-data">No location data available for this map</p>;
    }

    const center = [data.lat, data.lon];
    const zoom = config?.zoom || 10;
    const aqiValue = data.value || 50;

    // Check if this is a pollution concentration map
    if (isPollutionMap) {
      // Generate heatmap points
      const heatmapPoints = generateHeatmapPoints(data.lat, data.lon, aqiValue);

      return (
        <MapContainer
          center={center}
          zoom={zoom}
          style={{ height: '400px', width: '100%' }}
        >
          <TileLayer
            url={tileLayerUrl}
            attribution='&copy; OpenStreetMap contributors'
          />
          <HeatmapLayer points={heatmapPoints} />
          <Marker position={center}>
            <Popup>
              <div>
                <h4>{data.title || 'Pollutant Concentration'}</h4>
                <p>Value: {aqiValue}</p>
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      );
    }

    // Regular map with circle
    return (
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '300px', width: '100%' }}
      >
        <TileLayer
          url={tileLayerUrl}
          attribution='&copy; OpenStreetMap contributors'
        />
        <Circle
          center={center}
          radius={5000}
          pathOptions={{
            fillColor: aqiValue <= 50 ? '#10B981' : '#FBBF24',
            fillOpacity: 0.5,
            color: aqiValue <= 50 ? '#10B981' : '#FBBF24',
            weight: 2
          }}
        />
        <Marker position={center}>
          <Popup>
            <div>
              <h4>{data.title || 'Location'}</h4>
              <p>AQI: {aqiValue}</p>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    );
  };

  return (
    <div className={`dynamic-visualization ${isPollutionMap ? 'pollution-map-wide' : ''}`}>
      <h3>{title || 'Visualization'}</h3>
      {description && <p className="viz-description">{description}</p>}
      <div className="viz-content">
        {renderVisualization()}
      </div>
    </div>
  );
};

export default DynamicVisualization;
