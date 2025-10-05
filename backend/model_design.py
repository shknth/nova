#!/usr/bin/env python3
"""
Air Quality Prediction Model Design
Multi-target regression approach for NASA Space Apps Challenge
Updated to work with comprehensive_unified_dataset.csv
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
import os
import time
import warnings
warnings.filterwarnings('ignore')

def load_comprehensive_dataset(data_path='preprocessed_data/comprehensive_unified_dataset.csv', dry_run=False, sample_size=100):
    """
    Load the comprehensive unified dataset
    """
    print(f"📊 Loading comprehensive dataset from: {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found: {data_path}")
    
    # Load dataset
    df = pd.read_csv(data_path)
    print(f"✅ Loaded dataset with {len(df)} records and {len(df.columns)} features")
    
    # Dry run mode - sample small subset
    if dry_run:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
        print(f"🧪 DRY RUN MODE: Using {len(df)} records for testing")
    
    return df

class AirQualityPredictor:
    """
    Multi-target air quality prediction model
    Predicts PM2.5, O3, NO2, CO, and AQI from comprehensive dataset
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        # Updated target names to match your desired output structure
        self.target_names = [
            # Satellite measurements
            'tempo_no2_no2_weight', 'tempo_hcho_hcho_weight', 'tempo_co_co_vmr', 'aerosol',
            # Weather conditions  
            'temperature_2m', 'merra2_wind_speed', 'precipitation',
            # Air quality metrics (AQI will be calculated)
            'ground_pm25', 'ground_o3', 'ground_no2', 'ground_co'
        ]
        self.dataset = None
        
    def load_data(self, data_path='preprocessed_data/comprehensive_unified_dataset.csv', dry_run=False, sample_size=100):
        """
        Load the comprehensive unified dataset
        """
        self.dataset = load_comprehensive_dataset(data_path, dry_run, sample_size)
        return self.dataset
    
    def analyze_dataset(self):
        """
        Analyze the loaded dataset structure and quality
        """
        if self.dataset is None:
            print("❌ No dataset loaded")
            return
        
        df = self.dataset
        print(f"\n📊 DATASET ANALYSIS")
        print(f"{'='*50}")
        print(f"📋 Shape: {df.shape}")
        
        # Handle datetime column safely
        if 'datetime' in df.columns:
            try:
                # Convert to datetime if not already
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                valid_dates = df['datetime'].dropna()
                if len(valid_dates) > 0:
                    print(f"📅 Date range: {valid_dates.min()} to {valid_dates.max()}")
                else:
                    print("📅 No valid datetime values found")
            except Exception as e:
                print(f"📅 Datetime column exists but has issues: {str(e)}")
        else:
            print("📅 No datetime column")
        
        # Check target variables
        print(f"\n🎯 TARGET VARIABLES:")
        for target in self.target_names:
            if target in df.columns:
                non_null = df[target].notna().sum()
                print(f"   {target:15}: {non_null:,} non-null ({non_null/len(df)*100:.1f}%)")
            else:
                print(f"   {target:15}: ❌ Missing")
        
        # Check feature completeness
        print(f"\n📈 FEATURE COMPLETENESS:")
        feature_cols = [col for col in df.columns if col not in ['datetime', 'lat', 'lon'] + self.target_names]
        for col in feature_cols[:10]:  # Show first 10 features
            non_null = df[col].notna().sum()
            print(f"   {col:20}: {non_null:,} non-null ({non_null/len(df)*100:.1f}%)")
        
        if len(feature_cols) > 10:
            print(f"   ... and {len(feature_cols)-10} more features")
    
    def prepare_features(self, df=None):
        """
        Prepare features and targets from the comprehensive dataset
        Uses only location/time as input features to predict everything else
        """
        if df is None:
            df = self.dataset
        
        if df is None:
            raise ValueError("No dataset loaded. Call load_data() first.")
        
        print("🔧 Preparing features and targets...")
        print("🎯 NEW APPROACH: Using only location/time to predict satellite/weather/air quality")
        
        # Convert datetime to useful features
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df['hour'] = df['datetime'].dt.hour
            df['day_of_year'] = df['datetime'].dt.dayofyear
            df['month'] = df['datetime'].dt.month
            df['is_weekend'] = df['datetime'].dt.weekday >= 5
        
        # Use only basic location and time features as INPUT
        basic_features = ['lat', 'lon', 'hour', 'day_of_year', 'month', 'is_weekend']
        available_features = [col for col in basic_features if col in df.columns]
        
        print(f"📊 INPUT FEATURES (only location/time): {len(available_features)}")
        for i, col in enumerate(available_features):
            print(f"   {i+1:2d}. {col}")
        
        # Prepare features
        X = df[available_features].copy()
        
        # Handle missing values
        for col in X.columns:
            if X[col].dtype in ['float64', 'int64']:
                X[col] = X[col].fillna(X[col].median())
            else:
                X[col] = X[col].fillna(0)
        
        # Map target names to actual column names in dataset
        target_mapping = {
            # Satellite measurements
            'tempo_no2': 'tempo_no2_no2_weight',
            'tempo_ch2o': 'tempo_hcho_hcho_weight', 
            'tropomi_co': 'tempo_co_co_vmr',
            'modis_aod': 'aerosol',
            # Weather conditions
            'temperature_2m': 'temperature_2m',
            'wind_speed': 'wind_speed',
            'precipitation': 'precipitation',  # Will use 0 if not available
            # Air quality
            'pm25': 'ground_pm25',
            'o3': 'ground_o3',
            'no2': 'ground_no2',
            'co': 'ground_co'
        }
        
        # Find available targets in dataset
        available_targets = []
        target_columns = []
        
        for desired_name, actual_col in target_mapping.items():
            if actual_col in df.columns:
                available_targets.append(desired_name)
                target_columns.append(actual_col)
            else:
                print(f"   ⚠️  {desired_name} ({actual_col}) not found in dataset")
        
        if not target_columns:
            raise ValueError(f"No target columns found in dataset!")
        
        # Prepare targets
        y = df[target_columns].copy()
        y.columns = available_targets  # Rename to desired names
        
        # Fill missing target values
        for col in y.columns:
            if y[col].dtype in ['float64', 'int64']:
                y[col] = y[col].fillna(y[col].median())
            else:
                y[col] = y[col].fillna(0)
        
        self.feature_names = available_features
        self.target_names = available_targets
        
        print(f"✅ Features prepared: {X.shape}")
        print(f"✅ Targets prepared: {y.shape}")
        print(f"🎯 PREDICTION TARGETS:")
        for target in available_targets:
            print(f"   📊 {target}")
        
        return X, y
    
    def train_model(self, X, y, model_type='xgboost'):
        """
        Train multi-target regression model
        """
        print("🤖 Training multi-target air quality prediction model...")
        print(f"📊 Dataset: {X.shape[0]} samples, {X.shape[1]} features")
        print(f"🎯 Targets: {len(y.columns)} variables - {list(y.columns)}")
        
        start_time = time.time()
        
        # Split data: 70% train, 15% validation, 15% test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=42  # 0.176 * 0.85 ≈ 0.15
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
        
        # Choose model
        if model_type == 'xgboost':
            print("🚀 Training XGBoost model...")
            base_model = xgb.XGBRegressor(
                n_estimators=100,  # Reduced for dry run
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )
        else:
            print("🌲 Training Random Forest model...")
            base_model = RandomForestRegressor(
                n_estimators=50,  # Reduced for dry run
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        
        # Multi-target wrapper
        self.model = MultiOutputRegressor(base_model)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        training_time = time.time() - start_time
        print(f"✅ Model training completed in {training_time:.1f} seconds!")
        
        # Evaluate on all splits
        print("\\n📊 MODEL PERFORMANCE:")
        
        # Training performance
        y_train_pred = self.model.predict(X_train_scaled)
        print("\\n🔵 TRAINING SET:")
        self._evaluate_predictions(y_train, y_train_pred)
        
        # Validation performance
        y_val_pred = self.model.predict(X_val_scaled)
        print("\\n🟡 VALIDATION SET:")
        self._evaluate_predictions(y_val, y_val_pred)
        
        # Test performance
        y_test_pred = self.model.predict(X_test_scaled)
        print("\\n🔴 TEST SET:")
        self._evaluate_predictions(y_test, y_test_pred)
        
        return self.model
    
    def _evaluate_predictions(self, y_true, y_pred):
        """Evaluate model predictions"""
        for i, target in enumerate(self.target_names):
            if i < y_pred.shape[1]:  # Check if prediction exists for this target
                r2 = r2_score(y_true.iloc[:, i], y_pred[:, i])
                rmse = np.sqrt(mean_squared_error(y_true.iloc[:, i], y_pred[:, i]))
                mae = mean_absolute_error(y_true.iloc[:, i], y_pred[:, i])
                print(f"   {target:15}: R² = {r2:.3f}, RMSE = {rmse:.2f}, MAE = {mae:.2f}")
    
    def predict_comprehensive(self, lat, lon, datetime_str):
        """
        Make comprehensive predictions from lat/lon/datetime
        Returns the exact structure you requested
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Parse datetime
        import pandas as pd
        from datetime import datetime
        
        if isinstance(datetime_str, str):
            dt = pd.to_datetime(datetime_str)
        else:
            dt = datetime_str
        
        # Prepare input features
        sample_features = {
            'lat': lat,
            'lon': lon,
            'hour': dt.hour,
            'day_of_year': dt.timetuple().tm_yday,
            'month': dt.month,
            'is_weekend': dt.weekday() >= 5
        }
        
        # Create feature vector
        X = np.array([[sample_features.get(col, 0.0) for col in self.feature_names]])
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)[0]
        
        # Map predictions to target names
        pred_dict = {}
        for i, target in enumerate(self.target_names):
            if i < len(predictions):
                pred_dict[target] = predictions[i]
        
        # Calculate AQI from predicted PM2.5 and O3
        pm25 = pred_dict.get('pm25', 0)
        o3 = pred_dict.get('o3', 0)
        aqi = self.calculate_aqi(pm25, o3)
        
        # Structure the response exactly as you requested
        result = {
            "satellite_data": {
                "tempo_no2": pred_dict.get('tempo_no2', 0),
                "tempo_ch2o": pred_dict.get('tempo_ch2o', 0),
                "tropomi_co": pred_dict.get('tropomi_co', 0),
                "modis_aod": pred_dict.get('modis_aod', 0)
            },
            "weather_data": {
                "temperature_2m": pred_dict.get('temperature_2m', 0),
                "pbl_height": 800,  # Default value - add if available in dataset
                "wind_speed": pred_dict.get('wind_speed', 0),
                "precipitation": pred_dict.get('precipitation', 0)
            },
            "air_quality": {
                "pm25": pred_dict.get('pm25', 0),
                "o3": pred_dict.get('o3', 0),
                "aqi": aqi  # CALCULATED from PM2.5 + O3
            }
        }
        
        return result
    
    def calculate_aqi(self, pm25, o3):
        """
        Calculate Air Quality Index from PM2.5 and O3
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
    
def run_dry_run_pipeline(sample_size=100, model_type='xgboost'):
    """
    Run a complete dry run of the air quality prediction pipeline
    """
    print("🧪 STARTING DRY RUN PIPELINE")
    print("="*60)
    
    try:
        # Initialize predictor
        predictor = AirQualityPredictor()
        
        # Load data in dry run mode
        print("\\n📊 STEP 1: Loading Data")
        predictor.load_data(dry_run=True, sample_size=sample_size)
        
        # Analyze dataset
        print("\\n🔍 STEP 2: Dataset Analysis")
        predictor.analyze_dataset()
        
        # Prepare features
        print("\\n🔧 STEP 3: Feature Preparation")
        X, y = predictor.prepare_features()
        
        # Train model
        print("\\n🤖 STEP 4: Model Training")
        model = predictor.train_model(X, y, model_type=model_type)
        
        # Test comprehensive prediction
        print("\\n🎯 STEP 5: Comprehensive Prediction Test")
        # Use sample location and time
        sample_lat = -61.0
        sample_lon = 64.375
        sample_datetime = "2025-09-01 14:00:00"
        
        print(f"📍 Test Location: {sample_lat}, {sample_lon}")
        print(f"🕐 Test Time: {sample_datetime}")
        
        prediction = predictor.predict_comprehensive(sample_lat, sample_lon, sample_datetime)
        
        print("\\n📊 COMPREHENSIVE PREDICTION RESULT:")
        print("🛰️  Satellite Data:")
        for key, value in prediction["satellite_data"].items():
            print(f"   {key}: {value:.3e}")
        
        print("\\n🌤️  Weather Data:")
        for key, value in prediction["weather_data"].items():
            print(f"   {key}: {value:.2f}")
        
        print("\\n🏭 Air Quality:")
        for key, value in prediction["air_quality"].items():
            print(f"   {key}: {value:.2f}")
        
        print("\\n✅ DRY RUN COMPLETED SUCCESSFULLY!")
        print("🚀 Pipeline is ready for full-scale training!")
        
        return predictor
        
    except Exception as e:
        print(f"\\n❌ DRY RUN FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
def run_full_pipeline(model_type='xgboost'):
    """
    Run the complete air quality prediction pipeline with full dataset
    """
    print("🚀 STARTING FULL PIPELINE")
    print("="*60)
    
    try:
        # Initialize predictor
        predictor = AirQualityPredictor()
        
        # Load full data
        print("\\n📊 STEP 1: Loading Full Dataset")
        predictor.load_data(dry_run=False)
        
        # Analyze dataset
        print("\\n🔍 STEP 2: Dataset Analysis")
        predictor.analyze_dataset()
        
        # Prepare features
        print("\\n🔧 STEP 3: Feature Preparation")
        X, y = predictor.prepare_features()
        
        # Train model
        print("\\n🤖 STEP 4: Model Training")
        model = predictor.train_model(X, y, model_type=model_type)
        
        print("\\n✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
        print("🎯 Model is ready for production use!")
        
        return predictor
        
    except Exception as e:
        print(f"\\n❌ FULL PIPELINE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main function - run dry run by default, full pipeline optionally
    """
    print("🚀 NASA SPACE APPS - AIR QUALITY PREDICTION MODEL")
    print("=" * 60)
    
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        print("🎯 Running FULL PIPELINE with complete dataset...")
        predictor = run_full_pipeline(model_type='xgboost')
    else:
        print("🧪 Running DRY RUN with 100 samples...")
        print("   (Use --full flag for complete dataset)")
        predictor = run_dry_run_pipeline(sample_size=100, model_type='xgboost')
    
    if predictor:
        print("\\n🎉 SUCCESS! Model pipeline completed.")
        print("📊 Model is trained and ready for predictions!")
    else:
        print("\\n💥 FAILED! Check the error messages above.")

if __name__ == "__main__":
    main()
