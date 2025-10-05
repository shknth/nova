"""
Real-time Data Source for AuraCast Alerts
Fetches live air quality data from various sources for alert monitoring
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import threading

# Configure logging
logger = logging.getLogger(__name__)

class RealtimeDataSource:
    """Real-time data source for alert monitoring"""
    
    def __init__(self):
        self.openaq_api_key = "edca264c44c7f9f67ed3c43e6e53fd7eddc84fa474b3ef268bddabe26d3b6f7e"
        # Cache structure
        self.data_cache = {}  # Short-term data cache
        self.sensor_cache = {}  # Long-term sensor ID cache
        self.location_cache = {}  # Long-term location details cache
        self.historical_cache = {}  # Historical data cache
        
        # Cache durations
        self.data_cache_duration = 300  # 5 minutes for real-time data
        self.sensor_cache_duration = 3600  # 1 hour for sensor IDs
        self.location_cache_duration = 3600  # 1 hour for location details
        self.historical_cache_duration = 3600  # 1 hour for historical data
        
        self.monitoring_locations = set()
        
    def add_monitoring_location(self, location: str):
        """Add a location to monitor for alerts"""
        self.monitoring_locations.add(location.lower())
        logger.info(f"Added monitoring location: {location}")
    
    def remove_monitoring_location(self, location: str):
        """Remove a location from monitoring"""
        self.monitoring_locations.discard(location.lower())
        logger.info(f"Removed monitoring location: {location}")
    
    def get_realtime_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Get real-time air quality data for a location"""
        # Check cache first
        cache_key = f"{location.lower()}_{datetime.now().strftime('%Y%m%d%H%M')}"
        if cache_key in self.data_cache:
            cached_data = self.data_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_duration):
                return cached_data['data']
        
        # Fetch fresh data
        try:
            # Try OpenAQ first
            data = self._fetch_openaq_data(location)
            if data:
                # Cache the data
                self.data_cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
                return data
            
            # Fallback to simulated data for demo
            data = self._generate_simulated_data(location)
            self.data_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            return data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {location}: {str(e)}")
            return None
    
    def _fetch_openaq_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch data from OpenAQ API"""
        try:
            # Use OpenAQ API v2
            url = "https://api.openaq.org/v2/measurements"
            
            # Get coordinates for the location (simplified - in real app, use geocoding)
            coords = self._get_location_coordinates(location)
            if not coords:
                return None
            
            params = {
                'date_from': (datetime.now() - timedelta(hours=1)).isoformat() + 'Z',
                'date_to': datetime.now().isoformat() + 'Z',
                'coordinates': f"{coords['lat']},{coords['lon']}",
                'radius': 10000,  # 10km radius
                'parameter': 'pm25,o3,no2,co',
                'limit': 100,
                'order_by': 'datetime',
                'sort': 'desc'
            }
            
            headers = {'X-API-Key': self.openaq_api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                measurements = data.get('results', [])
                
                if measurements:
                    return self._process_openaq_measurements(measurements, location)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching OpenAQ data: {str(e)}")
            return None
    
    def _get_location_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get coordinates for any location using geocoding"""
        try:
            # Try to extract coordinates if they're already provided
            if ',' in location:
                try:
                    parts = location.split(',')
                    if len(parts) == 2:
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            return {'lat': lat, 'lon': lon}
                except ValueError:
                    pass
            
            # Use the existing geocoding service
            from .geocoding import GeocodingService
            geocoding_service = GeocodingService()
            
            # Get coordinates for the location
            coords = geocoding_service.geocode(location)
            if coords:
                return {'lat': coords['lat'], 'lon': coords['lon']}
            
            # If geocoding fails, return None to trigger simulated data
            logger.warning(f"Could not geocode location: {location}. Using simulated data.")
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {location}: {e}")
            return None
    
    def _process_openaq_measurements(self, measurements: List[Dict], location: str) -> Dict[str, Any]:
        """Process OpenAQ measurements into our format"""
        # Group measurements by parameter
        param_data = {}
        for measurement in measurements:
            param = measurement.get('parameter')
            value = measurement.get('value')
            if param and value is not None:
                if param not in param_data:
                    param_data[param] = []
                param_data[param].append(value)
        
        # Calculate averages
        processed_data = {
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'source': 'OpenAQ',
            'air_quality': {}
        }
        
        # Process each parameter
        if 'pm25' in param_data:
            processed_data['air_quality']['pm25'] = sum(param_data['pm25']) / len(param_data['pm25'])
        
        if 'o3' in param_data:
            processed_data['air_quality']['o3'] = sum(param_data['o3']) / len(param_data['o3'])
        
        if 'no2' in param_data:
            processed_data['air_quality']['no2'] = sum(param_data['no2']) / len(param_data['no2'])
        
        if 'co' in param_data:
            processed_data['air_quality']['co'] = sum(param_data['co']) / len(param_data['co'])
        
        # Calculate AQI (simplified)
        if 'pm25' in processed_data['air_quality']:
            pm25 = processed_data['air_quality']['pm25']
            if pm25 <= 12:
                aqi = pm25 * 50 / 12
            elif pm25 <= 35.4:
                aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)
            elif pm25 <= 55.4:
                aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
            else:
                aqi = min(300, 150 + (pm25 - 55.4) * 150 / 150)
            
            processed_data['air_quality']['aqi'] = aqi
        
        return processed_data
    
    def _generate_simulated_data(self, location: str) -> Dict[str, Any]:
        """Generate simulated real-time data for demo purposes"""
        import random
        
        # Generate basic simulated data
        data = {
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'source': 'Simulated',
            'air_quality': {
                'pm25': round(random.uniform(5, 35), 2),
                'o3': round(random.uniform(0, 0.1), 3),
                'no2': round(random.uniform(0, 0.1), 3),
                'co': round(random.uniform(0.5, 5), 2),
            }
        }
        
        # Calculate simulated AQI based on PM2.5
        pm25 = data['air_quality']['pm25']
        if pm25 <= 12:
            aqi = pm25 * 50 / 12
        elif pm25 <= 35.4:
            aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)
        elif pm25 <= 55.4:
            aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
        else:
            aqi = min(300, 150 + (pm25 - 55.4) * 150 / 150)
        
        data['air_quality']['aqi'] = round(aqi, 1)
        return data
    
    def get_historical_data(self, location: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """Get historical data for a location"""
        cache_key = f"{location.lower()}_historical_{days}"
        
        # Check cache
        if cache_key in self.historical_cache:
            cached_data = self.historical_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.historical_cache_duration):
                return cached_data['data']
        
        try:
            # Get sensors for location
            sensor_ids = self._get_location_sensors(location)
            if not sensor_ids:
                return None
            
            historical_data = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch historical data from OpenAQ
            for sensor_id in sensor_ids:
                url = "https://api.openaq.org/v2/measurements"
                params = {
                    'date_from': start_date.isoformat() + 'Z',
                    'date_to': end_date.isoformat() + 'Z',
                    'sensor_id': sensor_id,
                    'limit': 1000,
                    'order_by': 'datetime',
                    'sort': 'asc'
                }
                
                headers = {'X-API-Key': self.openaq_api_key}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    historical_data.extend(data.get('results', []))
            
            # Process and format historical data
            processed_data = self._process_historical_data(historical_data)
            
            # Cache the processed data
            self.historical_cache[cache_key] = {
                'data': processed_data,
                'timestamp': datetime.now()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {location}: {str(e)}")
            return None
    
    def _get_location_sensors(self, location: str) -> List[str]:
        """Get OpenAQ sensor IDs for a location"""
        cache_key = f"{location.lower()}_sensors"
        
        # Check cache
        if cache_key in self.sensor_cache:
            cached_data = self.sensor_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.sensor_cache_duration):
                return cached_data['sensor_ids']
        
        try:
            coords = self._get_location_coordinates(location)
            if not coords:
                return []
            
            url = "https://api.openaq.org/v2/sensors"
            params = {
                'coordinates': f"{coords['lat']},{coords['lon']}",
                'radius': 10000,  # 10km radius
                'limit': 100
            }
            
            headers = {'X-API-Key': self.openaq_api_key}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                sensor_ids = [sensor['sensor_id'] for sensor in data.get('results', [])]
                
                # Cache the sensor IDs
                self.sensor_cache[cache_key] = {
                    'sensor_ids': sensor_ids,
                    'timestamp': datetime.now()
                }
                
                return sensor_ids
                
            return []
            
        except Exception as e:
            logger.error(f"Error fetching sensors for {location}: {str(e)}")
            return []
    
    def _process_historical_data(self, measurements: List[Dict]) -> Dict[str, Any]:
        """Process historical measurements into visualization-friendly format"""
        processed = {
            'parameters': {},
            'timestamps': []
        }
        
        # Group measurements by parameter
        for measurement in measurements:
            parameter = measurement.get('parameter')
            value = measurement.get('value')
            timestamp = measurement.get('datetime')
            
            if parameter and value and timestamp:
                if parameter not in processed['parameters']:
                    processed['parameters'][parameter] = []
                processed['parameters'][parameter].append({
                    'timestamp': timestamp,
                    'value': value
                })
                if timestamp not in processed['timestamps']:
                    processed['timestamps'].append(timestamp)
        
        # Sort timestamps
        processed['timestamps'].sort()
        
        return processed
        
        # Base values with some randomness
        base_values = {
            'pm25': random.uniform(10, 40),
            'o3': random.uniform(40, 120),
            'no2': random.uniform(1e15, 4e15),
            'co': random.uniform(1e18, 3e18),
            'pm10': random.uniform(20, 60),
            'so2': random.uniform(5, 25),
            'co_ground': random.uniform(0.5, 3.0)  # Ground CO in ppm
        }
        
        # Add random variations to simulate different air quality patterns
        # In production, this would be based on actual location characteristics
        # (urban vs rural, industrial vs residential, etc.)
        variation_factor = random.uniform(0.7, 1.5)
        base_values['pm25'] *= variation_factor
        base_values['no2'] *= random.uniform(0.8, 1.4)
        base_values['so2'] *= random.uniform(0.6, 1.8)
        
        # Calculate AQI
        pm25 = base_values['pm25']
        if pm25 <= 12:
            aqi = pm25 * 50 / 12
        elif pm25 <= 35.4:
            aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)
        elif pm25 <= 55.4:
            aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
        else:
            aqi = min(300, 150 + (pm25 - 55.4) * 150 / 150)
        
        # Generate time series data for trends
        current_time = datetime.now()
        hourly_data = []
        for i in range(24):  # Last 24 hours
            hour_time = current_time - timedelta(hours=i)
            hourly_data.append({
                'timestamp': hour_time.isoformat(),
                'pm25': round(base_values['pm25'] * random.uniform(0.7, 1.3), 1),
                'o3': round(base_values['o3'] * random.uniform(0.6, 1.4), 1),
                'aqi': round(aqi * random.uniform(0.8, 1.2), 0)
            })
        
        return {
            'location': location,
            'timestamp': current_time.isoformat(),
            'source': 'simulated',
            'air_quality': {
                'pm25': round(base_values['pm25'], 1),
                'pm10': round(base_values['pm10'], 1),
                'o3': round(base_values['o3'], 1),
                'no2': base_values['no2'],
                'so2': round(base_values['so2'], 1),
                'co': base_values['co'],
                'co_ground': round(base_values['co_ground'], 2),
                'aqi': round(aqi, 0),
                'health_risk': self._get_health_risk(aqi)
            },
            'weather_data': {
                'temperature_2m': round(random.uniform(280, 295), 1),
                'temperature_celsius': round(random.uniform(7, 22), 1),
                'pbl_height': random.randint(500, 1500),
                'wind_speed': round(random.uniform(2, 8), 1),
                'wind_direction': random.randint(0, 360),
                'precipitation': round(random.uniform(0, 5), 1),
                'humidity': random.randint(40, 90),
                'pressure': round(random.uniform(1000, 1030), 1),
                'uv_index': random.randint(0, 10)
            },
            'satellite_data': {
                'tempo_no2': random.uniform(1e15, 5e15),
                'tempo_ch2o': random.uniform(5e14, 1e15),
                'tropomi_co': random.uniform(1e18, 4e18),
                'modis_aod': round(random.uniform(0.1, 0.8), 2),
                'cloud_cover': random.randint(0, 100),
                'solar_zenith': random.randint(20, 80)
            },
            'trends': {
                'hourly_data': hourly_data,
                'pm25_trend': random.choice(['increasing', 'decreasing', 'stable']),
                'o3_trend': random.choice(['increasing', 'decreasing', 'stable']),
                'aqi_trend': random.choice(['increasing', 'decreasing', 'stable'])
            },
            'forecast': {
                'next_6h': self._generate_forecast_data(base_values, 6),
                'next_24h': self._generate_forecast_data(base_values, 24)
            }
        }
    
    def _get_health_risk(self, aqi: float) -> str:
        """Get health risk category based on AQI"""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        else:
            return "Very Unhealthy"
    
    def _generate_forecast_data(self, base_values: Dict, hours: int) -> List[Dict]:
        """Generate forecast data for next N hours"""
        import random
        forecast = []
        current_time = datetime.now()
        
        for i in range(1, hours + 1):
            forecast_time = current_time + timedelta(hours=i)
            # Add some variation to base values
            pm25 = base_values['pm25'] * random.uniform(0.8, 1.2)
            o3 = base_values['o3'] * random.uniform(0.7, 1.3)
            
            # Calculate AQI for forecast
            if pm25 <= 12:
                aqi = pm25 * 50 / 12
            elif pm25 <= 35.4:
                aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)
            else:
                aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
            
            forecast.append({
                'timestamp': forecast_time.isoformat(),
                'pm25': round(pm25, 1),
                'o3': round(o3, 1),
                'aqi': round(aqi, 0),
                'health_risk': self._get_health_risk(aqi)
            })
        
        return forecast
    
    def get_dashboard_data(self, location: str) -> Dict[str, Any]:
        """Generate dashboard JSON data for frontend visualization"""
        realtime_data = self.get_realtime_data(location)
        if not realtime_data:
            return {}
        
        # Generate dashboard components
        dashboard_data = {
            'location': location,
            'timestamp': realtime_data['timestamp'],
            'source': realtime_data['source'],
            'components': {
                'aqi_gauge': {
                    'type': 'gauge',
                    'title': 'Air Quality Index',
                    'value': realtime_data['air_quality']['aqi'],
                    'max_value': 300,
                    'color': self._get_aqi_color(realtime_data['air_quality']['aqi']),
                    'status': realtime_data['air_quality']['health_risk'],
                    'unit': 'index'
                },
                'pollutant_chart': {
                    'type': 'bar_chart',
                    'title': 'Pollutant Levels',
                    'data': [
                        {'name': 'PM2.5', 'value': realtime_data['air_quality']['pm25'], 'unit': 'µg/m³', 'color': '#ff6b6b'},
                        {'name': 'PM10', 'value': realtime_data['air_quality']['pm10'], 'unit': 'µg/m³', 'color': '#4ecdc4'},
                        {'name': 'O₃', 'value': realtime_data['air_quality']['o3'], 'unit': 'ppb', 'color': '#45b7d1'},
                        {'name': 'NO₂', 'value': realtime_data['air_quality']['no2'], 'unit': 'molecules/cm²', 'color': '#96ceb4'},
                        {'name': 'SO₂', 'value': realtime_data['air_quality']['so2'], 'unit': 'ppb', 'color': '#feca57'}
                    ]
                },
                'hourly_trend': {
                    'type': 'line_chart',
                    'title': '24-Hour AQI Trend',
                    'x_axis': 'Time',
                    'y_axis': 'AQI',
                    'data': [
                        {
                            'x': point['timestamp'],
                            'y': point['aqi'],
                            'pm25': point['pm25'],
                            'o3': point['o3']
                        }
                        for point in realtime_data['trends']['hourly_data']
                    ]
                },
                'weather_widget': {
                    'type': 'weather_card',
                    'title': 'Current Weather',
                    'data': {
                        'temperature': realtime_data['weather_data']['temperature_celsius'],
                        'humidity': realtime_data['weather_data']['humidity'],
                        'wind_speed': realtime_data['weather_data']['wind_speed'],
                        'wind_direction': realtime_data['weather_data']['wind_direction'],
                        'pressure': realtime_data['weather_data']['pressure'],
                        'uv_index': realtime_data['weather_data']['uv_index']
                    }
                },
                'forecast_chart': {
                    'type': 'forecast_chart',
                    'title': '6-Hour Forecast',
                    'data': [
                        {
                            'time': point['timestamp'],
                            'aqi': point['aqi'],
                            'pm25': point['pm25'],
                            'o3': point['o3'],
                            'health_risk': point['health_risk']
                        }
                        for point in realtime_data['forecast']['next_6h']
                    ]
                },
                'satellite_data': {
                    'type': 'satellite_card',
                    'title': 'Satellite Observations',
                    'data': {
                        'tempo_no2': realtime_data['satellite_data']['tempo_no2'],
                        'tempo_ch2o': realtime_data['satellite_data']['tempo_ch2o'],
                        'tropomi_co': realtime_data['satellite_data']['tropomi_co'],
                        'modis_aod': realtime_data['satellite_data']['modis_aod'],
                        'cloud_cover': realtime_data['satellite_data']['cloud_cover']
                    }
                },
                'trend_indicators': {
                    'type': 'trend_indicators',
                    'title': 'Trend Analysis',
                    'data': {
                        'pm25_trend': {
                            'direction': realtime_data['trends']['pm25_trend'],
                            'icon': self._get_trend_icon(realtime_data['trends']['pm25_trend'])
                        },
                        'o3_trend': {
                            'direction': realtime_data['trends']['o3_trend'],
                            'icon': self._get_trend_icon(realtime_data['trends']['o3_trend'])
                        },
                        'aqi_trend': {
                            'direction': realtime_data['trends']['aqi_trend'],
                            'icon': self._get_trend_icon(realtime_data['trends']['aqi_trend'])
                        }
                    }
                }
            },
            'alerts': {
                'active_alerts': len([a for a in self._get_active_alerts(location) if not a.get('is_resolved', True)]),
                'health_warnings': self._get_health_warnings(realtime_data['air_quality'])
            }
        }
        
        return dashboard_data
    
    def _get_aqi_color(self, aqi: float) -> str:
        """Get color based on AQI value"""
        if aqi <= 50:
            return '#00e400'  # Green
        elif aqi <= 100:
            return '#ffff00'  # Yellow
        elif aqi <= 150:
            return '#ff7e00'  # Orange
        elif aqi <= 200:
            return '#ff0000'  # Red
        else:
            return '#8f3f97'  # Purple
    
    def _get_trend_icon(self, trend: str) -> str:
        """Get icon based on trend direction"""
        if trend == 'increasing':
            return '📈'
        elif trend == 'decreasing':
            return '📉'
        else:
            return '➡️'
    
    def _get_active_alerts(self, location: str) -> List[Dict]:
        """Get active alerts for location"""
        try:
            from .alert_system import alert_system
            # Get recent alerts for this location
            alerts = alert_system.get_alert_history(location=location, hours=1)
            # Filter for unresolved alerts
            active_alerts = [alert for alert in alerts if not alert.get('is_resolved', True)]
            return active_alerts
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def _get_health_warnings(self, air_quality: Dict) -> List[str]:
        """Get health warnings based on air quality"""
        warnings = []
        
        if air_quality['aqi'] > 100:
            warnings.append("Air quality is unhealthy for sensitive groups")
        
        if air_quality['pm25'] > 25:
            warnings.append("PM2.5 levels are elevated - consider reducing outdoor activities")
        
        if air_quality['o3'] > 100:
            warnings.append("Ozone levels are high - avoid outdoor exercise during peak hours")
        
        return warnings
    
    def start_monitoring(self, alert_system):
        """Start monitoring all locations for alerts"""
        def monitoring_loop():
            while True:
                try:
                    for location in list(self.monitoring_locations):
                        data = self.get_realtime_data(location)
                        if data:
                            # Check for alerts
                            triggered_alerts = alert_system.check_alerts(location, data)
                            
                            # Log triggered alerts
                            for alert in triggered_alerts:
                                logger.info(f"Alert triggered for {location}: {alert.message}")
                    
                    # Wait before next check
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(30)
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Real-time monitoring started")

# Global data source instance
realtime_data_source = RealtimeDataSource()
