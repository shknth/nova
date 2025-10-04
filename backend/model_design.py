#!/usr/bin/env python3
"""
Air Quality Prediction Model Design
Multi-target regression approach for NASA Space Apps Challenge
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from scipy.spatial import KDTree
from multiprocessing import Pool, cpu_count
import os
import time
from functools import partial

def process_pm25_chunk_static(pm25_chunk, o3_data, datasets):
    """
    Static function to process a chunk of PM2.5 data in parallel
    """
    chunk_results = []
    
    # Create a temporary predictor instance for helper methods
    predictor = AirQualityPredictor()
    
    for _, pm25_row in pm25_chunk.iterrows():
        # Find matching O3 measurement
        o3_match = o3_data[
            (o3_data['datetime'] == pm25_row['datetime']) &
            (o3_data['latitude'] == pm25_row['latitude']) &
            (o3_data['longitude'] == pm25_row['longitude'])
        ]
        
        if o3_match.empty:
            continue
            
        o3_value = o3_match.iloc[0]['ground_o3']
        
        # Find nearest satellite data (spatial and temporal matching)
        satellite_features = predictor.get_nearest_satellite_data(
            datasets, pm25_row['datetime'], 
            pm25_row['latitude'], pm25_row['longitude']
        )
        
        # Find nearest weather data
        weather_features = predictor.get_nearest_weather_data(
            datasets, pm25_row['datetime'],
            pm25_row['latitude'], pm25_row['longitude']
        )
        
        # Combine all features
        if satellite_features and weather_features:
            row_data = {
                'datetime': pm25_row['datetime'],
                'latitude': pm25_row['latitude'],
                'longitude': pm25_row['longitude'],
                'city': pm25_row['city'],
                
                # Targets
                'pm25': pm25_row['ground_pm25'],
                'o3': o3_value,
                'aqi': predictor.calculate_aqi(pm25_row['ground_pm25'], o3_value),
                
                # Features
                **satellite_features,
                **weather_features
            }
            chunk_results.append(row_data)
    
    return chunk_results

class AirQualityPredictor:
    """
    Multi-target air quality prediction model
    Predicts PM2.5, O3, and AQI from satellite and weather data
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.target_names = ['pm25', 'o3', 'aqi']
        self.spatial_indices = {}  # Cache for KDTree indices
        
    def load_and_integrate_data(self, data_dir='data'):
        """
        Load and integrate all data sources into a unified dataset
        """
        print("🔄 Loading and integrating data sources...")
        
        # Load all datasets
        datasets = {}
        
        # Load 90-day datasets
        print("📊 Loading 90-day datasets...")
        datasets['tempo_no2'] = pd.read_csv(f'{data_dir}/tempo_no2_90days.csv')
        datasets['tempo_ch2o'] = pd.read_csv(f'{data_dir}/tempo_ch2o_90days.csv')
        datasets['tropomi_co'] = pd.read_csv(f'{data_dir}/tropomi_co_90days.csv')
        datasets['modis_aod'] = pd.read_csv(f'{data_dir}/modis_aod_90days.csv')
        
        # Weather data
        datasets['merra2_temp'] = pd.read_csv(f'{data_dir}/merra2_temperature_90days.csv')
        datasets['merra2_pbl'] = pd.read_csv(f'{data_dir}/merra2_pbl_90days.csv')
        datasets['merra2_wind'] = pd.read_csv(f'{data_dir}/merra2_wind_90days.csv')
        datasets['gpm_precip'] = pd.read_csv(f'{data_dir}/gpm_precipitation_90days.csv')
        
        # Ground truth
        datasets['openaq_pm25'] = pd.read_csv(f'{data_dir}/openaq_pm25_90days.csv')
        datasets['openaq_o3'] = pd.read_csv(f'{data_dir}/openaq_o3_90days.csv')
        
        print(f"✅ Loaded {len(datasets)} datasets")
        
        # Create unified dataset
        unified_data = self.create_unified_dataset(datasets)
        
        return unified_data
    
    def build_spatial_indices(self, datasets):
        """
        Build KDTree spatial indices for all datasets to speed up nearest neighbor searches
        """
        print("🌐 Building spatial indices...")
        for name, df in datasets.items():
            if 'latitude' in df.columns and 'longitude' in df.columns:
                coords = df[['latitude', 'longitude']].values
                self.spatial_indices[name] = {
                    'tree': KDTree(coords),
                    'data': df
                }
        print(f"✅ Built spatial indices for {len(self.spatial_indices)} datasets")
    
    def process_pm25_chunk(self, pm25_chunk, o3_data, datasets):
        """
        Process a chunk of PM2.5 data in parallel
        """
        chunk_results = []
        
        for _, pm25_row in pm25_chunk.iterrows():
            # Find matching O3 measurement
            o3_match = o3_data[
                (o3_data['datetime'] == pm25_row['datetime']) &
                (o3_data['latitude'] == pm25_row['latitude']) &
                (o3_data['longitude'] == pm25_row['longitude'])
            ]
            
            if o3_match.empty:
                continue
                
            o3_value = o3_match.iloc[0]['ground_o3']
            
            # Find nearest satellite data (spatial and temporal matching)
            satellite_features = self.get_nearest_satellite_data(
                datasets, pm25_row['datetime'], 
                pm25_row['latitude'], pm25_row['longitude']
            )
            
            # Find nearest weather data
            weather_features = self.get_nearest_weather_data(
                datasets, pm25_row['datetime'],
                pm25_row['latitude'], pm25_row['longitude']
            )
            
            # Combine all features
            if satellite_features and weather_features:
                row_data = {
                    'datetime': pm25_row['datetime'],
                    'latitude': pm25_row['latitude'],
                    'longitude': pm25_row['longitude'],
                    'city': pm25_row['city'],
                    
                    # Targets
                    'pm25': pm25_row['ground_pm25'],
                    'o3': o3_value,
                    'aqi': self.calculate_aqi(pm25_row['ground_pm25'], o3_value),
                    
                    # Features
                    **satellite_features,
                    **weather_features
                }
                chunk_results.append(row_data)
        
        return chunk_results
    
    def create_unified_dataset(self, datasets):
        """
        Create a unified dataset by spatially and temporally matching all sources
        Optimized with multiprocessing and spatial indexing
        """
        print("🔗 Creating unified dataset...")
        
        # Convert datetime columns
        for name, df in datasets.items():
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Build spatial indices for fast nearest neighbor searches
        self.build_spatial_indices(datasets)
        
        # Get unique ground truth locations and times
        pm25_data = datasets['openaq_pm25'].copy()
        o3_data = datasets['openaq_o3'].copy()
        
        pm25_data['datetime'] = pd.to_datetime(pm25_data['datetime'])
        o3_data['datetime'] = pd.to_datetime(o3_data['datetime'])
        
        # Split PM2.5 data into chunks for parallel processing
        num_cores = min(cpu_count(), 8)  # Limit to 8 cores max
        chunk_size = max(1, len(pm25_data) // num_cores)
        pm25_chunks = [pm25_data.iloc[i:i+chunk_size] for i in range(0, len(pm25_data), chunk_size)]
        
        print(f"🚀 Processing {len(pm25_data)} samples using {num_cores} cores in {len(pm25_chunks)} chunks")
        
        # Process chunks in parallel
        try:
            with Pool(processes=num_cores) as pool:
                # Create partial function with fixed arguments
                process_func = partial(process_pm25_chunk_static, o3_data=o3_data, datasets=datasets)
                
                # Process all chunks in parallel
                chunk_results = pool.map(process_func, pm25_chunks)
        except Exception as e:
            print(f"⚠️  Multiprocessing failed ({e}), falling back to sequential processing...")
            # Fallback to sequential processing
            chunk_results = []
            for chunk in pm25_chunks:
                result = process_pm25_chunk_static(chunk, o3_data, datasets)
                chunk_results.append(result)
        
        # Flatten results from all chunks
        base_data = []
        for chunk_result in chunk_results:
            base_data.extend(chunk_result)
        
        unified_df = pd.DataFrame(base_data)
        print(f"✅ Created unified dataset with {len(unified_df)} records")
        print(f"   Features: {len([c for c in unified_df.columns if c not in ['datetime', 'latitude', 'longitude', 'city', 'pm25', 'o3', 'aqi']])}")
        print(f"   Targets: pm25, o3, aqi")
        
        return unified_df
    
    def get_nearest_satellite_data_fast(self, datasets, target_time, target_lat, target_lon):
        """
        Find nearest satellite measurements using spatial indexing (optimized)
        """
        features = {}
        target_coords = np.array([[target_lat, target_lon]])
        
        # TEMPO NO2 (hourly)
        if 'tempo_no2' in self.spatial_indices:
            no2_match = self.find_nearest_measurement_fast(
                'tempo_no2', target_time, target_coords, 'no2'
            )
            features['tempo_no2'] = no2_match if no2_match else np.nan
        
        # TEMPO CH2O (hourly)
        if 'tempo_ch2o' in self.spatial_indices:
            ch2o_match = self.find_nearest_measurement_fast(
                'tempo_ch2o', target_time, target_coords, 'ch2o'
            )
            features['tempo_ch2o'] = ch2o_match if ch2o_match else np.nan
        
        # TROPOMI CO (daily)
        if 'tropomi_co' in self.spatial_indices:
            co_match = self.find_nearest_measurement_fast(
                'tropomi_co', target_time, target_coords, 'co', time_tolerance_hours=12
            )
            features['tropomi_co'] = co_match if co_match else np.nan
        
        # MODIS AOD (twice daily)
        if 'modis_aod' in self.spatial_indices:
            aod_match = self.find_nearest_measurement_fast(
                'modis_aod', target_time, target_coords, 'aod', time_tolerance_hours=6
            )
            features['modis_aod'] = aod_match if aod_match else np.nan
        
        return features
    
    def get_nearest_weather_data_fast(self, datasets, target_time, target_lat, target_lon):
        """
        Find nearest weather measurements using spatial indexing (optimized)
        """
        features = {}
        target_coords = np.array([[target_lat, target_lon]])
        
        # MERRA-2 Temperature
        if 'merra2_temp' in self.spatial_indices:
            temp_match = self.find_nearest_measurement_fast(
                'merra2_temp', target_time, target_coords, 'temperature_2m'
            )
            features['temperature_2m'] = temp_match if temp_match else np.nan
        
        # MERRA-2 PBL Height
        if 'merra2_pbl' in self.spatial_indices:
            pbl_match = self.find_nearest_measurement_fast(
                'merra2_pbl', target_time, target_coords, 'pbl_height'
            )
            features['pbl_height'] = pbl_match if pbl_match else np.nan
        
        # MERRA-2 Wind
        if 'merra2_wind' in self.spatial_indices:
            wind_match = self.find_nearest_measurement_fast(
                'merra2_wind', target_time, target_coords, ['wind_U', 'wind_V', 'wind_speed']
            )
            if wind_match:
                if isinstance(wind_match, dict):
                    features.update(wind_match)
                else:
                    features['wind_speed'] = wind_match
        
        # GPM Precipitation
        if 'gpm_precip' in self.spatial_indices:
            precip_match = self.find_nearest_measurement_fast(
                'gpm_precip', target_time, target_coords, 'precipitation'
            )
            features['precipitation'] = precip_match if precip_match else 0.0
        
        return features
    
    def find_nearest_measurement_fast(self, dataset_name, target_time, target_coords, 
                                    value_col, time_tolerance_hours=2, spatial_tolerance=1.0):
        """
        Find the nearest measurement using KDTree spatial indexing (optimized)
        """
        if dataset_name not in self.spatial_indices:
            return None
        
        spatial_data = self.spatial_indices[dataset_name]
        tree = spatial_data['tree']
        df = spatial_data['data']
        
        # Time filtering first
        time_diff = abs((df['datetime'] - target_time).dt.total_seconds() / 3600)
        time_mask = time_diff <= time_tolerance_hours
        
        if not time_mask.any():
            return None
        
        # Get time-filtered data and rebuild spatial index for this subset
        time_filtered_df = df[time_mask].copy()
        if len(time_filtered_df) == 0:
            return None
        
        # Find nearest spatial neighbors from time-filtered data
        time_filtered_coords = time_filtered_df[['latitude', 'longitude']].values
        time_filtered_tree = KDTree(time_filtered_coords)
        
        # Find nearest neighbor
        distances, indices = time_filtered_tree.query(target_coords, k=1)
        
        if distances[0] > spatial_tolerance:
            # If no match within spatial tolerance, return closest anyway
            pass
        
        closest_row = time_filtered_df.iloc[indices[0]]
        
        # Return value(s)
        if isinstance(value_col, list):
            return {col: closest_row[col] for col in value_col if col in closest_row}
        else:
            return closest_row[value_col] if value_col in closest_row else None
    
    def get_nearest_satellite_data(self, datasets, target_time, target_lat, target_lon):
        """
        Find nearest satellite measurements in space and time
        """
        features = {}
        
        # TEMPO NO2 (hourly, daylight only)
        tempo_no2 = datasets['tempo_no2']
        no2_match = self.find_nearest_measurement(
            tempo_no2, target_time, target_lat, target_lon, 'no2'
        )
        features['tempo_no2'] = no2_match if no2_match else np.nan
        
        # TEMPO CH2O
        tempo_ch2o = datasets['tempo_ch2o']
        ch2o_match = self.find_nearest_measurement(
            tempo_ch2o, target_time, target_lat, target_lon, 'ch2o'
        )
        features['tempo_ch2o'] = ch2o_match if ch2o_match else np.nan
        
        # TROPOMI CO (daily)
        tropomi_co = datasets['tropomi_co']
        co_match = self.find_nearest_measurement(
            tropomi_co, target_time, target_lat, target_lon, 'co', time_tolerance_hours=12
        )
        features['tropomi_co'] = co_match if co_match else np.nan
        
        # MODIS AOD (twice daily)
        modis_aod = datasets['modis_aod']
        aod_match = self.find_nearest_measurement(
            modis_aod, target_time, target_lat, target_lon, 'aod', time_tolerance_hours=6
        )
        features['modis_aod'] = aod_match if aod_match else np.nan
        
        return features
    
    def get_nearest_weather_data(self, datasets, target_time, target_lat, target_lon):
        """
        Find nearest weather measurements
        """
        features = {}
        
        # MERRA-2 Temperature
        temp_data = datasets['merra2_temp']
        temp_match = self.find_nearest_measurement(
            temp_data, target_time, target_lat, target_lon, 'temperature_2m'
        )
        features['temperature_2m'] = temp_match if temp_match else np.nan
        
        # MERRA-2 PBL Height
        pbl_data = datasets['merra2_pbl']
        pbl_match = self.find_nearest_measurement(
            pbl_data, target_time, target_lat, target_lon, 'pbl_height'
        )
        features['pbl_height'] = pbl_match if pbl_match else np.nan
        
        # MERRA-2 Wind
        wind_data = datasets['merra2_wind']
        wind_match = self.find_nearest_measurement(
            wind_data, target_time, target_lat, target_lon, ['wind_U', 'wind_V', 'wind_speed']
        )
        if wind_match:
            if isinstance(wind_match, dict):
                features.update(wind_match)
            else:
                features['wind_speed'] = wind_match
        
        # GPM Precipitation
        precip_data = datasets['gpm_precip']
        precip_match = self.find_nearest_measurement(
            precip_data, target_time, target_lat, target_lon, 'precipitation'
        )
        features['precipitation'] = precip_match if precip_match else 0.0
        
        return features
    
    def find_nearest_measurement(self, df, target_time, target_lat, target_lon, 
                               value_col, time_tolerance_hours=2, spatial_tolerance=1.0):
        """
        Find the nearest measurement in space and time
        """
        # Time filtering
        time_diff = abs((df['datetime'] - target_time).dt.total_seconds() / 3600)
        time_mask = time_diff <= time_tolerance_hours
        
        if not time_mask.any():
            return None
        
        # Spatial filtering
        lat_diff = abs(df['latitude'] - target_lat)
        lon_diff = abs(df['longitude'] - target_lon)
        spatial_distance = np.sqrt(lat_diff**2 + lon_diff**2)
        spatial_mask = spatial_distance <= spatial_tolerance
        
        # Combined filtering
        combined_mask = time_mask & spatial_mask
        
        if not combined_mask.any():
            # If no exact match, find closest in space within time window
            time_filtered = df[time_mask]
            if len(time_filtered) == 0:
                return None
            
            lat_diff = abs(time_filtered['latitude'] - target_lat)
            lon_diff = abs(time_filtered['longitude'] - target_lon)
            spatial_distance = np.sqrt(lat_diff**2 + lon_diff**2)
            closest_idx = spatial_distance.idxmin()
            closest_row = time_filtered.loc[closest_idx]
        else:
            # Find closest match within both time and space constraints
            filtered_df = df[combined_mask]
            closest_row = filtered_df.iloc[0]  # Take first match
        
        # Return value(s)
        if isinstance(value_col, list):
            return {col: closest_row[col] for col in value_col if col in closest_row}
        else:
            return closest_row[value_col] if value_col in closest_row else None
    
    def calculate_aqi(self, pm25, o3):
        """
        Calculate Air Quality Index from PM2.5 and O3
        Simplified AQI calculation
        """
        # PM2.5 AQI breakpoints (µg/m³)
        if pm25 <= 12:
            pm25_aqi = pm25 * 50 / 12
        elif pm25 <= 35.4:
            pm25_aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)
        elif pm25 <= 55.4:
            pm25_aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
        else:
            pm25_aqi = min(300, 150 + (pm25 - 55.4) * 150 / 150)
        
        # O3 AQI (simplified, assuming µg/m³)
        o3_ppb = o3 * 0.5  # Rough conversion µg/m³ to ppb
        if o3_ppb <= 54:
            o3_aqi = o3_ppb * 50 / 54
        elif o3_ppb <= 70:
            o3_aqi = 50 + (o3_ppb - 54) * 50 / (70 - 54)
        else:
            o3_aqi = min(300, 100 + (o3_ppb - 70) * 100 / 100)
        
        # Return maximum AQI (worst pollutant determines overall AQI)
        return max(pm25_aqi, o3_aqi)
    
    def prepare_features(self, df):
        """
        Prepare features for model training
        """
        # Select feature columns
        feature_cols = [
            'tempo_no2', 'tempo_ch2o', 'tropomi_co', 'modis_aod',
            'temperature_2m', 'pbl_height', 'wind_speed', 'precipitation'
        ]
        
        # Add temporal features
        df['hour'] = pd.to_datetime(df['datetime']).dt.hour
        df['day_of_year'] = pd.to_datetime(df['datetime']).dt.dayofyear
        df['is_weekend'] = pd.to_datetime(df['datetime']).dt.weekday >= 5
        
        feature_cols.extend(['hour', 'day_of_year', 'is_weekend'])
        
        # Handle missing values
        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[['pm25', 'o3', 'aqi']]
        
        self.feature_names = feature_cols
        
        return X, y
    
    def train_model(self, X, y):
        """
        Train XGBoost multi-target regression model with proper train/val/test splits
        """
        print("🤖 Training XGBoost multi-target air quality model...")
        print(f"📊 Dataset size: {X.shape[0]} samples, {X.shape[1]} features")
        
        start_time = time.time()
        
        # Split data: 60% train, 20% validation, 20% test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42  # 0.25 * 0.8 = 0.2 of total
        )
        
        print(f"📈 Data splits:")
        print(f"   Training:   {X_train.shape[0]:,} samples ({X_train.shape[0]/X.shape[0]*100:.1f}%)")
        print(f"   Validation: {X_val.shape[0]:,} samples ({X_val.shape[0]/X.shape[0]*100:.1f}%)")
        print(f"   Test:       {X_test.shape[0]:,} samples ({X_test.shape[0]/X.shape[0]*100:.1f}%)")
        
        # Scale features
        print("⚙️  Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Configure XGBoost for multi-target regression
        print("🚀 Training XGBoost model...")
        xgb_params = {
            'n_estimators': 200,
            'max_depth': 8,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        
        # Use MultiOutputRegressor for multi-target
        self.model = MultiOutputRegressor(
            xgb.XGBRegressor(**xgb_params)
        )
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        training_time = time.time() - start_time
        print(f"✅ Model training completed in {training_time:.1f} seconds!")
        
        # Evaluate on all splits
        print("\n📊 Model Performance:")
        
        # Training performance
        y_train_pred = self.model.predict(X_train_scaled)
        print("\n🔵 TRAINING SET:")
        self._evaluate_predictions(y_train, y_train_pred)
        
        # Validation performance
        y_val_pred = self.model.predict(X_val_scaled)
        print("\n🟡 VALIDATION SET:")
        self._evaluate_predictions(y_val, y_val_pred)
        
        # Test performance
        y_test_pred = self.model.predict(X_test_scaled)
        print("\n🔴 TEST SET:")
        self._evaluate_predictions(y_test, y_test_pred)
        
        # Feature importance
        print("\n🎯 FEATURE IMPORTANCE (Top 5):")
        self._show_feature_importance()
        
        return self.model
    
    def _evaluate_predictions(self, y_true, y_pred):
        """Evaluate model predictions"""
        for i, target in enumerate(self.target_names):
            r2 = r2_score(y_true.iloc[:, i], y_pred[:, i])
            rmse = np.sqrt(mean_squared_error(y_true.iloc[:, i], y_pred[:, i]))
            mae = mean_absolute_error(y_true.iloc[:, i], y_pred[:, i])
            print(f"   {target.upper():4}: R² = {r2:.3f}, RMSE = {rmse:.2f}, MAE = {mae:.2f}")
    
    def _show_feature_importance(self):
        """Show feature importance from XGBoost"""
        try:
            # Get feature importance from first estimator (they should be similar)
            importance = self.model.estimators_[0].feature_importances_
            feature_importance = list(zip(self.feature_names, importance))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            for feature, importance in feature_importance[:5]:
                print(f"   {feature:15}: {importance:.3f}")
        except Exception as e:
            print(f"   Could not display feature importance: {str(e)}")
    
    def predict(self, satellite_data, weather_data, location, time):
        """
        Make air quality predictions for new data
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Prepare input features
        features = {
            'tempo_no2': satellite_data.get('no2', np.nan),
            'tempo_ch2o': satellite_data.get('ch2o', np.nan),
            'tropomi_co': satellite_data.get('co', np.nan),
            'modis_aod': satellite_data.get('aod', np.nan),
            'temperature_2m': weather_data.get('temperature', np.nan),
            'pbl_height': weather_data.get('pbl_height', np.nan),
            'wind_speed': weather_data.get('wind_speed', np.nan),
            'precipitation': weather_data.get('precipitation', 0.0),
            'hour': time.hour,
            'day_of_year': time.timetuple().tm_yday,
            'is_weekend': time.weekday() >= 5
        }
        
        # Create feature vector
        X = np.array([[features[col] for col in self.feature_names]])
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)[0]
        
        return {
            'pm25': predictions[0],
            'o3': predictions[1], 
            'aqi': predictions[2],
            'health_risk': self.get_health_risk(predictions[2]),
            'location': location,
            'timestamp': time
        }
    
    def get_health_risk(self, aqi):
        """
        Convert AQI to health risk category
        """
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        else:
            return "Very Unhealthy"

def main():
    """
    Demonstrate the modeling approach
    """
    print("🚀 NASA SPACE APPS - AIR QUALITY PREDICTION MODEL")
    print("=" * 60)
    
    # Initialize predictor
    predictor = AirQualityPredictor()
    
    # Load and integrate data
    try:
        unified_data = predictor.load_and_integrate_data()
        
        if len(unified_data) > 0:
            print(f"\n📊 Unified Dataset Summary:")
            print(f"   Records: {len(unified_data)}")
            print(f"   Cities: {unified_data['city'].nunique()}")
            print(f"   Time range: {unified_data['datetime'].min()} to {unified_data['datetime'].max()}")
            
            # Prepare features
            X, y = predictor.prepare_features(unified_data)
            
            if len(X) > 10:  # Need minimum data for training
                # Train model
                model = predictor.train_model(X, y)
                
                print(f"\n🎯 MODEL READY FOR DEPLOYMENT!")
                print(f"   Input: Satellite + Weather data")
                print(f"   Output: PM2.5, O₃, AQI predictions")
                print(f"   Use case: Real-time air quality forecasting")
            else:
                print("⚠️  Insufficient data for model training")
        else:
            print("❌ No unified data created - check data integration")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
