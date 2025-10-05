"""
Dashboard Configuration for AuraCast
Defines dashboard layouts, component configurations, and visualization settings
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class DashboardComponent:
    """Configuration for a dashboard component"""
    component_id: str
    component_type: str
    title: str
    description: str
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int  # seconds
    data_source: str
    visualization_config: Dict[str, Any]

class DashboardConfig:
    """Dashboard configuration manager"""
    
    def __init__(self):
        self.components = self._initialize_components()
        self.layouts = self._initialize_layouts()
        self.color_schemes = self._initialize_color_schemes()
    
    def _initialize_components(self) -> Dict[str, DashboardComponent]:
        """Initialize all available dashboard components"""
        return {
            'aqi_gauge': DashboardComponent(
                component_id='aqi_gauge',
                component_type='gauge',
                title='Air Quality Index',
                description='Current AQI with health risk indicator',
                position={'x': 0, 'y': 0, 'width': 4, 'height': 3},
                refresh_interval=60,
                data_source='air_quality.aqi',
                visualization_config={
                    'min_value': 0,
                    'max_value': 300,
                    'thresholds': [
                        {'value': 50, 'color': '#00e400', 'label': 'Good'},
                        {'value': 100, 'color': '#ffff00', 'label': 'Moderate'},
                        {'value': 150, 'color': '#ff7e00', 'label': 'Unhealthy for Sensitive Groups'},
                        {'value': 200, 'color': '#ff0000', 'label': 'Unhealthy'},
                        {'value': 300, 'color': '#8f3f97', 'label': 'Very Unhealthy'}
                    ],
                    'show_needle': True,
                    'show_labels': True
                }
            ),
            
            'pollutant_chart': DashboardComponent(
                component_id='pollutant_chart',
                component_type='bar_chart',
                title='Pollutant Levels',
                description='Current levels of major air pollutants',
                position={'x': 4, 'y': 0, 'width': 8, 'height': 3},
                refresh_interval=60,
                data_source='air_quality',
                visualization_config={
                    'x_axis': 'pollutant',
                    'y_axis': 'value',
                    'colors': {
                        'pm25': '#ff6b6b',
                        'pm10': '#4ecdc4',
                        'o3': '#45b7d1',
                        'no2': '#96ceb4',
                        'so2': '#feca57',
                        'co': '#ff9ff3'
                    },
                    'show_values': True,
                    'horizontal': False
                }
            ),
            
            'hourly_trend': DashboardComponent(
                component_id='hourly_trend',
                component_type='line_chart',
                title='24-Hour AQI Trend',
                description='AQI trend over the last 24 hours',
                position={'x': 0, 'y': 3, 'width': 12, 'height': 4},
                refresh_interval=300,
                data_source='trends.hourly_data',
                visualization_config={
                    'x_axis': 'timestamp',
                    'y_axis': 'aqi',
                    'line_color': '#2c3e50',
                    'fill_area': True,
                    'show_points': True,
                    'smooth_curve': True,
                    'grid_lines': True
                }
            ),
            
            'weather_widget': DashboardComponent(
                component_id='weather_widget',
                component_type='weather_card',
                title='Current Weather',
                description='Real-time weather conditions',
                position={'x': 0, 'y': 7, 'width': 6, 'height': 3},
                refresh_interval=300,
                data_source='weather_data',
                visualization_config={
                    'show_icon': True,
                    'show_temperature': True,
                    'show_humidity': True,
                    'show_wind': True,
                    'show_pressure': True,
                    'compact_mode': False
                }
            ),
            
            'forecast_chart': DashboardComponent(
                component_id='forecast_chart',
                component_type='forecast_chart',
                title='6-Hour Forecast',
                description='Air quality forecast for next 6 hours',
                position={'x': 6, 'y': 7, 'width': 6, 'height': 3},
                refresh_interval=600,
                data_source='forecast.next_6h',
                visualization_config={
                    'show_aqi': True,
                    'show_pm25': True,
                    'show_o3': True,
                    'show_health_risk': True,
                    'color_by_risk': True
                }
            ),
            
            'satellite_data': DashboardComponent(
                component_id='satellite_data',
                component_type='satellite_card',
                title='Satellite Observations',
                description='NASA satellite data and imagery',
                position={'x': 0, 'y': 10, 'width': 6, 'height': 3},
                refresh_interval=1800,
                data_source='satellite_data',
                visualization_config={
                    'show_tempo_data': True,
                    'show_modis_data': True,
                    'show_cloud_cover': True,
                    'format_scientific': True
                }
            ),
            
            'trend_indicators': DashboardComponent(
                component_id='trend_indicators',
                component_type='trend_indicators',
                title='Trend Analysis',
                description='Direction of air quality trends',
                position={'x': 6, 'y': 10, 'width': 6, 'height': 3},
                refresh_interval=300,
                data_source='trends',
                visualization_config={
                    'show_icons': True,
                    'show_direction': True,
                    'show_arrows': True,
                    'color_coded': True
                }
            ),
            
            'alerts_panel': DashboardComponent(
                component_id='alerts_panel',
                component_type='alerts_panel',
                title='Active Alerts',
                description='Current air quality alerts and warnings',
                position={'x': 0, 'y': 13, 'width': 12, 'height': 2},
                refresh_interval=60,
                data_source='alerts',
                visualization_config={
                    'show_active_count': True,
                    'show_health_warnings': True,
                    'show_alert_history': False,
                    'compact_mode': True
                }
            )
        }
    
    def _initialize_layouts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize different dashboard layouts"""
        return {
            'default': {
                'name': 'Default Layout',
                'description': 'Standard dashboard layout with all components',
                'grid_size': {'columns': 12, 'rows': 15},
                'components': list(self.components.keys())
            },
            'compact': {
                'name': 'Compact Layout',
                'description': 'Condensed layout for smaller screens',
                'grid_size': {'columns': 8, 'rows': 10},
                'components': ['aqi_gauge', 'pollutant_chart', 'hourly_trend', 'weather_widget']
            },
            'analyst': {
                'name': 'Analyst Layout',
                'description': 'Detailed layout for data analysis',
                'grid_size': {'columns': 16, 'rows': 20},
                'components': list(self.components.keys()) + ['detailed_forecast', 'historical_data']
            },
            'mobile': {
                'name': 'Mobile Layout',
                'description': 'Mobile-optimized single column layout',
                'grid_size': {'columns': 4, 'rows': 20},
                'components': ['aqi_gauge', 'pollutant_chart', 'weather_widget', 'alerts_panel']
            }
        }
    
    def _initialize_color_schemes(self) -> Dict[str, Dict[str, str]]:
        """Initialize color schemes for different themes"""
        return {
            'default': {
                'primary': '#2c3e50',
                'secondary': '#3498db',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'info': '#17a2b8',
                'light': '#f8f9fa',
                'dark': '#343a40'
            },
            'dark': {
                'primary': '#ffffff',
                'secondary': '#6c757d',
                'success': '#28a745',
                'warning': '#ffc107',
                'danger': '#dc3545',
                'info': '#17a2b8',
                'light': '#495057',
                'dark': '#212529'
            },
            'nature': {
                'primary': '#2d5016',
                'secondary': '#4a7c59',
                'success': '#6b8e23',
                'warning': '#daa520',
                'danger': '#cd5c5c',
                'info': '#4682b4',
                'light': '#f0f8ff',
                'dark': '#2f4f4f'
            }
        }
    
    def get_component_config(self, component_id: str) -> DashboardComponent:
        """Get configuration for a specific component"""
        return self.components.get(component_id)
    
    def get_layout_config(self, layout_name: str) -> Dict[str, Any]:
        """Get configuration for a specific layout"""
        return self.layouts.get(layout_name, self.layouts['default'])
    
    def get_color_scheme(self, scheme_name: str) -> Dict[str, str]:
        """Get color scheme for a specific theme"""
        return self.color_schemes.get(scheme_name, self.color_schemes['default'])
    
    def get_dashboard_metadata(self) -> Dict[str, Any]:
        """Get metadata about available dashboard configurations"""
        return {
            'available_components': list(self.components.keys()),
            'available_layouts': list(self.layouts.keys()),
            'available_color_schemes': list(self.color_schemes.keys()),
            'total_components': len(self.components),
            'default_layout': 'default',
            'default_color_scheme': 'default'
        }
    
    def get_component_list(self) -> List[Dict[str, Any]]:
        """Get list of all components with their basic info"""
        return [
            {
                'id': comp.component_id,
                'type': comp.component_type,
                'title': comp.title,
                'description': comp.description,
                'refresh_interval': comp.refresh_interval
            }
            for comp in self.components.values()
        ]

# Global dashboard configuration instance
dashboard_config = DashboardConfig()
