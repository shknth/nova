"""Visualization configurations and mappings"""

VISUALIZATION_MAPPINGS = {
    # Gemini suggestion patterns to our fixed types
    "concentration map": "pollutant_map",
    "spatial_distribution": "pollutant_map",
    "map": "pollutant_map",
    "time_series": "time_series",
    "time series": "time_series",
    "trend": "time_series",
    "wind_rose": "wind_rose",
    "wind rose": "wind_rose",
    "distribution": "box_plot",
    "comparison": "bar_chart",
    "levels": "line_chart",
    "forecast": "forecast_chart",
    # Add specific pollutant patterns
    "no2": "pollutant_map",
    "aod": "pollutant_map"
}

SUPPORTED_VISUALIZATIONS = {
    "pollutant_map": {
        "type": "map",
        "title": "Pollutant Concentration Map",
        "description": "Geographical distribution of pollutant concentrations",
        "requires_realtime": True,
        "data_fields": ["lat", "lon", "value"],
        "config": {
            "colorscale": "Viridis",
            "zoom": 10
        }
    },
    "time_series": {
        "type": "line",
        "title": "Time Series Analysis",
        "description": "Historical and predicted pollutant levels over time",
        "requires_realtime": True,
        "data_fields": ["timestamp", "value"],
        "config": {
            "x_label": "Time",
            "y_label": "Concentration"
        }
    },
    "wind_rose": {
        "type": "polar",
        "title": "Wind Rose Diagram",
        "description": "Wind speed and direction distribution",
        "requires_realtime": False,
        "data_fields": ["direction", "speed"],
        "config": {
            "max_radius": 100
        }
    },
    "box_plot": {
        "type": "box",
        "title": "Pollutant Distribution",
        "description": "Statistical distribution of pollutant levels",
        "requires_realtime": True,
        "data_fields": ["parameter", "values"],
        "config": {
            "showOutliers": True
        }
    },
    "bar_chart": {
        "type": "bar",
        "title": "Pollutant Comparison",
        "description": "Comparison of different pollutant levels",
        "requires_realtime": True,
        "data_fields": ["parameter", "value"],
        "config": {
            "orientation": "vertical"
        }
    },
    "forecast_chart": {
        "type": "line",
        "title": "Forecast Analysis",
        "description": "Predicted pollutant levels with uncertainty",
        "requires_realtime": False,
        "data_fields": ["timestamp", "value", "uncertainty"],
        "config": {
            "show_uncertainty": True
        }
    }
}

def get_visualization_type(gemini_suggestion: str) -> str:
    """Map Gemini's suggestion to our supported visualization type"""
    
    suggestion_lower = gemini_suggestion.lower()
    for pattern, viz_type in VISUALIZATION_MAPPINGS.items():
        if pattern in suggestion_lower:
            return viz_type
    return "time_series"  # default fallback