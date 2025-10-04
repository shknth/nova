from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from utils import InputAgent, OutputAgent

# Load environment variables
load_dotenv()

# Initialize Flask app and components
app = Flask(__name__)
CORS(app)
input_agent = InputAgent()
output_agent = OutputAgent()

# Error handling
class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'success',
        'message': 'Service is running'
    })

# Main parameter extraction endpoint
@app.route('/api/extract-parameters', methods=['POST'])
def extract_parameters():
    app.logger.info("=== New Request Received ===")
    
    if not request.is_json:
        app.logger.error("Error: Request is not JSON")
        return jsonify({
            'status_code': 400,
            'display_text': "Invalid request format. Please provide a JSON request.",
            'metadata': {
                'status': 'error',
                'error': 'Request must be JSON'
            }
        }), 400

    try:
        data = request.get_json()
        app.logger.info(f"Request data: {data}")
    except Exception as e:
        app.logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({
            'status_code': 400,
            'display_text': "Invalid JSON format. Please check your request format.",
            'metadata': {
                'status': 'error',
                'error': 'Invalid JSON'
            }
        }), 400
    
    if 'prompt' not in data:
        app.logger.error("Error: Missing prompt field")
        return jsonify({
            'status_code': 400,
            'display_text': "I didn't receive any question. What would you like to know about the air quality?",
            'metadata': {
                'status': 'error',
                'error': 'Missing prompt in request'
            }
        }), 400
    
    if not isinstance(data['prompt'], str) or not data['prompt'].strip():
        app.logger.error("Error: Invalid prompt format")
        return jsonify({
            'status_code': 400,
            'display_text': "I didn't receive a valid question. Could you please rephrase your query?",
            'metadata': {
                'status': 'error',
                'error': 'Invalid prompt format'
            }
        }), 400

    try:
        app.logger.info("Processing request...")
        # Extract parameters using Input Agent
        extracted_params = input_agent.extract_parameters(data['prompt'])
        
        # Add original prompt to parameters
        extracted_params['original_prompt'] = data['prompt']
        
        # Get model predictions (placeholder for now)
        predictions = {
            "satellite_data": {
                "tempo_no2": 2.5e15,
                "tempo_ch2o": 8e14,
                "tropomi_co": 1.8e18,
                "modis_aod": 0.25
            },
            "weather_data": {
                "temperature_2m": 285.5,
                "pbl_height": 800,
                "wind_speed": 5.2,
                "precipitation": 0.0
            },
            "air_quality": {
                "pm25": 28.5,
                "o3": 85.2,
                "aqi": 95
            }
        }
        
        # Generate response using Output Agent
        result = output_agent.analyze_predictions(predictions, extracted_params)
        
        app.logger.info(f"Final response: {result}")
        app.logger.info("=== Request Processing Completed ===")
        
        return jsonify(result), result['status_code']
        
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'status_code': 500,
            'display_text': "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
            'metadata': {
                'status': 'error',
                'error': str(e)
            }
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)