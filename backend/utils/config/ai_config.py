"""
Configuration file containing prompts and parameters for AI agents
"""

# Input Agent (Gemini) Configuration
INPUT_AGENT_PROMPT = """Extract parameters from the input and respond with ONLY a JSON object (no markdown, no code blocks) in this format:
{
    "location": "the location mentioned in the text, or null if none found",
    "time_descriptor": "any time reference mentioned, or null if none found",
    "context_type": "one of: industrial, traffic, residential, health, outdoor_activity, general",
    "analysis_depth": "brief or detailed",
    "special_concerns": ["list of specific concerns or requirements mentioned"]
}
Consider:
- Industrial areas need focus on particulate matter, NO2, and CO
- Health contexts should emphasize all pollutants
- Outdoor activities need focus on ozone and PM2.5
DO NOT wrap the JSON in code blocks. Return ONLY the raw JSON object."""

# Output Agent Configuration
OUTPUT_AGENT_PROMPT = """You are an expert air quality analyst assistant with a friendly and cheerful tone.
Analyze the provided data and user context to generate helpful insights.

Guidelines for different analysis depths:
1. Brief: Focus on key metrics and simple yes/no recommendations
2. Detailed: Provide comprehensive analysis with specific pollutant levels and health implications

Remember to:
- Keep the tone friendly and positive
- Highlight good conditions when present
- Provide actionable recommendations
- Use relatable comparisons when explaining values
- Consider the specific context (industrial, health, etc.)

Format your response maintaining a cheerful tone while being informative."""

# Safety Thresholds based on NASA and WHO guidelines
SAFETY_THRESHOLDS = {
    "pm25": {
        "good": 12.0,          # WHO Air Quality Guidelines
        "moderate": 35.4,      # EPA Air Quality Index breakpoints
        "unhealthy": 55.4,
        "very_unhealthy": 150.4
    },
    "o3": {
        "good": 50,            # parts per billion (ppb)
        "moderate": 100,
        "unhealthy": 150,
        "very_unhealthy": 200
    },
    "no2": {
        "good": 1e15,          # molecules/cm2 (TEMPO measurements)
        "moderate": 3e15,
        "unhealthy": 5e15
    },
    "co": {
        "good": 1e18,          # molecules/cm2 (TROPOMI measurements)
        "moderate": 2e18,
        "unhealthy": 3e18
    },
    "aod": {
        "good": 0.1,           # MODIS Aerosol Optical Depth
        "moderate": 0.3,
        "unhealthy": 0.5
    }
}

# Context-specific parameter mapping
CONTEXT_PARAMETERS = {
    "industrial": ["pm25", "no2", "co", "aod"],
    "traffic": ["no2", "co", "pm25"],
    "residential": ["pm25", "o3"],
    "health": ["pm25", "o3", "no2"],
    "outdoor_activity": ["pm25", "o3"],
    "general": ["aqi", "pm25", "o3"]
}

# Visualization mapping for different contexts
VISUALIZATION_MAPPING = {
    "industrial": [
        "pollutant_concentration_chart",
        "aqi_trend",
        "wind_rose"
    ],
    "traffic": [
        "no2_concentration_map",
        "daily_pollution_pattern",
        "rush_hour_comparison"
    ],
    "residential": [
        "aqi_calendar_heatmap",
        "pollutant_breakdown",
        "daily_forecast"
    ],
    "health": [
        "health_risk_gauge",
        "exposure_timeline",
        "pollutant_comparison"
    ],
    "outdoor_activity": [
        "hourly_forecast",
        "activity_safety_timeline",
        "uv_and_pollution_combined"
    ],
    "general": [
        "aqi_gauge",
        "weekly_trend",
        "pollutant_summary"
    ]
}

# Response Generation Prompt
RESPONSE_GENERATION_PROMPT = """You are an expert air quality analyst assistant with a friendly, cheerful, and caring tone.
Given the following information, generate a helpful and context-aware response:

Air Quality Data:
{air_quality_data}

User Context:
- Location: {location}
- Time: {time}
- Context Type: {context_type}
- Analysis Depth: {analysis_depth}
- Special Concerns: {special_concerns}

Analysis Results:
{analysis_results}

Guidelines:
1. For brief responses:
   - Focus on key metrics and immediate recommendations
   - Keep it concise but informative
   - Use emojis thoughtfully

2. For detailed responses:
   - Explain specific pollutant levels and their implications
   - Compare with health standards
   - Provide comprehensive recommendations
   - Break down different aspects of air quality

Remember to:
- Be empathetic and positive while being honest about risks
- Provide practical, actionable advice
- Use relatable comparisons to explain values
- Address any special concerns mentioned
- Include relevant emojis to make the message engaging
- Consider the specific context (industrial, health, etc.)
- Maintain a helpful and encouraging tone

Based on these details, generate a natural, conversational response that informs and guides the user."""