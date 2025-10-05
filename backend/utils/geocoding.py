import requests
from typing import Dict, Optional, Tuple
import time
from .location_cache import MAJOR_CITIES_CACHE, get_cached_coordinates

class GeocodingService:
    def __init__(self):
        # Using OpenStreetMap Nominatim (free, no API key required)
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'NASA-SpaceApps-AirQuality/1.0'
        }
        
        # Initialize with static cache and runtime cache
        self.location_cache = dict(MAJOR_CITIES_CACHE)  # Start with major cities
    
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
        
        # First check the static cache using smart matching
        cached_result = get_cached_coordinates(normalized_name)
        if cached_result:
            display_name = location_name  # Use original name for display
            cached_result['display_name'] = display_name
            return cached_result
        
        # Then check runtime cache
        if normalized_name in self.location_cache:
            return self.location_cache[normalized_name]
        
        try:
            # If not in any cache, make API request to Nominatim (global search)
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
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
        Check if coordinates are valid globally
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are valid global coordinates
        """
        # Global bounds
        return (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0)
    
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
                'region': 'Global' if self.is_valid_coordinates(coords['lat'], coords['lon']) else 'Invalid Coordinates'
            }
        
        return None