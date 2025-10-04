import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from typing import Dict, Optional, Union
from .config.ai_config import INPUT_AGENT_PROMPT

# Load environment variables
load_dotenv()

class InputAgent:
    def __init__(self):
        api_key = os.getenv('GOOGLE_AI_STUDIO_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # System prompt for parameter extraction
        self.system_prompt = """Extract parameters from the input and respond with ONLY a JSON object (no markdown, no code blocks) in this format:
        {
            "location": "the location mentioned in the text, or null if none found",
            "time_descriptor": "any time reference mentioned, or null if none found",
            "health_context": "any health or activity context mentioned, or null if none found"
        }
        DO NOT wrap the JSON in code blocks. Return ONLY the raw JSON object."""

    def extract_parameters(self, prompt: str) -> Dict[str, Optional[str]]:
        try:
            from flask import current_app
            current_app.logger.info("=== Parameter Extraction Started ===")
            current_app.logger.info(f"Input prompt: {prompt}")
            
            # Combine system prompt with user query
            full_prompt = f"{self.system_prompt}\n\nInput text: {prompt}"
            
            # Generate response with minimal configuration
            current_app.logger.info("Calling Gemini API...")
            response = self.model.generate_content(full_prompt)
            
            current_app.logger.info(f"Raw Gemini response: {response.text}")
            
            try:
                # Extract the JSON part from the response
                json_str = response.text.strip()
                
                # Remove code block markers if present
                if json_str.startswith('```'):
                    json_str = json_str.split('\n', 1)[1]  # Remove first line with ```json
                if json_str.endswith('```'):
                    json_str = json_str.rsplit('\n', 1)[0]  # Remove last line with ```
                
                # Parse the JSON
                extracted_params = json.loads(json_str)
                
                current_app.logger.info("Extracted parameters:")
                for key, value in extracted_params.items():
                    current_app.logger.info(f"{key}: {value}")
                
                # Validate required fields
                required_fields = ['location', 'time_descriptor', 'health_context']
                for field in required_fields:
                    if field not in extracted_params:
                        current_app.logger.info(f"Missing required field: {field}")
                        extracted_params[field] = None
                
                current_app.logger.info("=== Parameter Extraction Completed ===")
                return extracted_params
            
            except json.JSONDecodeError:
                # If response is not valid JSON, return None for all parameters
                return {
                    'location': None,
                    'time_descriptor': None,
                    'health_context': None
                }
                
        except Exception as e:
            # Log the error
            current_app.logger.error(f"Error in Gemini API call: {str(e)}")
            raise

    def validate_parameters(self, params: Dict[str, Optional[str]]) -> Dict[str, Union[str, list]]:
        """
        Validate the extracted parameters and return appropriate response format
        """
        from flask import current_app
        current_app.logger.info("=== Parameter Validation Started ===")
        missing = []
        
        # Check for required parameters
        if not params.get('location'):
            missing.append('location')
            current_app.logger.info("Missing required parameter: location")
            
        # Time is required for forecasting
        if not params.get('time_descriptor'):
            missing.append('time_descriptor')
            current_app.logger.info("Missing required parameter: time_descriptor")
        
        # Health context is optional, so we don't check for it
        current_app.logger.info(f"Optional parameter 'health_context': {params.get('health_context')}")
        
        # Generate display text (hardcoded for now)
        if missing:
            display_text = f"I need more information to provide an accurate forecast. Could you please specify the {' and '.join(missing)}?"
            status_code = 422  # Unprocessable Entity
            current_app.logger.info(f"Validation failed. Missing: {missing}")
        else:
            # Hardcoded response for testing
            location = params['location']
            time = params['time_descriptor']
            health_context = params.get('health_context', 'general conditions')
            
            display_text = f"Based on the forecasted conditions for {location} {time}, "
            if health_context:
                display_text += f"considering {health_context}, "
            display_text += "the air quality is expected to be good with an AQI of 42. It's a great time for outdoor activities!"
            status_code = 200
            current_app.logger.info("Validation successful")
        
        current_app.logger.info("=== Parameter Validation Completed ===")
        
        if missing:
            return {
                'status_code': status_code,
                'display_text': display_text,
                'metadata': {
                    'status': 'incomplete',
                    'missing_information': missing,
                    'extracted_parameters': params
                }
            }
            
        return {
            'status_code': status_code,
            'display_text': display_text,
            'metadata': {
                'status': 'success',
                'extracted_parameters': params
            }
        }