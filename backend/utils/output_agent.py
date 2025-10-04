"""
Output Agent for processing model predictions and generating user-friendly responses
"""

import json
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()
from .config.ai_config import (
    OUTPUT_AGENT_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    SAFETY_THRESHOLDS,
    CONTEXT_PARAMETERS,
    VISUALIZATION_MAPPING
)

# Configure logging
logger = logging.getLogger(__name__)

class OutputAgent:
    def __init__(self):
        """Initialize the output agent with configuration"""
        self.safety_thresholds = SAFETY_THRESHOLDS
        self.context_parameters = CONTEXT_PARAMETERS
        self.visualization_mapping = VISUALIZATION_MAPPING
        
        # Initialize Gemini model
        api_key = os.getenv('GOOGLE_AI_STUDIO_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_predictions(self, 
                          predictions: Dict, 
                          user_context: Dict) -> Dict:
        """
        Analyze model predictions based on user context and generate API response
        
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
            # Get relevant parameters based on context
            context_type = user_context.get('context_type', 'general')
            analysis_depth = user_context.get('analysis_depth', 'brief')
            relevant_params = self.context_parameters[context_type]
            
            # Analyze each relevant parameter
            analysis_results = {}
            for param in relevant_params:
                if param in self._get_flat_predictions(predictions):
                    analysis_results[param] = self._analyze_parameter(
                        param, 
                        self._get_parameter_value(predictions, param)
                    )
            
            # Generate visualization recommendations
            visualizations = self.visualization_mapping[context_type]
            
            # Create user-friendly response
            response = self._generate_response(
                analysis_results,
                user_context,
                predictions['air_quality']['aqi']
            )
            
            # Determine status code based on analysis
            if not analysis_results:
                status_code = 422  # Unprocessable Entity - not enough data
            else:
                status_code = 200  # Success
                
            return {
                'status_code': status_code,
                'display_text': response,
                'metadata': {
                    'status': 'success',
                    'analysis': {
                        'results': analysis_results,
                        'recommendations': self._generate_recommendations(analysis_results, context_type),
                        'suggested_visualizations': visualizations
                    },
                    'context': {
                        'analyzed_parameters': list(analysis_results.keys()),
                        'context_type': context_type,
                        'analysis_depth': analysis_depth,
                        'original_prompt': user_context.get('original_prompt', '')
                    }
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in analyze_predictions: {error_msg}")
            
            return {
                'status_code': 500,  # Internal Server Error
                'display_text': "I apologize, but I'm having trouble analyzing the air quality data right now. Please try again in a moment.",
                'metadata': {
                    'status': 'error',
                    'error': error_msg
                }
            }
    
    def _get_flat_predictions(self, predictions: Dict) -> Dict:
        """Flatten nested predictions dictionary"""
        flat_dict = {}
        for category, values in predictions.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    flat_dict[key] = value
            else:
                flat_dict[category] = values
        return flat_dict
    
    def _get_parameter_value(self, predictions: Dict, param: str) -> float:
        """Extract parameter value from nested predictions"""
        flat_predictions = self._get_flat_predictions(predictions)
        return flat_predictions.get(param)
    
    def _analyze_parameter(self, param: str, value: float) -> Dict:
        """Analyze a single parameter against safety thresholds"""
        if param not in self.safety_thresholds:
            return {'status': 'unknown', 'value': value}
            
        thresholds = self.safety_thresholds[param]
        
        if value <= thresholds['good']:
            status = 'good'
        elif value <= thresholds['moderate']:
            status = 'moderate'
        else:
            status = 'unhealthy'
            
        return {
            'status': status,
            'value': value,
            'thresholds': thresholds
        }
    
    def _generate_recommendations(self, 
                                analysis_results: Dict,
                                context_type: str) -> List[str]:
        """Generate context-specific recommendations based on analysis"""
        recommendations = []
        
        # Add general recommendations
        if context_type == 'outdoor_activity':
            if all(result['status'] == 'good' 
                  for result in analysis_results.values()):
                recommendations.append(
                    "Perfect conditions for outdoor activities! 🌟"
                )
            else:
                recommendations.append(
                    "Consider indoor activities or wear appropriate protection 😷"
                )
                
        elif context_type == 'industrial':
            if any(result['status'] == 'unhealthy' 
                  for result in analysis_results.values()):
                recommendations.append(
                    "Industrial emissions are high - extra ventilation recommended 🏭"
                )
        
        # Add parameter-specific recommendations
        for param, result in analysis_results.items():
            if result['status'] == 'unhealthy':
                if param == 'pm25':
                    recommendations.append(
                        "Consider using air purifiers indoors 🏠"
                    )
                elif param == 'o3':
                    recommendations.append(
                        "Ozone levels are high - best to stay indoors during peak sun ☀️"
                    )
                    
        return recommendations
    
    def _generate_response(self, 
                          analysis_results: Dict,
                          user_context: Dict,
                          predictions: Dict) -> str:
        """Generate a user-friendly response using Gemini"""
        try:
            # Format the data for the prompt
            air_quality_data = json.dumps(predictions, indent=2)
            analysis_data = json.dumps(analysis_results, indent=2)
            
            # Prepare the prompt with all context
            prompt = RESPONSE_GENERATION_PROMPT.format(
                air_quality_data=air_quality_data,
                location=user_context.get('location', 'not specified'),
                time=user_context.get('time_descriptor', 'not specified'),
                context_type=user_context.get('context_type', 'general'),
                analysis_depth=user_context.get('analysis_depth', 'brief'),
                special_concerns=", ".join(user_context.get('special_concerns', [])),
                analysis_results=analysis_data
            )
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            # Extract and return the generated response
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ("I apologize, but I'm having trouble generating a detailed response. "
                   f"The air quality index is {predictions['air_quality']['aqi']}. "
                   "Please check the analysis results for more information.")