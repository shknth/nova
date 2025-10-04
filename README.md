# StratoSense: Air Quality Prediction & Monitoring

StratoSense is a web application developed for the NASA Space Apps Challenge 2025, addressing the "From Earthdata to Action: Cloud Computing with Earth Observation Data for Predicting Cleaner, Safer Skies" challenge.

## Project Overview

StratoSense leverages NASA Earth observation data to predict and visualize air quality trends, helping users make informed decisions about outdoor activities and health precautions. The application combines satellite data with machine learning to provide accurate air quality forecasts and visualizations.

### Key Features

- **Interactive Dashboard**: Real-time air quality metrics and forecasts
- **Geospatial Visualization**: Map-based view of air quality across different regions
- **Predictive Analytics**: Machine learning models to forecast air quality trends
- **Health Recommendations**: Personalized advice based on air quality conditions

## Tech Stack

### Frontend
- React.js
- Chart.js for data visualization
- Leaflet for interactive maps
- Axios for API communication

### Backend
- Flask (Python)
- Scikit-learn for machine learning models
- NumPy and Pandas for data processing

## Getting Started

### Prerequisites
- Node.js and npm
- Python 3.8+
- Git

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/shknth/StratoSense.git
   cd StratoSense
   ```

2. Set up the frontend:
   ```
   cd frontend
   npm install
   npm start
   ```
   The frontend will be available at http://localhost:3000

3. Set up the backend:
   ```
   cd ../backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
   The backend API will be available at http://localhost:5000

## API Endpoints

- `GET /api/health`: Health check endpoint
- `GET /api/data`: Get current air quality data and forecasts
- `POST /api/predict`: Get predictions based on input features
- `GET /api/model/info`: Get information about the ML model

## Project Structure

```
StratoSense/
├── frontend/           # React frontend application
│   ├── public/         # Static files
│   └── src/            # React components and logic
│       ├── components/ # UI components
│       └── ...
├── backend/            # Flask backend application
│   ├── app.py          # Main Flask application
│   ├── model.py        # ML model for air quality prediction
│   └── requirements.txt # Python dependencies
└── README.md           # Project documentation
```

## Future Enhancements

- Integration with real-time NASA Earth observation data
- Advanced ML models for more accurate predictions
- User accounts for personalized monitoring
- Mobile application for on-the-go access
- Alerts and notifications for dangerous air quality conditions

## Contributors

- Team CodeOrbiters - NASA Space Apps Challenge 2025

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NASA for providing Earth observation data
- The Space Apps Challenge for the opportunity to contribute to cleaner, safer skies
