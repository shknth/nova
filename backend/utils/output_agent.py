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
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_predictions(self, 
                          predictions: Dict, 
                          user_context: Dict) -> Dict:
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
{json.dumps(predictions, indent=2)}

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
                }
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