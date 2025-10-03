from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is working"""
    return jsonify({
        "status": "success",
        "message": "API is operational"
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    """Placeholder endpoint for future data retrieval"""
    # This will be replaced with actual data processing once we have the NASA datasets
    sample_data = {
        "message": "This endpoint will serve processed NASA Earth observation data",
        "data_status": "placeholder"
    }
    return jsonify(sample_data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
