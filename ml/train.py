"""
Complete ML training pipeline for healthcare recovery forecasting.
Includes data preprocessing, feature engineering, model training, and evaluation.
"""

import numpy as np
import pandas as pd
import pickle
import warnings
from datetime import datetime
from typing import Tuple, Dict, Any

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, median_absolute_error, r2_score, mean_squared_error
import xgboost as xgb

from data_generator import generate_synthetic_data

warnings.filterwarnings('ignore')


class DataPreprocessor:
    """Handle data cleaning, feature engineering, and preparation."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        
    def preprocess(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Preprocess raw patient data.
        
        Args:
            df: Raw patient dataframe
            fit: Whether to fit transformers (True for training data)
            
        Returns:
            Preprocessed dataframe
        """
        df = df.copy()
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Feature engineering
        df = self._engineer_features(df)
        
        # Encode categorical variables
        df = self._encode_categorical(df, fit=fit)
        
        # Remove feature columns no longer needed
        df = df.drop(['admission_date', 'discharge_date', 'gender'], axis=1)
        
        # Scale numerical features
        if fit:
            df = self._fit_and_scale(df)
        else:
            df = self._scale(df)
            
        self.feature_names = df.columns.tolist()
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values."""
        # Fill with median for numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            if df[col].isna().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        # Fill with mode for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isna().any():
                df[col].fillna(df[col].mode()[0], inplace=True)
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create new features from existing ones."""
        
        # Mean Arterial Pressure
        df['map'] = (df['bp_systolic'] + 2 * df['bp_diastolic']) / 3
        
        # Pulse Pressure
        df['pulse_pressure'] = df['bp_systolic'] - df['bp_diastolic']
        
        # Comorbidity count
        comorbidity_cols = ['has_diabetes', 'has_hypertension', 'has_copd', 
                           'has_heart_disease', 'has_kidney_disease']
        df['comorbidity_count'] = df[comorbidity_cols].sum(axis=1)
        
        # Clinical risk score (composite)
        df['clinical_risk'] = (
            (df['white_blood_cells'] > 12).astype(int) +
            (df['heart_rate'] > 100).astype(int) +
            (df['temperature'] > 38).astype(int) +
            (df['respiratory_rate'] > 20).astype(int) +
            (df['creatinine'] > 1.5).astype(int)
        )
        
        # BMI category risk
        df['bmi_risk'] = pd.cut(df['bmi'], bins=[0, 18.5, 25, 30, 35, 100],
                                labels=[1, 2, 3, 4, 5], ordered=False).astype(int)
        
        # Age groups
        df['age_group'] = pd.cut(df['age'], bins=[0, 30, 50, 70, 100],
                                 labels=[1, 2, 3, 4]).astype(int)
        
        # Glucose risk
        df['glucose_risk'] = pd.cut(df['glucose'], bins=[0, 100, 126, 200, 400],
                                    labels=[1, 2, 3, 4]).astype(int)
        
        # Hemoglobin risk
        df['hemoglobin_risk'] = pd.cut(df['hemoglobin'], bins=[0, 7, 9, 12, 20],
                                       labels=[4, 3, 2, 1]).astype(int)
        
        return df
    
    def _encode_categorical(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Encode categorical variables."""
        if fit:
            # Gender encoding
            if 'gender' in df.columns:
                self.label_encoders['gender'] = LabelEncoder()
                df['gender_encoded'] = self.label_encoders['gender'].fit_transform(df['gender'])
        else:
            if 'gender' in df.columns:
                df['gender_encoded'] = self.label_encoders['gender'].transform(df['gender'])
        
        return df
    
    def _fit_and_scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit scaler and transform numerical features."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude target variable if present
        if 'los_actual' in numerical_cols:
            numerical_cols.remove('los_actual')
        if 'severity_level' in numerical_cols:
            numerical_cols.remove('severity_level')
            
        df[numerical_cols] = self.scaler.fit_transform(df[numerical_cols])
        return df
    
    def _scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform numerical features using fitted scaler."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'los_actual' in numerical_cols:
            numerical_cols.remove('los_actual')
        if 'severity_level' in numerical_cols:
            numerical_cols.remove('severity_level')
            
        df[numerical_cols] = self.scaler.transform(df[numerical_cols])
        return df


class RecoveryModelTrainer:
    """Train and evaluate recovery prediction models."""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.xgb_model = None
        self.rf_model = None
        self.preprocessor = None
        self.metrics = {}
        
    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.2) -> Tuple:
        """Prepare data for training."""
        self.preprocessor = DataPreprocessor()
        
        # Preprocess
        df_processed = self.preprocessor.preprocess(df, fit=True)
        
        # Separate features and target
        X = df_processed.drop(['los_actual', 'severity_level'], axis=1)
        y = df_processed['los_actual']
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )
        
        return X_train, X_test, y_train, y_test, X.columns.tolist()
    
    def train_xgboost(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train XGBoost regressor optimized for healthcare data."""
        print("Training XGBoost model...")
        
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='reg:squarederror',  # Absolute error for robustness
            random_state=self.random_state,
            verbosity=0,
            enable_categorical=False
        )
        
        self.xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train)],
            verbose=False
        )
        
        print("✓ XGBoost training complete")
    
    def train_random_forest(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train Random Forest regressor."""
        print("Training Random Forest model...")
        
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.rf_model.fit(X_train, y_train)
        print("✓ Random Forest training complete")
    
    def evaluate_models(self, X_test: np.ndarray, y_test: np.ndarray, 
                       feature_names: list) -> Dict[str, Dict]:
        """Evaluate both models using appropriate metrics for healthcare."""
        results = {}
        
        # XGBoost evaluation
        if self.xgb_model:
            y_pred_xgb = self.xgb_model.predict(X_test)
            results['xgboost'] = {
                'mae': mean_absolute_error(y_test, y_pred_xgb),
                'median_ae': median_absolute_error(y_test, y_pred_xgb),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_xgb)),
                'r2': r2_score(y_test, y_pred_xgb),
                'predictions': y_pred_xgb,
            }
            
            print(f"\nXGBoost Model Performance:")
            print(f"  MAE:  {results['xgboost']['mae']:.2f} days")
            print(f"  Median AE: {results['xgboost']['median_ae']:.2f} days")
            print(f"  RMSE: {results['xgboost']['rmse']:.2f} days")
            print(f"  R²:   {results['xgboost']['r2']:.4f}")
        
        # Random Forest evaluation
        if self.rf_model:
            y_pred_rf = self.rf_model.predict(X_test)
            results['random_forest'] = {
                'mae': mean_absolute_error(y_test, y_pred_rf),
                'median_ae': median_absolute_error(y_test, y_pred_rf),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_rf)),
                'r2': r2_score(y_test, y_pred_rf),
                'predictions': y_pred_rf,
            }
            
            print(f"\nRandom Forest Model Performance:")
            print(f"  MAE:  {results['random_forest']['mae']:.2f} days")
            print(f"  Median AE: {results['random_forest']['median_ae']:.2f} days")
            print(f"  RMSE: {results['random_forest']['rmse']:.2f} days")
            print(f"  R²:   {results['random_forest']['r2']:.4f}")
        
        self.metrics = results
        return results
    
    def get_feature_importance(self, feature_names: list) -> pd.DataFrame:
        """Extract feature importance from both models."""
        importance_dfs = []
        
        if self.xgb_model:
            xgb_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': self.xgb_model.feature_importances_,
                'model': 'XGBoost'
            }).sort_values('importance', ascending=False)
            importance_dfs.append(xgb_importance)
        
        if self.rf_model:
            rf_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': self.rf_model.feature_importances_,
                'model': 'Random Forest'
            }).sort_values('importance', ascending=False)
            importance_dfs.append(rf_importance)
        
        return pd.concat(importance_dfs, ignore_index=True) if importance_dfs else pd.DataFrame()
    
    def save_models(self, output_dir: str = './') -> None:
        """Save trained models and preprocessor."""
        print(f"\nSaving models to {output_dir}...")
        
        if self.xgb_model:
            self.xgb_model.save_model(f'{output_dir}/xgboost_model.json')
        
        if self.rf_model:
            with open(f'{output_dir}/random_forest_model.pkl', 'wb') as f:
                pickle.dump(self.rf_model, f)
        
        with open(f'{output_dir}/preprocessor.pkl', 'wb') as f:
            pickle.dump(self.preprocessor, f)
        
        print("✓ Models saved successfully")
    
    def load_models(self, model_dir: str = './') -> None:
        """Load previously trained models."""
        try:
            self.xgb_model = xgb.XGBRegressor()
            self.xgb_model.load_model(f'{model_dir}/xgboost_model.json')
            
            with open(f'{model_dir}/random_forest_model.pkl', 'rb') as f:
                self.rf_model = pickle.load(f)
            
            with open(f'{model_dir}/preprocessor.pkl', 'rb') as f:
                self.preprocessor = pickle.load(f)
                
            print("✓ Models loaded successfully")
        except FileNotFoundError as e:
            print(f"Error loading models: {e}")


def main():
    """Complete training pipeline."""
    print("=" * 60)
    print("Healthcare Recovery Forecasting - Training Pipeline")
    print("=" * 60)
    
    # Generate synthetic data
    print("\n1. Generating synthetic patient data...")
    df = generate_synthetic_data(n_samples=2000, random_state=42)
    print(f"✓ Generated {len(df)} patient records")
    
    # Initialize trainer
    trainer = RecoveryModelTrainer(random_state=42)
    
    # Prepare data
    print("\n2. Preprocessing and preparing data...")
    X_train, X_test, y_train, y_test, feature_names = trainer.prepare_data(df)
    print(f"✓ Training set: {X_train.shape}")
    print(f"✓ Test set: {X_test.shape}")
    
    # Train models
    print("\n3. Training models...")
    trainer.train_xgboost(X_train, y_train)
    trainer.train_random_forest(X_train, y_train)
    
    # Evaluate models
    print("\n4. Evaluating models...")
    metrics = trainer.evaluate_models(X_test, y_test, feature_names)
    
    # Feature importance
    print("\n5. Feature Importance (Top 10)")
    importance_df = trainer.get_feature_importance(feature_names)
    print(importance_df.groupby('model').head(10).to_string(index=False))
    
    # Save models
    print("\n6. Saving models...")
    trainer.save_models(output_dir='./')
    
    # Save test data for later evaluation
    test_data = pd.DataFrame(X_test, columns=feature_names)
    test_data['y_actual'] = y_test.values
    test_data['y_pred_xgb'] = metrics['xgboost']['predictions']
    test_data['y_pred_rf'] = metrics['random_forest']['predictions']
    test_data.to_csv('test_predictions.csv', index=False)
    
    print("\n" + "=" * 60)
    print("Training pipeline complete!")
    print("=" * 60)
    
    return trainer, X_train, X_test, y_train, y_test, feature_names


if __name__ == '__main__':
    trainer, X_train, X_test, y_train, y_test, feature_names = main()
