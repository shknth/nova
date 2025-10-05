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
            "context_type": "one of: industrial, traffic, residential, health, outdoor_activity, general",
            "analysis_depth": "brief or detailed",
            "special_concerns": ["list of specific concerns or requirements mentioned"],
            "query_intent": "the main purpose of the query (forecast, analysis, validation, etc.)"
        }
        Consider:
        - "industrial area", "industrial park", "factory", "manufacturing" → industrial
        - "asthma", "respiratory", "health" → health
        - "outdoor activities", "exercise", "sports" → outdoor_activity
        - "traffic", "highway", "road" → traffic
        - "this month", "this week", "today" → detailed analysis
        - "quick", "brief" → brief analysis
        - "understand", "analyze", "source" → analysis intent
        - "forecast", "prediction" → forecast intent
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
                required_fields = ['location', 'time_descriptor', 'context_type', 'analysis_depth', 'special_concerns', 'query_intent']
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
                    'context_type': None,
                    'analysis_depth': None,
                    'special_concerns': None,
                    'query_intent': None
                }
                
        except Exception as e:
            # Log the error
            current_app.logger.error(f"Error in Gemini API call: {str(e)}")
            raise

    def validate_parameters(self, params: Dict[str, Optional[str]]) -> Dict[str, Union[str, list]]:
        """
        Use AI to validate parameters and determine if more information is needed
        """
        from flask import current_app
        current_app.logger.info("=== AI Parameter Validation Started ===")
        
        # Use AI to validate and determine if more information is needed
        validation_prompt = f"""Analyze these extracted parameters and determine if they are sufficient for air quality analysis:

Parameters: {json.dumps(params, indent=2)}

Respond with ONLY a JSON object in this format:
{{
    "sufficient": true/false,
    "missing_information": ["list of missing critical information"],
    "validation_message": "brief message about what's missing or confirmation that parameters are sufficient"
}}

Consider:
- Location is critical for any air quality query
- Time reference helps determine forecast vs current conditions
- Context type helps determine analysis approach
- Query intent helps understand what the user wants

Return ONLY the raw JSON object."""
        
        try:
            response = self.model.generate_content(validation_prompt)
            validation_result = json.loads(response.text.strip())
            
            current_app.logger.info(f"AI Validation result: {validation_result}")
            
            if validation_result.get('sufficient', False):
                return {
                    'status_code': 200,
                    'display_text': "Parameters validated successfully",
                    'metadata': {
                        'status': 'success',
                        'extracted_parameters': params,
                        'validation_message': validation_result.get('validation_message', 'Parameters are sufficient')
                    }
                }
            else:
                missing_info = validation_result.get('missing_information', [])
                return {
                    'status_code': 422,
                    'display_text': f"I need more information to provide an accurate analysis. {validation_result.get('validation_message', 'Please provide more details.')}",
                    'metadata': {
                        'status': 'incomplete',
                        'missing_information': missing_info,
                        'extracted_parameters': params,
                        'validation_message': validation_result.get('validation_message', 'Missing critical information')
                    }
                }
                
        except Exception as e:
            current_app.logger.error(f"Error in AI validation: {str(e)}")
            # Fallback to basic validation
            if not params.get('location'):
                return {
                    'status_code': 422,
                    'display_text': "I need to know the location to provide air quality information. Where would you like to check?",
                    'metadata': {
                        'status': 'incomplete',
                        'missing_information': ['location'],
                        'extracted_parameters': params
                    }
                }
            return {
                'status_code': 200,
                'display_text': "Parameters validated successfully",
                'metadata': {
                    'status': 'success',
                    'extracted_parameters': params
                }
            }