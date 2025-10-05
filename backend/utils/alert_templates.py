"""
Alert Templates for AuraCast Frontend
Provides predefined alert configurations for different user scenarios
"""

from typing import Dict, List, Any
from utils.alert_system import AlertType, AlertThreshold

class AlertTemplates:
    """Predefined alert templates for different user scenarios"""
    
    @staticmethod
    def get_templates() -> Dict[str, Dict[str, Any]]:
        """Get all available alert templates"""
        return {
            "health_sensitive": {
                "name": "Health Sensitive Individual",
                "description": "For people with asthma, respiratory conditions, or heart disease",
                "alert_type": "health",
                "thresholds": [
                    {"parameter": "pm25", "warning": 15.0, "critical": 25.0, "unit": "µg/m³", "description": "PM2.5 fine particles"},
                    {"parameter": "o3", "warning": 70, "critical": 100, "unit": "ppb", "description": "Ground-level ozone"},
                    {"parameter": "aqi", "warning": 50, "critical": 100, "unit": "index", "description": "Air Quality Index"}
                ],
                "recommended_actions": [
                    "Stay indoors when alerts trigger",
                    "Use air purifiers",
                    "Avoid outdoor exercise",
                    "Keep windows closed"
                ],
                "icon": "🏥",
                "color": "red"
            },
            
            "outdoor_enthusiast": {
                "name": "Outdoor Enthusiast",
                "description": "For runners, cyclists, and outdoor sports enthusiasts",
                "alert_type": "outdoor_activity",
                "thresholds": [
                    {"parameter": "pm25", "warning": 20.0, "critical": 35.0, "unit": "µg/m³", "description": "PM2.5 fine particles"},
                    {"parameter": "o3", "warning": 80, "critical": 120, "unit": "ppb", "description": "Ground-level ozone"},
                    {"parameter": "aqi", "warning": 80, "critical": 100, "unit": "index", "description": "Air Quality Index"}
                ],
                "recommended_actions": [
                    "Check air quality before outdoor activities",
                    "Consider indoor alternatives when alerts trigger",
                    "Wear appropriate masks if necessary",
                    "Plan activities for better air quality times"
                ],
                "icon": "🏃‍♂️",
                "color": "orange"
            },
            
            "industrial_worker": {
                "name": "Industrial Worker",
                "description": "For workers in industrial areas or near factories",
                "alert_type": "industrial",
                "thresholds": [
                    {"parameter": "pm25", "warning": 35.0, "critical": 55.0, "unit": "µg/m³", "description": "PM2.5 fine particles"},
                    {"parameter": "no2", "warning": 3e15, "critical": 5e15, "unit": "molecules/cm²", "description": "Nitrogen dioxide"},
                    {"parameter": "co", "warning": 2e18, "critical": 3e18, "unit": "molecules/cm²", "description": "Carbon monoxide"},
                    {"parameter": "aqi", "warning": 100, "critical": 150, "unit": "index", "description": "Air Quality Index"}
                ],
                "recommended_actions": [
                    "Use proper ventilation systems",
                    "Wear appropriate protective equipment",
                    "Monitor workplace air quality regularly",
                    "Report high levels to safety officers"
                ],
                "icon": "🏭",
                "color": "blue"
            },
            
            "parent_guardian": {
                "name": "Parent/Guardian",
                "description": "For parents concerned about children's health and outdoor activities",
                "alert_type": "health",
                "thresholds": [
                    {"parameter": "pm25", "warning": 20.0, "critical": 35.0, "unit": "µg/m³", "description": "PM2.5 fine particles"},
                    {"parameter": "o3", "warning": 80, "critical": 120, "unit": "ppb", "description": "Ground-level ozone"},
                    {"parameter": "aqi", "warning": 80, "critical": 100, "unit": "index", "description": "Air Quality Index"}
                ],
                "recommended_actions": [
                    "Limit children's outdoor play during alerts",
                    "Choose indoor activities when air quality is poor",
                    "Check air quality before school outdoor activities",
                    "Educate children about air quality awareness"
                ],
                "icon": "👨‍👩‍👧‍👦",
                "color": "green"
            },
            
            "general_public": {
                "name": "General Public",
                "description": "For general air quality awareness and daily activities",
                "alert_type": "general",
                "thresholds": [
                    {"parameter": "aqi", "warning": 100, "critical": 150, "unit": "index", "description": "Air Quality Index"},
                    {"parameter": "pm25", "warning": 25.0, "critical": 50.0, "unit": "µg/m³", "description": "PM2.5 fine particles"}
                ],
                "recommended_actions": [
                    "Stay informed about local air quality",
                    "Reduce outdoor activities during poor air quality",
                    "Use public transportation when possible",
                    "Support clean air initiatives"
                ],
                "icon": "🌍",
                "color": "purple"
            }
        }
    
    @staticmethod
    def get_template_by_id(template_id: str) -> Dict[str, Any]:
        """Get a specific template by ID"""
        templates = AlertTemplates.get_templates()
        return templates.get(template_id, {})
    
    @staticmethod
    def get_templates_by_alert_type(alert_type: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific alert type"""
        templates = AlertTemplates.get_templates()
        return [
            template for template in templates.values()
            if template.get('alert_type') == alert_type
        ]
    
    @staticmethod
    def create_subscription_from_template(template_id: str, user_id: str, location: str, 
                                        notification_methods: List[str]) -> Dict[str, Any]:
        """Create a subscription request from a template"""
        template = AlertTemplates.get_template_by_id(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Convert template thresholds to AlertThreshold objects
        thresholds = []
        for threshold in template.get('thresholds', []):
            thresholds.append(AlertThreshold(
                parameter=threshold['parameter'],
                warning_level=threshold['warning'],
                critical_level=threshold['critical'],
                unit=threshold['unit'],
                description=threshold['description']
            ))
        
        return {
            'user_id': user_id,
            'location': location,
            'alert_type': template['alert_type'],
            'notification_methods': notification_methods,
            'custom_thresholds': thresholds,
            'template_id': template_id,
            'template_name': template['name']
        }

# Alert UI Components for Frontend
class AlertUIComponents:
    """UI component templates for alert system"""
    
    @staticmethod
    def get_alert_button_config() -> Dict[str, Any]:
        """Get configuration for alert button component"""
        return {
            "button_text": "Set Air Quality Alert",
            "button_icon": "🔔",
            "button_color": "primary",
            "modal_title": "Configure Air Quality Alerts",
            "modal_description": "Get notified when air quality changes in your area",
            "templates": AlertTemplates.get_templates()
        }
    
    @staticmethod
    def get_alert_card_config() -> Dict[str, Any]:
        """Get configuration for alert card component"""
        return {
            "card_title": "Active Alerts",
            "card_icon": "🚨",
            "empty_state": {
                "title": "No Active Alerts",
                "description": "You'll be notified when air quality changes",
                "action_text": "Set up alerts"
            },
            "alert_states": {
                "active": {"color": "red", "icon": "🔴"},
                "warning": {"color": "orange", "icon": "🟡"},
                "resolved": {"color": "green", "icon": "🟢"}
            }
        }
    
    @staticmethod
    def get_alert_history_config() -> Dict[str, Any]:
        """Get configuration for alert history component"""
        return {
            "title": "Alert History",
            "filters": {
                "time_ranges": ["1 hour", "6 hours", "24 hours", "7 days"],
                "severity_levels": ["low", "medium", "high", "critical"],
                "parameters": ["pm25", "o3", "no2", "co", "aqi"]
            },
            "columns": [
                {"key": "timestamp", "label": "Time", "type": "datetime"},
                {"key": "location", "label": "Location", "type": "text"},
                {"key": "parameter", "label": "Parameter", "type": "text"},
                {"key": "severity", "label": "Severity", "type": "badge"},
                {"key": "message", "label": "Message", "type": "text"}
            ]
        }
