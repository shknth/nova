"""
Real-time Alert System for AuraCast
Handles threshold monitoring, user notifications, and alert management
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    HEALTH = "health"
    INDUSTRIAL = "industrial"
    OUTDOOR_ACTIVITY = "outdoor_activity"
    GENERAL = "general"
    THRESHOLD_BREACH = "threshold_breach"

@dataclass
class AlertThreshold:
    """Defines alert thresholds for different parameters"""
    parameter: str
    warning_level: float
    critical_level: float
    unit: str
    description: str

@dataclass
class UserAlert:
    """User's alert subscription"""
    contact_info: str  # mobile number or email
    location: str
    alert_type: AlertType
    thresholds: List[AlertThreshold]
    notification_method: str  # email or sms
    is_active: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    context_from_query: Dict[str, Any] = None  # Store original query context

@dataclass
class AlertEvent:
    """Represents a triggered alert"""
    alert_id: str
    contact_info: str
    location: str
    parameter: str
    current_value: float
    threshold_value: float
    severity: AlertSeverity
    message: str
    timestamp: datetime
    is_resolved: bool = False

class AlertSystem:
    """Main alert system for real-time monitoring"""
    
    def __init__(self):
        self.user_alerts: Dict[str, UserAlert] = {}
        self.alert_history: List[AlertEvent] = []
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Default thresholds for different contexts
        self.default_thresholds = {
            AlertType.HEALTH: [
                AlertThreshold("pm25", 25.0, 50.0, "µg/m³", "PM2.5 fine particles"),
                AlertThreshold("o3", 100, 150, "ppb", "Ground-level ozone"),
                AlertThreshold("no2", 2e15, 4e15, "molecules/cm²", "Nitrogen dioxide"),
                AlertThreshold("aqi", 100, 150, "index", "Air Quality Index")
            ],
            AlertType.INDUSTRIAL: [
                AlertThreshold("pm25", 35.0, 55.0, "µg/m³", "PM2.5 fine particles"),
                AlertThreshold("no2", 3e15, 5e15, "molecules/cm²", "Nitrogen dioxide"),
                AlertThreshold("co", 2e18, 3e18, "molecules/cm²", "Carbon monoxide"),
                AlertThreshold("aod", 0.3, 0.5, "dimensionless", "Aerosol Optical Depth")
            ],
            AlertType.OUTDOOR_ACTIVITY: [
                AlertThreshold("pm25", 20.0, 35.0, "µg/m³", "PM2.5 fine particles"),
                AlertThreshold("o3", 80, 120, "ppb", "Ground-level ozone"),
                AlertThreshold("aqi", 80, 100, "index", "Air Quality Index")
            ],
            AlertType.GENERAL: [
                AlertThreshold("aqi", 100, 150, "index", "Air Quality Index"),
                AlertThreshold("pm25", 25.0, 50.0, "µg/m³", "PM2.5 fine particles")
            ]
        }
    
    def subscribe_user_alert_from_context(self, contact_info: str, location: str, 
                                        input_context: Dict[str, Any], 
                                        notification_method: str) -> str:
        """Subscribe user to alerts based on Input Agent context"""
        # Determine alert type from input context
        alert_type = self._determine_alert_type_from_context(input_context)
        
        alert_id = f"{contact_info}_{location}_{alert_type.value}_{int(time.time())}"
        
        # Get appropriate thresholds based on context
        thresholds = self._get_thresholds_from_context(input_context, alert_type)
        
        user_alert = UserAlert(
            contact_info=contact_info,
            location=location,
            alert_type=alert_type,
            thresholds=thresholds,
            notification_method=notification_method,
            created_at=datetime.now(),
            context_from_query=input_context
        )
        
        self.user_alerts[alert_id] = user_alert
        logger.info(f"User {contact_info} subscribed to {alert_type.value} alerts for {location}")
        
        return alert_id
    
    def _determine_alert_type_from_context(self, context: Dict[str, Any]) -> AlertType:
        """Determine alert type from Input Agent context"""
        context_type = context.get('context_type', 'general')
        special_concerns = context.get('special_concerns', [])
        
        # Map context types to alert types
        if context_type == 'health' or 'asthma' in str(special_concerns).lower():
            return AlertType.HEALTH
        elif context_type == 'industrial':
            return AlertType.INDUSTRIAL
        elif context_type == 'outdoor_activity':
            return AlertType.OUTDOOR_ACTIVITY
        else:
            return AlertType.GENERAL
    
    def _get_thresholds_from_context(self, context: Dict[str, Any], alert_type: AlertType) -> List[AlertThreshold]:
        """Get appropriate thresholds based on context"""
        # Start with default thresholds for the alert type
        thresholds = self.default_thresholds.get(alert_type, [])
        
        # Adjust based on special concerns
        special_concerns = context.get('special_concerns', [])
        if 'asthma' in str(special_concerns).lower():
            # More sensitive thresholds for asthma
            thresholds = [
                AlertThreshold("pm25", 12.0, 20.0, "µg/m³", "PM2.5 fine particles"),
                AlertThreshold("o3", 60, 80, "ppb", "Ground-level ozone"),
                AlertThreshold("aqi", 50, 80, "index", "Air Quality Index")
            ]
        
        return thresholds
    
    def unsubscribe_user_alert(self, alert_id: str) -> bool:
        """Unsubscribe a user from alerts"""
        if alert_id in self.user_alerts:
            del self.user_alerts[alert_id]
            logger.info(f"Alert subscription {alert_id} removed")
            return True
        return False
    
    def check_alerts(self, location: str, air_quality_data: Dict[str, Any]) -> List[AlertEvent]:
        """Check if current air quality data triggers any alerts"""
        triggered_alerts = []
        current_time = datetime.now()
        
        # Find all active alerts for this location
        location_alerts = [
            (alert_id, alert) for alert_id, alert in self.user_alerts.items()
            if alert.location.lower() == location.lower() and alert.is_active
        ]
        
        for alert_id, alert in location_alerts:
            for threshold in alert.thresholds:
                parameter = threshold.parameter
                current_value = self._get_parameter_value(air_quality_data, parameter)
                
                if current_value is None:
                    continue
                
                # Check if threshold is breached
                severity = None
                if current_value >= threshold.critical_level:
                    severity = AlertSeverity.CRITICAL
                elif current_value >= threshold.warning_level:
                    severity = AlertSeverity.MEDIUM
                
                if severity:
                    # Check if we should trigger (avoid spam - only if not triggered recently)
                    if (alert.last_triggered is None or 
                        current_time - alert.last_triggered > timedelta(minutes=30)):
                        
                        alert_event = AlertEvent(
                            alert_id=alert_id,
                            contact_info=alert.contact_info,
                            location=location,
                            parameter=parameter,
                            current_value=current_value,
                            threshold_value=threshold.warning_level if severity == AlertSeverity.MEDIUM else threshold.critical_level,
                            severity=severity,
                            message=self._generate_alert_message(alert, threshold, current_value, severity),
                            timestamp=current_time
                        )
                        
                        triggered_alerts.append(alert_event)
                        self.alert_history.append(alert_event)
                        
                        # Update last triggered time
                        alert.last_triggered = current_time
                        
                        logger.info(f"Alert triggered: {alert_event.message}")
        
        return triggered_alerts
    
    def _get_parameter_value(self, air_quality_data: Dict[str, Any], parameter: str) -> Optional[float]:
        """Extract parameter value from air quality data"""
        # Handle nested structure
        if parameter in air_quality_data:
            return air_quality_data[parameter]
        
        # Check in nested structures
        for category in ['air_quality', 'satellite_data', 'weather_data']:
            if category in air_quality_data and parameter in air_quality_data[category]:
                return air_quality_data[category][parameter]
        
        return None
    
    def _generate_alert_message(self, alert: UserAlert, threshold: AlertThreshold, 
                              current_value: float, severity: AlertSeverity) -> str:
        """Generate human-readable alert message"""
        severity_emoji = {
            AlertSeverity.LOW: "⚠️",
            AlertSeverity.MEDIUM: "🚨",
            AlertSeverity.HIGH: "🔴",
            AlertSeverity.CRITICAL: "🚨🚨"
        }
        
        emoji = severity_emoji.get(severity, "⚠️")
        
        if alert.alert_type == AlertType.HEALTH:
            return f"{emoji} Health Alert: {threshold.description} in {alert.location} is {current_value:.1f} {threshold.unit} (threshold: {threshold.warning_level:.1f} {threshold.unit}). Consider reducing outdoor activities."
        
        elif alert.alert_type == AlertType.INDUSTRIAL:
            return f"{emoji} Industrial Alert: {threshold.description} in {alert.location} industrial area is {current_value:.1f} {threshold.unit} (threshold: {threshold.warning_level:.1f} {threshold.unit}). Monitor ventilation systems."
        
        elif alert.alert_type == AlertType.OUTDOOR_ACTIVITY:
            return f"{emoji} Outdoor Activity Alert: Air quality in {alert.location} is not ideal for outdoor activities. {threshold.description}: {current_value:.1f} {threshold.unit} (threshold: {threshold.warning_level:.1f} {threshold.unit})."
        
        else:
            return f"{emoji} Air Quality Alert: {threshold.description} in {alert.location} is {current_value:.1f} {threshold.unit} (threshold: {threshold.warning_level:.1f} {threshold.unit})."
    
    def get_user_alerts(self, contact_info: str) -> List[Dict[str, Any]]:
        """Get all alerts for a specific contact (email/mobile)"""
        user_alert_list = []
        for alert_id, alert in self.user_alerts.items():
            if alert.contact_info == contact_info:
                user_alert_list.append({
                    'alert_id': alert_id,
                    'contact_info': alert.contact_info,
                    'location': alert.location,
                    'alert_type': alert.alert_type.value,
                    'is_active': alert.is_active,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                    'thresholds': [asdict(t) for t in alert.thresholds],
                    'context_from_query': alert.context_from_query
                })
        return user_alert_list
    
    def get_alert_history(self, contact_info: Optional[str] = None, location: Optional[str] = None, 
                         hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history with optional filters"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_alerts = []
        for alert in self.alert_history:
            if alert.timestamp < cutoff_time:
                continue
            
            if contact_info and alert.contact_info != contact_info:
                continue
            
            if location and alert.location.lower() != location.lower():
                continue
            
            filtered_alerts.append({
                'alert_id': alert.alert_id,
                'contact_info': alert.contact_info,
                'location': alert.location,
                'parameter': alert.parameter,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'is_resolved': alert.is_resolved
            })
        
        return sorted(filtered_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def start_monitoring(self, data_source_callback):
        """Start real-time monitoring (placeholder for actual implementation)"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("Alert monitoring started")
        
        # In a real implementation, this would connect to your data pipeline
        # For now, it's a placeholder for the monitoring loop
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # This would be replaced with actual data source integration
                    # data = data_source_callback()
                    # self.check_alerts(data['location'], data['air_quality'])
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(30)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Alert monitoring stopped")

# Global alert system instance
alert_system = AlertSystem()
