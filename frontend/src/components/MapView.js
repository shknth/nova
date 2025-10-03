import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';
import L from 'leaflet';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const MapView = () => {
  // Sample data - this would come from your API in a real application
  const airQualityData = [
    { id: 1, lat: 37.7749, lng: -122.4194, aqi: 42, location: 'San Francisco' },
    { id: 2, lat: 34.0522, lng: -118.2437, aqi: 65, location: 'Los Angeles' },
    { id: 3, lat: 40.7128, lng: -74.0060, aqi: 55, location: 'New York' },
    { id: 4, lat: 41.8781, lng: -87.6298, aqi: 48, location: 'Chicago' },
    { id: 5, lat: 29.7604, lng: -95.3698, aqi: 72, location: 'Houston' },
  ];

  // Function to determine circle color based on AQI
  const getCircleColor = (aqi) => {
    if (aqi <= 50) return '#10B981'; // Good - Green
    if (aqi <= 100) return '#FBBF24'; // Moderate - Yellow
    if (aqi <= 150) return '#F59E0B'; // Unhealthy for Sensitive Groups - Orange
    if (aqi <= 200) return '#EF4444'; // Unhealthy - Red
    if (aqi <= 300) return '#8B5CF6'; // Very Unhealthy - Purple
    return '#7F1D1D'; // Hazardous - Maroon
  };

  return (
    <div className="map-container">
      <div className="map-header">
        <h2>Air Quality Map</h2>
        <p>View air quality data across different locations</p>
      </div>
      
      <MapContainer 
        center={[39.8283, -98.5795]} // Center of the US
        zoom={4} 
        style={{ height: '600px', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {airQualityData.map(station => (
          <React.Fragment key={station.id}>
            <Circle
              center={[station.lat, station.lng]}
              radius={50000} // 50km radius
              pathOptions={{
                fillColor: getCircleColor(station.aqi),
                fillOpacity: 0.5,
                color: getCircleColor(station.aqi),
                weight: 1
              }}
            />
            <Marker position={[station.lat, station.lng]}>
              <Popup>
                <div className="popup-content">
                  <h3>{station.location}</h3>
                  <p><strong>AQI:</strong> {station.aqi}</p>
                  <p><strong>Status:</strong> {
                    station.aqi <= 50 ? 'Good' :
                    station.aqi <= 100 ? 'Moderate' :
                    station.aqi <= 150 ? 'Unhealthy for Sensitive Groups' :
                    station.aqi <= 200 ? 'Unhealthy' :
                    station.aqi <= 300 ? 'Very Unhealthy' : 'Hazardous'
                  }</p>
                </div>
              </Popup>
            </Marker>
          </React.Fragment>
        ))}
      </MapContainer>
      
      <div className="map-legend">
        <h3>AQI Legend</h3>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#10B981' }}></span>
            <span className="legend-label">Good (0-50)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#FBBF24' }}></span>
            <span className="legend-label">Moderate (51-100)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#F59E0B' }}></span>
            <span className="legend-label">Unhealthy for Sensitive Groups (101-150)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#EF4444' }}></span>
            <span className="legend-label">Unhealthy (151-200)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#8B5CF6' }}></span>
            <span className="legend-label">Very Unhealthy (201-300)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#7F1D1D' }}></span>
            <span className="legend-label">Hazardous (301+)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;
