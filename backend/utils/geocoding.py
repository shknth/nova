import requests
from typing import Dict, Optional, Tuple
import time

class GeocodingService:
    def __init__(self):
        # Using OpenStreetMap Nominatim (free, no API key required)
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'NASA-SpaceApps-AirQuality/1.0'
        }
        
        # Cache for frequently requested locations
        self.location_cache = {
            # Major US cities (pre-cached for faster response)
            'los angeles': {'lat': 34.0522, 'lon': -118.2437, 'display_name': 'Los Angeles, CA, USA'},
            'new york': {'lat': 40.7128, 'lon': -74.0060, 'display_name': 'New York, NY, USA'},
            'chicago': {'lat': 41.8781, 'lon': -87.6298, 'display_name': 'Chicago, IL, USA'},
            'houston': {'lat': 29.7604, 'lon': -95.3698, 'display_name': 'Houston, TX, USA'},
            'phoenix': {'lat': 33.4484, 'lon': -112.0740, 'display_name': 'Phoenix, AZ, USA'},
            'philadelphia': {'lat': 39.9526, 'lon': -75.1652, 'display_name': 'Philadelphia, PA, USA'},
            'san antonio': {'lat': 29.4241, 'lon': -98.4936, 'display_name': 'San Antonio, TX, USA'},
            'san diego': {'lat': 32.7157, 'lon': -117.1611, 'display_name': 'San Diego, CA, USA'},
            'dallas': {'lat': 32.7767, 'lon': -96.7970, 'display_name': 'Dallas, TX, USA'},
            'san jose': {'lat': 37.3382, 'lon': -121.8863, 'display_name': 'San Jose, CA, USA'},
            'austin': {'lat': 30.2672, 'lon': -97.7431, 'display_name': 'Austin, TX, USA'},
            'denver': {'lat': 39.7392, 'lon': -104.9903, 'display_name': 'Denver, CO, USA'},
            'seattle': {'lat': 47.6062, 'lon': -122.3321, 'display_name': 'Seattle, WA, USA'},
            'atlanta': {'lat': 33.7490, 'lon': -84.3880, 'display_name': 'Atlanta, GA, USA'},
            'miami': {'lat': 25.7617, 'lon': -80.1918, 'display_name': 'Miami, FL, USA'}
        }
    
    def geocode(self, location_name: str) -> Optional[Dict[str, float]]:
        """
        Convert location name to coordinates
        
        Args:
            location_name: Name of the location (e.g., "Los Angeles", "New York")
            
        Returns:
            Dictionary with 'lat', 'lon', and 'display_name' or None if not found
        """
        if not location_name:
            return None
            
        # Normalize location name
        normalized_name = location_name.lower().strip()
        
        # Check cache first
        if normalized_name in self.location_cache:
            return self.location_cache[normalized_name]
        
        try:
            # Make API request to Nominatim
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us',  # Focus on US locations for air quality data
                'addressdetails': 1
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    result = data[0]
                    
                    location_info = {
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result.get('display_name', location_name)
                    }
                    
                    # Cache the result
                    self.location_cache[normalized_name] = location_info
                    
                    # Be nice to the free API - add small delay
                    time.sleep(0.1)
                    
                    return location_info
                    
            return None
            
        except Exception as e:
            print(f"Geocoding error for '{location_name}': {str(e)}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Convert coordinates to location name
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Location name or None if not found
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = requests.get(
                url, 
                params=params, 
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'display_name' in data:
                    # Be nice to the free API
                    time.sleep(0.1)
                    return data['display_name']
                    
            return None
            
        except Exception as e:
            print(f"Reverse geocoding error for ({lat}, {lon}): {str(e)}")
            return None
    
    def is_valid_coordinates(self, lat: float, lon: float) -> bool:
        """
        Check if coordinates are valid for North America (our data coverage)
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are within North America bounds
        """
        # North America bounds (roughly)
        return (20.0 <= lat <= 70.0) and (-170.0 <= lon <= -50.0)
    
    def get_city_info(self, location_name: str) -> Optional[Dict]:
        """
        Get comprehensive city information including coordinates and metadata
        
        Args:
            location_name: Name of the location
            
        Returns:
            Dictionary with location info or None
        """
        coords = self.geocode(location_name)
        
        if coords:
            return {
                'name': location_name,
                'display_name': coords['display_name'],
                'coordinates': {
                    'latitude': coords['lat'],
                    'longitude': coords['lon']
                },
                'is_valid_for_prediction': self.is_valid_coordinates(coords['lat'], coords['lon']),
                'region': 'North America' if self.is_valid_coordinates(coords['lat'], coords['lon']) else 'Outside Coverage'
            }
        
        return None