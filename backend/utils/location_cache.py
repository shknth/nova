"""
Geocoding cache for frequently accessed locations
"""

# Pre-computed coordinates for major North American cities
MAJOR_CITIES_CACHE = {
    # United States
    'new york': {'lat': 40.7128, 'lon': -74.0060},
    'los angeles': {'lat': 34.0522, 'lon': -118.2437},
    'chicago': {'lat': 41.8781, 'lon': -87.6298},
    'houston': {'lat': 29.7604, 'lon': -95.3698},
    'phoenix': {'lat': 33.4484, 'lon': -112.0740},
    'philadelphia': {'lat': 39.9526, 'lon': -75.1652},
    'san antonio': {'lat': 29.4241, 'lon': -98.4936},
    'san diego': {'lat': 32.7157, 'lon': -117.1611},
    'dallas': {'lat': 32.7767, 'lon': -96.7970},
    'san jose': {'lat': 37.3382, 'lon': -121.8863},
    'austin': {'lat': 30.2672, 'lon': -97.7431},
    'san francisco': {'lat': 37.7749, 'lon': -122.4194},
    'seattle': {'lat': 47.6062, 'lon': -122.3321},
    'denver': {'lat': 39.7392, 'lon': -104.9903},
    'washington dc': {'lat': 38.9072, 'lon': -77.0369},
    'boston': {'lat': 42.3601, 'lon': -71.0589},
    'las vegas': {'lat': 36.1699, 'lon': -115.1398},
    'miami': {'lat': 25.7617, 'lon': -80.1918},
    'atlanta': {'lat': 33.7490, 'lon': -84.3880},
    
    # Canada
    'toronto': {'lat': 43.6532, 'lon': -79.3832},
    'montreal': {'lat': 45.5017, 'lon': -73.5673},
    'vancouver': {'lat': 49.2827, 'lon': -123.1207},
    'calgary': {'lat': 51.0447, 'lon': -114.0719},
    'ottawa': {'lat': 45.4215, 'lon': -75.6972},
    'edmonton': {'lat': 53.5461, 'lon': -113.4938},
    'quebec city': {'lat': 46.8139, 'lon': -71.2080},
    'winnipeg': {'lat': 49.8951, 'lon': -97.1384},
    'halifax': {'lat': 44.6488, 'lon': -63.5752},
    
    # Mexico
    'mexico city': {'lat': 19.4326, 'lon': -99.1332},
    'guadalajara': {'lat': 20.6597, 'lon': -103.3496},
    'monterrey': {'lat': 25.6866, 'lon': -100.3161},
    'tijuana': {'lat': 32.5149, 'lon': -117.0382},
    'ciudad juarez': {'lat': 31.6904, 'lon': -106.4245}
}

def get_cached_coordinates(location: str) -> dict:
    """
    Get coordinates for a location from the cache.
    
    Args:
        location (str): Location name to look up
        
    Returns:
        dict: Dictionary with 'lat' and 'lon' if found, None if not in cache
    """
    # Normalize the location string
    normalized_location = location.lower().strip()
    
    # Try exact match first
    if normalized_location in MAJOR_CITIES_CACHE:
        return MAJOR_CITIES_CACHE[normalized_location]
    
    # Try partial matches (e.g., "new york city" -> "new york")
    for city in MAJOR_CITIES_CACHE:
        if city in normalized_location or normalized_location in city:
            return MAJOR_CITIES_CACHE[city]
    
    return None