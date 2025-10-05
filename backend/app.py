from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from utils import InputAgent, OutputAgent
from utils.alert_system import alert_system, AlertType, AlertSeverity
from utils.alert_templates import AlertTemplates, AlertUIComponents
from utils.realtime_data_source import realtime_data_source
from utils.dashboard_config import dashboard_config
from model_design import AirQualityPredictor
from utils.geocoding import GeocodingService


# Load environment variables
load_dotenv()

# Initialize Flask app and components
app = Flask(__name__)
CORS(app)
input_agent = InputAgent()
output_agent = OutputAgent()

# Ensure data is available from GCS
print("📥 Ensuring data availability from GCS...")
data_available = ensure_data_downloaded()
if not data_available:
    print("⚠️  Warning: Could not download data from GCS, will attempt to use local data")

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
        default_location = request.args.get('location', 'New York')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        app.logger.info(f"Getting frontend metrics for {default_location}")
        
        # Get coordinates for default location
        coords = geocoding_service.geocode(default_location)
        
        if coords:
            lat, lon = coords['lat'], coords['lon']
        else:
            # Fallback to New York coordinates
            lat, lon = 40.7128, -74.0060
        
        # Get comprehensive predictions
        predictions = predictor.predict_comprehensive(lat, lon, current_time)
        
        # Return just the frontend metrics
        return jsonify({
            'status': 'success',
            'location': default_location,
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': current_time,
            'metrics': predictions['frontend_metrics']
        })
        
    except Exception as e:
        app.logger.error(f"Error getting frontend metrics: {str(e)}")
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
        
        # Get model predictions using actual ML model
        app.logger.info("Getting model predictions...")
        
        # Extract location and datetime from parameters
        location_name = extracted_params.get('location', 'New York')  # Default location
        datetime_str = extracted_params.get('datetime', '2025-09-01 14:00:00')  # Default time
        
        app.logger.info(f"Location: {location_name}, DateTime: {datetime_str}")
        
        # Convert location name to coordinates using geocoding
        coords = geocoding_service.geocode(location_name)
        
        if coords:
            lat, lon = coords['lat'], coords['lon']
            app.logger.info(f"Coordinates found: {lat}, {lon}")
            
            # Get model predictions
            predictions = predictor.predict_comprehensive(lat, lon, datetime_str)
            app.logger.info("Model predictions generated successfully")
            
        else:
            app.logger.warning(f"Could not geocode location: {location_name}, using default coordinates")
            # Fallback to default coordinates (New York)
            predictions = predictor.predict_comprehensive(40.7128, -74.0060, datetime_str)
        
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
        
        # Add location to monitoring
        realtime_data_source.add_monitoring_location(extracted_params['location'])
        
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
        app.logger.error(f"Error subscribing from template: {str(e)}")
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

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start real-time monitoring for alerts"""
    try:
        # Start monitoring
        realtime_data_source.start_monitoring(alert_system)
        
        return jsonify({
            'status_code': 200,
            'message': 'Real-time monitoring started successfully',
            'monitoring_locations': list(realtime_data_source.monitoring_locations)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while starting monitoring'
        }), 500

@app.route('/api/dashboard/<location>', methods=['GET'])
def get_dashboard_data(location):
    """Get dashboard data for a specific location"""
    try:
        dashboard_data = realtime_data_source.get_dashboard_data(location)
        
        if not dashboard_data:
            return jsonify({
                'status_code': 404,
                'message': f'No data available for location: {location}'
            }), 404
        
        return jsonify({
            'status_code': 200,
            'dashboard_data': dashboard_data
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting dashboard data'
        }), 500

@app.route('/api/dashboard/raw/<location>', methods=['GET'])
def get_raw_dashboard_data(location):
    """Get raw real-time data for a specific location"""
    try:
        raw_data = realtime_data_source.get_realtime_data(location)
        
        if not raw_data:
            return jsonify({
                'status_code': 404,
                'message': f'No data available for location: {location}'
            }), 404
        
        return jsonify({
            'status_code': 200,
            'raw_data': raw_data
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting raw data: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting raw data'
        }), 500

@app.route('/api/dashboard/status', methods=['GET'])
def get_dashboard_status():
    """Get overall dashboard system status"""
    try:
        # Get monitoring status
        monitoring_locations = list(realtime_data_source.monitoring_locations)
        
        # Get alert system status
        total_alerts = len(alert_system.user_alerts)
        recent_alerts = len(alert_system.get_alert_history(hours=24))
        
        # Get data source status
        data_sources = {
            'openaq': 'available',
            'simulated': 'active',
            'satellite': 'available'
        }
        
        return jsonify({
            'status_code': 200,
            'dashboard_status': {
                'system_status': 'operational',
                'monitoring_locations': monitoring_locations,
                'total_alert_subscriptions': total_alerts,
                'recent_alerts_24h': recent_alerts,
                'data_sources': data_sources,
                'last_updated': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard status: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting dashboard status'
        }), 500

@app.route('/api/dashboard/locations', methods=['GET'])
def get_available_locations():
    """Get list of available locations for dashboard"""
    try:
        # Get all monitored locations
        monitored_locations = list(realtime_data_source.monitoring_locations)
        
        # Get available locations from monitoring system
        # In production, this would query a database of supported locations
        # For now, we'll use the currently monitored locations plus some demo locations
        available_locations = list(realtime_data_source.monitoring_locations)
        
        # Add some demo locations if none are monitored yet
        if not available_locations:
            available_locations = [
                'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
                'London, UK', 'Paris, France', 'Berlin, Germany', 'Tokyo, Japan',
                'Sydney, Australia', 'Toronto, Canada'
            ]
        
        # Check which locations have data
        locations_with_data = []
        for location in available_locations:
            data = realtime_data_source.get_realtime_data(location)
            if data:
                locations_with_data.append({
                    'name': location,
                    'has_data': True,
                    'last_updated': data.get('timestamp'),
                    'aqi': data.get('air_quality', {}).get('aqi', 'N/A'),
                    'is_monitored': location.lower() in [loc.lower() for loc in monitored_locations]
                })
            else:
                locations_with_data.append({
                    'name': location,
                    'has_data': False,
                    'last_updated': None,
                    'aqi': 'N/A',
                    'is_monitored': False
                })
        
        return jsonify({
            'status_code': 200,
            'locations': locations_with_data,
            'total_locations': len(locations_with_data),
            'monitored_locations': len(monitored_locations)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting available locations: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting locations'
        }), 500

@app.route('/api/dashboard/compare', methods=['POST'])
def compare_locations():
    """Compare air quality between multiple locations"""
    try:
        data = request.get_json()
        
        if 'locations' not in data:
            return jsonify({
                'status_code': 400,
                'message': 'Missing required field: locations'
            }), 400
        
        locations = data['locations']
        if not isinstance(locations, list) or len(locations) < 2:
            return jsonify({
                'status_code': 400,
                'message': 'At least 2 locations required for comparison'
            }), 400
        
        comparison_data = []
        
        for location in locations:
            dashboard_data = realtime_data_source.get_dashboard_data(location)
            if dashboard_data:
                aq = dashboard_data.get('components', {}).get('aqi_gauge', {})
                comparison_data.append({
                    'location': location,
                    'aqi': aq.get('value', 0),
                    'status': aq.get('status', 'Unknown'),
                    'color': aq.get('color', '#000000'),
                    'timestamp': dashboard_data.get('timestamp')
                })
        
        if not comparison_data:
            return jsonify({
                'status_code': 404,
                'message': 'No data available for any of the specified locations'
            }), 404
        
        # Sort by AQI (worst first)
        comparison_data.sort(key=lambda x: x['aqi'], reverse=True)
        
        return jsonify({
            'status_code': 200,
            'comparison': {
                'locations': comparison_data,
                'best_location': comparison_data[-1]['location'] if comparison_data else None,
                'worst_location': comparison_data[0]['location'] if comparison_data else None,
                'average_aqi': sum(loc['aqi'] for loc in comparison_data) / len(comparison_data)
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error comparing locations: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while comparing locations'
        }), 500

@app.route('/api/dashboard/export/<location>', methods=['GET'])
def export_dashboard_data(location):
    """Export dashboard data in various formats"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            dashboard_data = realtime_data_source.get_dashboard_data(location)
            if not dashboard_data:
                return jsonify({
                    'status_code': 404,
                    'message': f'No data available for location: {location}'
                }), 404
            
            return jsonify({
                'status_code': 200,
                'export_data': dashboard_data,
                'format': 'json',
                'exported_at': datetime.now().isoformat()
            }), 200
        
        elif format_type == 'csv':
            # Generate CSV format for data analysis
            raw_data = realtime_data_source.get_realtime_data(location)
            if not raw_data:
                return jsonify({
                    'status_code': 404,
                    'message': f'No data available for location: {location}'
                }), 404
            
            # Create CSV-like structure
            csv_data = {
                'location': location,
                'timestamp': raw_data['timestamp'],
                'pm25': raw_data['air_quality']['pm25'],
                'pm10': raw_data['air_quality']['pm10'],
                'o3': raw_data['air_quality']['o3'],
                'no2': raw_data['air_quality']['no2'],
                'so2': raw_data['air_quality']['so2'],
                'aqi': raw_data['air_quality']['aqi'],
                'temperature': raw_data['weather_data']['temperature_celsius'],
                'humidity': raw_data['weather_data']['humidity'],
                'wind_speed': raw_data['weather_data']['wind_speed']
            }
            
            return jsonify({
                'status_code': 200,
                'export_data': csv_data,
                'format': 'csv',
                'exported_at': datetime.now().isoformat()
            }), 200
        
        else:
            return jsonify({
                'status_code': 400,
                'message': f'Unsupported format: {format_type}. Supported formats: json, csv'
            }), 400
        
    except Exception as e:
        app.logger.error(f"Error exporting dashboard data: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while exporting data'
        }), 500

# Dashboard Configuration Endpoints
@app.route('/api/dashboard/config', methods=['GET'])
def get_dashboard_config():
    """Get dashboard configuration metadata"""
    try:
        metadata = dashboard_config.get_dashboard_metadata()
        
        return jsonify({
            'status_code': 200,
            'config': metadata
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard config: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting dashboard config'
        }), 500

@app.route('/api/dashboard/components', methods=['GET'])
def get_dashboard_components():
    """Get list of available dashboard components"""
    try:
        components = dashboard_config.get_component_list()
        
        return jsonify({
            'status_code': 200,
            'components': components,
            'count': len(components)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard components: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting components'
        }), 500

@app.route('/api/dashboard/layouts', methods=['GET'])
def get_dashboard_layouts():
    """Get available dashboard layouts"""
    try:
        layouts = {}
        for layout_name in dashboard_config.layouts.keys():
            layouts[layout_name] = dashboard_config.get_layout_config(layout_name)
        
        return jsonify({
            'status_code': 200,
            'layouts': layouts,
            'count': len(layouts)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard layouts: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting layouts'
        }), 500

@app.route('/api/dashboard/color-schemes', methods=['GET'])
def get_color_schemes():
    """Get available color schemes"""
    try:
        color_schemes = {}
        for scheme_name in dashboard_config.color_schemes.keys():
            color_schemes[scheme_name] = dashboard_config.get_color_scheme(scheme_name)
        
        return jsonify({
            'status_code': 200,
            'color_schemes': color_schemes,
            'count': len(color_schemes)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting color schemes: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting color schemes'
        }), 500

@app.route('/api/dashboard/component/<component_id>', methods=['GET'])
def get_component_config(component_id):
    """Get configuration for a specific component"""
    try:
        component = dashboard_config.get_component_config(component_id)
        
        if not component:
            return jsonify({
                'status_code': 404,
                'message': f'Component not found: {component_id}'
            }), 404
        
        return jsonify({
            'status_code': 200,
            'component': {
                'id': component.component_id,
                'type': component.component_type,
                'title': component.title,
                'description': component.description,
                'position': component.position,
                'refresh_interval': component.refresh_interval,
                'data_source': component.data_source,
                'visualization_config': component.visualization_config
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting component config: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while getting component config'
        }), 500

@app.route('/api/dashboard/custom', methods=['POST'])
def create_custom_dashboard():
    """Create a custom dashboard layout"""
    try:
        data = request.get_json()
        
        if 'layout_name' not in data or 'components' not in data:
            return jsonify({
                'status_code': 400,
                'message': 'Missing required fields: layout_name, components'
            }), 400
        
        layout_name = data['layout_name']
        components = data['components']
        
        # Validate components exist
        available_components = list(dashboard_config.components.keys())
        invalid_components = [comp for comp in components if comp not in available_components]
        
        if invalid_components:
            return jsonify({
                'status_code': 400,
                'message': f'Invalid components: {invalid_components}'
            }), 400
        
        # Create custom layout
        custom_layout = {
            'name': layout_name,
            'description': f'Custom layout: {layout_name}',
            'grid_size': data.get('grid_size', {'columns': 12, 'rows': 15}),
            'components': components,
            'is_custom': True
        }
        
        return jsonify({
            'status_code': 200,
            'message': f'Custom dashboard layout "{layout_name}" created successfully',
            'layout': custom_layout
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error creating custom dashboard: {str(e)}")
        return jsonify({
            'status_code': 500,
            'message': 'Internal server error while creating custom dashboard'
        }), 500

if __name__ == "__main__":
    # Start real-time monitoring
    realtime_data_source.start_monitoring(alert_system)
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)