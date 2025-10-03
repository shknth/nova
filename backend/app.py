from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import numpy as np
from dotenv import load_dotenv
from model import AirQualityModel, generate_sample_data

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize model
model = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is working"""
    return jsonify({
        "status": "success",
        "message": "API is operational"
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    """Endpoint for retrieving current air quality data"""
    # This will be replaced with actual data processing once we have the NASA datasets
    sample_data = {
        "current": {
            "aqi": 42,
            "category": "Good",
            "pollutants": {
                "pm25": 10.2,
                "pm10": 18.5,
                "o3": 35.1,
                "no2": 12.3
            }
        },
        "forecast": [
            { "date": "Today", "aqi": 42 },
            { "date": "Tomorrow", "aqi": 45 },
            { "date": "Day 3", "aqi": 52 },
            { "date": "Day 4", "aqi": 48 },
            { "date": "Day 5", "aqi": 38 },
            { "date": "Day 6", "aqi": 35 },
            { "date": "Day 7", "aqi": 40 }
        ]
    }
    return jsonify(sample_data)

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Endpoint for making predictions using the ML model
    
    Expected JSON input:
    {
        "features": [[feat1, feat2, ...], [feat1, feat2, ...], ...]
    }
    """
    global model
    
    # Initialize model if not already done
    if model is None:
        model = AirQualityModel()
        X_train, y_train, _ = generate_sample_data()
        model.train(X_train, y_train)
    
    try:
        # Get features from request
        data = request.get_json()
        features = np.array(data.get('features', []))
        
        if features.size == 0:
            return jsonify({
                "status": "error",
                "message": "No features provided"
            }), 400
        
        # Make predictions
        predictions = model.predict(features).tolist()
        
        return jsonify({
            "status": "success",
            "predictions": predictions
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/model/info', methods=['GET'])
def model_info():
    """Endpoint for retrieving information about the ML model"""
    global model
    
    # Initialize the model - AirQuality
    if model is None:
        model = AirQualityModel()
        X_train, y_train, _ = generate_sample_data()
        model.train(X_train, y_train)
    
    try:
        # Get feature importance
        importance = model.get_feature_importance()
        
        return jsonify({
            "status": "success",
            "model_type": "Random Forest Regressor",
            "is_trained": model.is_trained,
            "feature_importance": importance
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)