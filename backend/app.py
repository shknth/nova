from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import sys
import logging
import numpy as np
from datetime import datetime
from utils import InputAgent, OutputAgent
from utils.alert_system import alert_system, AlertType, AlertSeverity
from utils.alert_templates import AlertTemplates, AlertUIComponents
from model_design import AirQualityPredictor
from utils.geocoding import GeocodingService


# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Initialize Flask app and components
app = Flask(__name__)
CORS(app)
input_agent = InputAgent()
output_agent = OutputAgent()


# Initialize ML model and geocoding service
print("🚀 Initializing Air Quality Prediction Model...")
predictor = AirQualityPredictor()
geocoding_service = GeocodingService()

# Load and train model on startup
try:
    predictor.load_data(dry_run=False)  # Use full dataset
    X, y = predictor.prepare_features()
    predictor.train_model(X, y)
    print("✅ Model trained and ready for predictions!")
except Exception as e:
    print(f"⚠️  Model training failed, using dry run mode: {str(e)}")
    # Fallback to dry run mode
    predictor.load_data(dry_run=True, sample_size=100)
    X, y = predictor.prepare_features()
    predictor.train_model(X, y)
    print("✅ Model trained in dry run mode!")

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

# Frontend metrics endpoint
@app.route('/api/weather-metrics', methods=['GET'])
def get_weather_metrics():
    """Get basic weather metrics for frontend landing page"""
    try:
        # Default location (can be made configurable)
        default_location = request.args.get('location', 'Athlone')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Getting frontend metrics for {default_location}")
        
        # Get coordinates for default location
        coords = geocoding_service.geocode(default_location)

        if coords:
            lat, lon = coords['lat'], coords['lon']
            location_name = coords['display_name']
        else:
            # Fallback to New York coordinates
            lat, lon = 40.7128, -74.0060
        
        # Get comprehensive predictions
        predictions = predictor.predict_comprehensive(lat, lon, current_time)

        # Convert numpy types to native Python types and round to 2 decimal places
        metrics = predictions['frontend_metrics']
        converted_metrics = {k: round(float(v), 2) if hasattr(v, 'item') else v for k, v in metrics.items()}

        # Return just the frontend metrics
        return jsonify({
            'status': 'success',
            'location': default_location,
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': current_time,
            'metrics': converted_metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting frontend metrics: {str(e)}")
        # Return default values on error
        return jsonify({
            'status': 'error',
            'metrics': {
                'temperature': 22,
                'aqi': 42,
                'humidity': 65,
                'windSpeed': 12
            }
        }), 500

# Main parameter extraction endpoint
@app.route('/api/extract-parameters', methods=['POST'])
def extract_parameters():
    logger.info("=== New Request Received ===")
    
    if not request.is_json:
        logger.error("Error: Request is not JSON")
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
        logger.info(f"Request data: {data}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({
            'status_code': 400,
            'display_text': "Invalid JSON format. Please check your request format.",
            'metadata': {
                'status': 'error',
                'error': 'Invalid JSON'
            }
        }), 400
    
    if 'prompt' not in data:
        logger.error("Error: Missing prompt field")
        return jsonify({
            'status_code': 400,
            'display_text': "I didn't receive any question. What would you like to know about the air quality?",
            'metadata': {
                'status': 'error',
                'error': 'Missing prompt in request'
            }
        }), 400
    
    if not isinstance(data['prompt'], str) or not data['prompt'].strip():
        logger.error("Error: Invalid prompt format")
        return jsonify({
            'status_code': 400,
            'display_text': "I didn't receive a valid question. Could you please rephrase your query?",
            'metadata': {
                'status': 'error',
                'error': 'Invalid prompt format'
            }
        }), 400

    try:
        logger.info("Processing request...")
        # Extract parameters using Input Agent
        extracted_params = input_agent.extract_parameters(data['prompt'])
        
        # Add original prompt to parameters
        extracted_params['original_prompt'] = data['prompt']
        
        # Get model predictions using actual ML model
        logger.info("Getting model predictions...")
        
        # Extract location and datetime from parameters
        location_name = extracted_params.get('location', 'New York')  # Default location
        datetime_str = extracted_params.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # Default time
        
        logger.info(f"Location: {location_name}, DateTime: {datetime_str}")
        
        # Convert location name to coordinates using geocoding
        coords = geocoding_service.geocode(location_name)
        
        if coords:
            lat, lon = coords['lat'], coords['lon']
            location_name = coords['display_name']
            logger.info(f"Coordinates found: {lat}, {lon}")
            
            # Get model predictions
            predictions = predictor.predict_comprehensive(lat, lon, datetime_str)
            # Convert numpy types to native Python types and round to 2 decimal places
            predictions = {k: round(float(v), 2) if hasattr(v, 'item') else v for k, v in predictions.items()}
            logger.info(f"Model predictions generated successfully for coordinates: {lat}, {lon}")
            
        else:
            logger.warning(f"Could not geocode location: {location_name}, using default coordinates")
            # Fallback to default coordinates (New York)
            default_lat, default_lon = 40.7128, -74.0060
            predictions = predictor.predict_comprehensive(default_lat, default_lon, datetime_str)
            location_name = "New York"  # Default location name for fallback
            # Convert numpy types to native Python types and round to 2 decimal places
            predictions = {k: round(float(v), 2) if hasattr(v, 'item') else v for k, v in predictions.items()}
        
        # Generate response using Output Agent
        result = output_agent.analyze_predictions(predictions, extracted_params, lat, lon, location_name)
        
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

# Integrated Alert Subscription (uses Input Agent context)
@app.route('/api/subscribe-alert', methods=['POST'])
def subscribe_alert_from_query():
    """Subscribe to alerts based on user query context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['prompt', 'contact_info', 'notification_method']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status_code': 400,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters using Input Agent
        extracted_params = input_agent.extract_parameters(data['prompt'])
        
        if not extracted_params.get('location'):
            return jsonify({
                'status_code': 400,
                'message': 'Could not determine location from your query. Please specify a location.'
            }), 400
        
        # Subscribe to alerts based on context
        alert_id = alert_system.subscribe_user_alert_from_context(
            contact_info=data['contact_info'],
            location=extracted_params['location'],
            input_context=extracted_params,
            notification_method=data['notification_method']
        )
        
        return jsonify({
            'status_code': 200,
            'message': 'Successfully subscribed to air quality alerts!',
            'alert_id': alert_id,
            'metadata': {
                'location': extracted_params['location'],
                'context_type': extracted_params.get('context_type', 'general'),
                'special_concerns': extracted_params.get('special_concerns', []),
                'contact_info': data['contact_info'],
                'notification_method': data['notification_method']
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error subscribing to alerts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while subscribing to alerts'
        }), 500

# Alert Management Endpoints
@app.route('/api/alerts/subscribe', methods=['POST'])
def subscribe_alert():
    """Subscribe user to air quality alerts for a specific location"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'location', 'alert_type', 'notification_methods']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status_code': 400,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate alert type
        try:
            alert_type = AlertType(data['alert_type'])
        except ValueError:
            return jsonify({
                'status_code': 400,
                'message': f'Invalid alert_type. Must be one of: {[t.value for t in AlertType]}'
            }), 400
        
        # Subscribe to alerts
        alert_id = alert_system.subscribe_user_alert(
            user_id=data['user_id'],
            location=data['location'],
            alert_type=alert_type,
            notification_methods=data['notification_methods'],
            custom_thresholds=data.get('custom_thresholds')
        )
        
        return jsonify({
            'status_code': 200,
            'message': 'Successfully subscribed to alerts',
            'alert_id': alert_id,
            'metadata': {
                'user_id': data['user_id'],
                'location': data['location'],
                'alert_type': alert_type.value,
                'notification_methods': data['notification_methods']
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error subscribing to alerts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while subscribing to alerts'
        }), 500

@app.route('/api/alerts/unsubscribe/<alert_id>', methods=['DELETE'])
def unsubscribe_alert(alert_id):
    """Unsubscribe user from alerts"""
    try:
        success = alert_system.unsubscribe_user_alert(alert_id)
        
        if success:
            return jsonify({
                'status_code': 200,
                'message': 'Successfully unsubscribed from alerts'
            }), 200
        else:
            return jsonify({
                'status_code': 404,
                'message': 'Alert subscription not found'
            }), 404
            
    except Exception as e:
        app.logger.error(f"Error unsubscribing from alerts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while unsubscribing from alerts'
        }), 500

@app.route('/api/alerts/user/<contact_info>', methods=['GET'])
def get_user_alerts(contact_info):
    """Get all alert subscriptions for a contact (email/mobile)"""
    try:
        alerts = alert_system.get_user_alerts(contact_info)
        
        return jsonify({
            'status_code': 200,
            'alerts': alerts,
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting user alerts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting user alerts'
        }), 500

@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history with optional filters"""
    try:
        contact_info = request.args.get('contact_info')
        location = request.args.get('location')
        hours = int(request.args.get('hours', 24))
        
        alerts = alert_system.get_alert_history(contact_info, location, hours)
        
        return jsonify({
            'status_code': 200,
            'alerts': alerts,
            'count': len(alerts),
            'filters': {
                'contact_info': contact_info,
                'location': location,
                'hours': hours
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting alert history: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting alert history'
        }), 500

@app.route('/api/alerts/check', methods=['POST'])
def check_alerts():
    """Check for alerts based on current air quality data"""
    try:
        data = request.get_json()
        
        if 'location' not in data or 'air_quality_data' not in data:
            return jsonify({
                'status_code': 400,
                'message': 'Missing required fields: location, air_quality_data'
            }), 400
        
        # Check for triggered alerts
        triggered_alerts = alert_system.check_alerts(
            data['location'], 
            data['air_quality_data']
        )
        
        # Convert to JSON-serializable format
        alerts_data = []
        for alert in triggered_alerts:
            alerts_data.append({
                'alert_id': alert.alert_id,
                'user_id': alert.user_id,
                'location': alert.location,
                'parameter': alert.parameter,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'is_resolved': alert.is_resolved
            })
        
        return jsonify({
            'status_code': 200,
            'triggered_alerts': alerts_data,
            'count': len(alerts_data),
            'location': data['location']
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error checking alerts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while checking alerts'
        }), 500

@app.route('/api/alerts/templates', methods=['GET'])
def get_alert_templates():
    """Get available alert templates for frontend"""
    try:
        templates = AlertTemplates.get_templates()
        
        return jsonify({
            'status_code': 200,
            'templates': templates,
            'count': len(templates)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting alert templates: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting alert templates'
        }), 500

@app.route('/api/alerts/ui-components', methods=['GET'])
def get_alert_ui_components():
    """Get UI component configurations for alert system"""
    try:
        components = {
            'alert_button': AlertUIComponents.get_alert_button_config(),
            'alert_card': AlertUIComponents.get_alert_card_config(),
            'alert_history': AlertUIComponents.get_alert_history_config()
        }
        
        return jsonify({
            'status_code': 200,
            'components': components
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting UI components: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting UI components'
        }), 500

@app.route('/api/alerts/subscribe-from-template', methods=['POST'])
def subscribe_from_template():
    """Subscribe to alerts using a predefined template"""
    try:
        data = request.get_json()
        
        required_fields = ['template_id', 'user_id', 'location', 'notification_methods']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status_code': 400,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create subscription from template
        subscription_data = AlertTemplates.create_subscription_from_template(
            template_id=data['template_id'],
            user_id=data['user_id'],
            location=data['location'],
            notification_methods=data['notification_methods']
        )
        
        # Subscribe to alerts
        alert_id = alert_system.subscribe_user_alert(
            user_id=subscription_data['user_id'],
            location=subscription_data['location'],
            alert_type=AlertType(subscription_data['alert_type']),
            notification_methods=subscription_data['notification_methods'],
            custom_thresholds=subscription_data['custom_thresholds']
        )
        
        return jsonify({
            'status_code': 200,
            'message': 'Successfully subscribed to alerts using template',
            'alert_id': alert_id,
            'template_name': subscription_data['template_name'],
            'metadata': subscription_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'status_code': 400,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error subscribing from template: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while subscribing from template'
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
