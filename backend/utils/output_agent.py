"""
Output Agent for processing model predictions and generating user-friendly responses
"""

import json
import logging
import os
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from .visualization_config import VISUALIZATION_MAPPINGS, SUPPORTED_VISUALIZATIONS

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class OutputAgent:
    def __init__(self):
        """Initialize the output agent with AI model"""
        
        # Initialize Gemini model
        api_key = os.getenv('GOOGLE_AI_STUDIO_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def analyze_predictions(self, 
                          predictions: Dict, 
                          user_context: Dict,
                          lat: float,
                          lon: float,
                          location_name: str) -> Dict:
        """
        Use AI to analyze model predictions and generate intelligent response
        
        Args:
            predictions: Dictionary containing model predictions
            user_context: Dictionary containing extracted user context
            
        Returns:
            Dictionary containing {
                'status_code': int,
                'display_text': str,
                'metadata': Dict containing analysis results and context
            }
        """
        try:
            # Convert numpy values to Python native types
            def convert_numpy_values(obj: Any) -> Any:
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return round(float(obj), 2)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_values(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_numpy_values(item) for item in obj]
                return obj
            
            # Convert predictions before JSON serialization
            converted_predictions = convert_numpy_values(predictions)
            
            # Use AI to analyze predictions and generate response
            analysis_prompt = f"""You are an expert air quality analyst. Analyze the provided data and user context to generate a comprehensive response.

USER QUERY: {user_context.get('original_prompt', 'Unknown query')}

EXTRACTED CONTEXT:
- Location: {user_context.get('location', 'Not specified')}
- Time: {user_context.get('time_descriptor', 'Not specified')}
- Context Type: {user_context.get('context_type', 'general')}
- Analysis Depth: {user_context.get('analysis_depth', 'brief')}
- Special Concerns: {user_context.get('special_concerns', [])}
- Query Intent: {user_context.get('query_intent', 'analysis')}

AIR QUALITY DATA:
{json.dumps(converted_predictions, indent=2)}

Generate a response that:
1. Directly addresses the user's specific query and location
2. Analyzes the air quality data in context of their request
3. Provides relevant insights based on the context type (industrial, health, etc.)
4. Includes actionable recommendations
5. Suggests relevant visualizations or next steps
6. Uses an appropriate tone for the context

CRITICAL: You must respond with ONLY a valid JSON object. No markdown, no code blocks, no additional text.

Example format:
{{
    "display_text": "Based on the air quality data for Cabinteely Park this evening, the conditions are good for jogging with an AQI of 42.",
    "analysis_results": {{
        "aqi": {{
            "value": 42,
            "status": "good",
            "interpretation": "Air quality is good for outdoor activities"
        }},
        "pm25": {{
            "value": 15.2,
            "status": "good",
            "interpretation": "PM2.5 levels are within healthy range"
        }}
    }},
    "recommendations": ["Perfect conditions for jogging", "Consider going in the early evening for best air quality"],
    "suggested_visualizations": ["aqi_gauge", "hourly_forecast"],
    "status_code": 200
}}

Now generate your response:"""
            
            response = self.model.generate_content(analysis_prompt)
            
            # Clean and validate the response
            response_text = response.text.strip()
            logger.info(f"Raw AI response: {response_text}")
            
            # Remove any markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```
            
            response_text = response_text.strip()
            
            # Validate JSON
            if not response_text:
                raise ValueError("Empty response from AI model")
            
            analysis_result = json.loads(response_text)
            
            # Build dashboard details
            dashboard_details = self.build_dashboard_details(
                predictions=converted_predictions,
                location=user_context.get('location', 'Unknown'),
                suggested_vis=analysis_result.get('suggested_visualizations', []),
                latitude=lat,
                longitude=lon,
                location_name=location_name
            )

            return {
                'status_code': analysis_result.get('status_code', 200),
                'display_text': analysis_result.get('display_text', 'Analysis completed'),
                'metadata': {
                    'status': 'success',
                    'analysis': {
                        'results': analysis_result.get('analysis_results', {}),
                        'recommendations': analysis_result.get('recommendations', []),
                        'suggested_visualizations': analysis_result.get('suggested_visualizations', [])
                    },
                    'context': {
                        'analyzed_parameters': list(analysis_result.get('analysis_results', {}).keys()),
                        'context_type': user_context.get('context_type', 'general'),
                        'analysis_depth': user_context.get('analysis_depth', 'brief'),
                        'original_prompt': user_context.get('original_prompt', '')
                    }
                },
                'dashboard_details': dashboard_details
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(f"Error parsing AI response: {error_msg}")
            
            # Fallback response
            return {
                'status_code': 200,
                'display_text': f"Based on the air quality data for {user_context.get('location', 'your location')}, the current AQI is {predictions.get('air_quality', {}).get('aqi', 'unknown')}. Please check the detailed analysis results for more information.",
                'metadata': {
                    'status': 'partial_success',
                    'analysis': {
                        'results': {},
                        'recommendations': ['Check local air quality updates regularly'],
                        'suggested_visualizations': ['aqi_gauge', 'daily_forecast']
                    },
                    'context': {
                        'analyzed_parameters': [],
                        'context_type': user_context.get('context_type', 'general'),
                        'analysis_depth': user_context.get('analysis_depth', 'brief'),
                        'original_prompt': user_context.get('original_prompt', '')
                    },
                    'error': error_msg
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in AI analysis: {error_msg}")
            
            return {
                'status_code': 500,
                'display_text': "I apologize, but I'm having trouble analyzing the air quality data right now. Please try again in a moment.",
                'metadata': {
                    'status': 'error',
                    'error': error_msg
                }
            }

    def build_dashboard_details(self, predictions: Dict, location: str, suggested_vis: List[str], latitude: float, longitude: float, location_name: str) -> Dict:
        """
        Build the dashboard details from predictions and visualization suggestions
        
        Args:
            predictions: Dictionary containing model predictions
            location: Location name
            suggested_vis: List of visualization suggestions from AI
            lat: Latitude of the location
            lon: Longitude of the location
            location_name: Name of the location
            
        Returns:
            Dictionary containing dashboard configuration and data
        """

        # Get AQI and other metrics
        aqi = predictions.get('air_quality', {}).get('aqi', 0)
        
        # Include coordinates in dashboard details
        # coordinates = {
        #     'lat': lat,
        #     'lon': lon
        # }

        # Map suggested visualizations to our supported types
        visualizations = []
        for suggestion in suggested_vis:
            # Convert suggestion to lowercase for matching
            suggestion_lower = suggestion.lower()
            matched_vis_type = None
            
            # First, try exact matches
            for pattern, vis_type in VISUALIZATION_MAPPINGS.items():
                if pattern.lower() == suggestion_lower:
                    matched_vis_type = vis_type
                    break
            
            # If no exact match, try partial matches
            if not matched_vis_type:
                for pattern, vis_type in VISUALIZATION_MAPPINGS.items():
                    pattern_parts = pattern.lower().split('_')
                    # Check if any part of the pattern matches the suggestion
                    if any(part in suggestion_lower for part in pattern_parts):
                        matched_vis_type = vis_type
                        break
            
            if matched_vis_type and matched_vis_type in SUPPORTED_VISUALIZATIONS:
                vis_config = SUPPORTED_VISUALIZATIONS[matched_vis_type].copy()
                # Add the data needed for this visualization, with coordinates
                vis_config['data'] = self._extract_visualization_data(
                    predictions=predictions,
                    vis_type=matched_vis_type,
                    latitude=latitude,
                    longitude=longitude,
                    location_name=location_name,
                    suggestion=suggestion_lower
                )
                visualizations.append(vis_config)

        return {
            'location': location_name,
            'aqi': aqi,
            'visualizations': visualizations
        }

    def _extract_visualization_data(self, predictions: Dict, vis_type: str, lat: float, lon: float, location_name: str = '', suggestion: str = '') -> Dict:
        """
        Extract the required data for a specific visualization type
        
        Args:
            predictions: Dictionary containing model predictions
            vis_type: Type of visualization to generate data for
            lat: Latitude of the location
            lon: Longitude of the location
            location_name: Name of the location
            suggestion: Original visualization suggestion from AI
            
        Returns:
            Dictionary containing the data needed for the visualization
        """
        vis_config = SUPPORTED_VISUALIZATIONS[vis_type]
        required_fields = vis_config['data_fields']
        
        if vis_type == 'pollutant_map':
            # Get location data from predictions
            # coords = predictions.get('location_info', {}).get('coordinates', {})
            # lat = coords.get('latitude') or predictions.get('latitude', 40.7128)  # Default to NY coordinates
            # lon = coords.get('longitude') or predictions.get('longitude', -74.0060)
            
            # Default to AQI if no specific pollutant mentioned
            value = predictions.get('air_quality', {}).get('aqi', 0)
            title = "Air Quality Index Map"
            
            # Check for specific pollutants in the suggestion
            if 'no2' in suggestion:
                value = predictions.get('tempo_data', {}).get('no2', 4.72)  # Get from TEMPO data
                title = "NO2 Concentration Map"
            elif 'aod' in suggestion:
                value = predictions.get('modis_data', {}).get('aod', 1.11)  # Get from MODIS data
                title = "Aerosol Optical Depth Map"
            elif 'ch2o' in suggestion:
                value = predictions.get('tempo_data', {}).get('ch2o', 4.78)  # Get from TEMPO data
                title = "Formaldehyde Concentration Map"
            
            return {
                'lat': lat,
                'lon': lon,
                'value': value,
                'title': title
            }
        elif vis_type == 'wind_rose':
            wind_data = predictions.get('meteorological_data', {})
            return {
                'direction': wind_data.get('wind_direction', 180),  # Default wind direction
                'speed': wind_data.get('wind_speed', 24.49)  # Use actual wind speed from data
            }
        elif vis_type == 'time_series':
            current_time = predictions.get('timestamp') or datetime.now().isoformat()
            
            # Get the appropriate value based on suggestion
            value = predictions.get('air_quality', {}).get('aqi', 38.92)  # Default to AQI
            if 'no2' in suggestion:
                value = predictions.get('tempo_data', {}).get('no2', 4.72)
            elif 'ch2o' in suggestion:
                value = predictions.get('tempo_data', {}).get('ch2o', 4.78)
            elif 'pm25' in suggestion:
                value = predictions.get('air_quality', {}).get('pm25', 9.34)
            
            return {
                'timestamp': current_time,
                'value': value
            }
        elif vis_type == 'box_plot':
            # Extract historical data if available
            return {
                'values': predictions.get('historical_data', {}).get('aqi_values', [38.92, 35.5, 42.1, 39.8]),  # Sample values
                'categories': predictions.get('historical_data', {}).get('timeframes', ["Morning", "Afternoon", "Evening", "Night"])
            }
        
        return {}

