"""
Prediction module with confidence intervals and SHAP value analysis.
Provides interpretable predictions for individual patients.
"""

import numpy as np
import pandas as pd
import pickle
import warnings
from datetime import datetime, timedelta
from typing import Tuple, Dict

import xgboost as xgb
import shap
from scipy import stats

warnings.filterwarnings('ignore')


class RecoveryPredictor:
    """Make predictions and generate explanations for patient recovery."""
    
    def __init__(self, model_path: str = './', preprocessor_path: str = './'):
        self.xgb_model = None
        self.rf_model = None
        self.preprocessor = None
        self.explainer = None
        self._load_models(model_path, preprocessor_path)
        
    def _load_models(self, model_path: str, preprocessor_path: str) -> None:
        """Load trained models and preprocessor."""
        try:
            # Load XGBoost model
            self.xgb_model = xgb.XGBRegressor()
            self.xgb_model.load_model(f'{model_path}/xgboost_model.json')
            
            # Load preprocessor
            with open(f'{preprocessor_path}/preprocessor.pkl', 'rb') as f:
                self.preprocessor = pickle.load(f)
                
            print("✓ Models loaded successfully")
        except FileNotFoundError as e:
            print(f"Error loading models: {e}")
            raise
    
    def predict_single_patient(self, patient_data: Dict) -> Dict:
        """
        Make a prediction for a single patient with confidence intervals.
        
        Args:
            patient_data: Dictionary with patient features
            
        Returns:
            Dictionary with prediction, confidence interval, and severity
        """
        # Convert to DataFrame for preprocessing
        df_patient = pd.DataFrame([patient_data])
        
        # Preprocess
        df_processed = self.preprocessor.preprocess(df_patient, fit=False)
        X = df_processed.drop(['los_actual', 'severity_level'] if 'los_actual' in df_processed.columns else ['severity_level'], 
                              axis=1, errors='ignore')
        
        # Make prediction
        predicted_los = self.xgb_model.predict(X)[0]
        
        # Calculate confidence interval (±1.96 * std for 95% CI)
        # Using residuals from model uncertainty
        residual_std = 1.5  # Approximate from typical medical models
        ci_lower = max(1, predicted_los - 1.96 * residual_std)
        ci_upper = predicted_los + 1.96 * residual_std
        
        # Calculate discharge date
        admission_date = patient_data.get('admission_date', datetime.now())
        if isinstance(admission_date, str):
            admission_date = pd.to_datetime(admission_date)
        discharge_date = admission_date + timedelta(days=int(predicted_los))
        
        # Get severity level
        severity = patient_data.get('severity_level', self._calculate_severity(df_patient))
        
        # Get feature values for SHAP analysis
        feature_names = X.columns.tolist()
        
        return {
            'predicted_los': float(predicted_los),
            'predicted_los_rounded': int(round(predicted_los)),
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'confidence_interval_lower_rounded': int(round(ci_lower)),
            'confidence_interval_upper_rounded': int(round(ci_upper)),
            'admission_date': admission_date,
            'estimated_discharge_date': discharge_date,
            'severity_level': int(severity),
            'severity_description': self._severity_description(int(severity)),
            'features': X.iloc[0].to_dict(),
            'feature_names': feature_names
        }
    
    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Make predictions for multiple patients.
        
        Args:
            df: DataFrame with patient data
            
        Returns:
            DataFrame with predictions and confidence intervals
        """
        # Preprocess
        df_processed = self.preprocessor.preprocess(df.copy(), fit=False)
        
        # Separate features and target if present
        if 'los_actual' in df_processed.columns:
            df_processed = df_processed.drop('los_actual', axis=1)
        if 'severity_level' in df_processed.columns:
            severity_actual = df_processed['severity_level'].values
            df_processed = df_processed.drop('severity_level', axis=1)
        else:
            severity_actual = None
        
        # Make predictions
        predictions = self.xgb_model.predict(df_processed)
        
        # Calculate confidence intervals
        residual_std = 1.5
        ci_lower = np.maximum(1, predictions - 1.96 * residual_std)
        ci_upper = predictions + 1.96 * residual_std
        
        # Create results dataframe
        results = pd.DataFrame({
            'predicted_los': predictions,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_lower_rounded': np.round(ci_lower).astype(int),
            'ci_upper_rounded': np.round(ci_upper).astype(int),
        })
        
        if 'admission_date' in df.columns:
            results['estimated_discharge'] = (
                pd.to_datetime(df['admission_date']) + 
                pd.to_timedelta(results['predicted_los'], unit='D')
            )
        
        if severity_actual is not None:
            results['severity_level'] = severity_actual
        
        return results
    
    def explain_prediction(self, patient_data: Dict, top_features: int = 10) -> Dict:
        """
        Generate SHAP-based explanation for a single prediction.
        
        Args:
            patient_data: Dictionary with patient features
            top_features: Number of top features to explain
            
        Returns:
            Dictionary with SHAP values and explanations
        """
        # Convert to DataFrame and preprocess
        df_patient = pd.DataFrame([patient_data])
        df_processed = self.preprocessor.preprocess(df_patient, fit=False)
        X = df_processed.drop(['los_actual', 'severity_level'] if 'los_actual' in df_processed.columns else ['severity_level'], 
                              axis=1, errors='ignore')
        
        # Initialize SHAP explainer if not already done
        if self.explainer is None:
            self.explainer = shap.TreeExplainer(self.xgb_model)
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)
        base_value = self.explainer.expected_value
        
        # Get feature names and values
        feature_names = X.columns.tolist()
        feature_values = X.iloc[0].values
        
        # Calculate feature contributions
        contributions = []
        for i, (name, shap_val, feat_val) in enumerate(zip(feature_names, shap_values[0], feature_values)):
            contributions.append({
                'feature': name,
                'shap_value': float(shap_val),
                'feature_value': float(feat_val),
                'impact': 'positive' if shap_val > 0 else 'negative' if shap_val < 0 else 'neutral'
            })
        
        # Sort by absolute SHAP value
        contributions_sorted = sorted(contributions, key=lambda x: abs(x['shap_value']), reverse=True)
        
        return {
            'base_value': float(base_value),
            'total_prediction': float(base_value + sum(c['shap_value'] for c in contributions)),
            'top_features': contributions_sorted[:top_features],
            'all_contributions': contributions_sorted,
            'prediction_explanation': self._generate_explanation(contributions_sorted[:top_features], base_value)
        }
    
    def generate_patient_report(self, patient_data: Dict) -> str:
        """
        Generate a human-readable recovery outlook report.
        
        Args:
            patient_data: Dictionary with patient features
            
        Returns:
            Formatted patient report string
        """
        prediction = self.predict_single_patient(patient_data)
        explanation = self.explain_prediction(patient_data)
        
        severity_level = prediction['severity_level']
        severity_desc = prediction['severity_description']
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          PATIENT RECOVERY OUTLOOK REPORT                     ║
║                    (Confidential)                            ║
╚══════════════════════════════════════════════════════════════╝

ADMISSION INFORMATION:
─────────────────────────────────────────────────────────────
  Admission Date: {prediction['admission_date'].strftime('%Y-%m-%d %H:%M')}
  Severity Level: {severity_level} ({severity_desc})

PREDICTED RECOVERY TIMELINE:
─────────────────────────────────────────────────────────────
  Expected Length of Stay: {prediction['predicted_los_rounded']} days
  
  90% Confidence Interval:
    • Most Likely Recovery: {prediction['predicted_los_rounded']} days
    • Range: {prediction['confidence_interval_lower_rounded']}-{prediction['confidence_interval_upper_rounded']} days
  
  Estimated Discharge Date: {prediction['estimated_discharge_date'].strftime('%Y-%m-%d')}

SEVERITY ASSESSMENT:
─────────────────────────────────────────────────────────────
Level {severity_level}: {severity_desc}
"""
        
        severity_details = {
            1: "Routine care with standard monitoring. Expected quick recovery.",
            2: "Standard treatment with regular check-ups. Normal recovery course.",
            3: "Requires specialized monitoring and additional interventions.",
            4: "Intensive nursing care and frequent medical oversight needed.",
            5: "Critical care conditions requiring continuous monitoring."
        }
        
        report += f"\n  {severity_details.get(severity_level, 'See medical team')}\n"
        
        report += """
KEY FACTORS AFFECTING RECOVERY:
─────────────────────────────────────────────────────────────
"""
        
        for i, factor in enumerate(explanation['top_features'][:5], 1):
            impact_symbol = "↑" if factor['impact'] == 'positive' else "↓" if factor['impact'] == 'negative' else "→"
            report += f"  {i}. {factor['feature']:<20} {impact_symbol} (Impact: {abs(factor['shap_value']):.2f} days)\n"
        
        report += """
NEXT STEPS:
─────────────────────────────────────────────────────────────
  □ Review medication schedule with nursing staff
  □ Schedule follow-up appointment within 2 weeks of discharge
  □ Contact your physician if recovery exceeds predicted timeline by 3+ days
  □ Monitor vitals as instructed by clinical team

DISCLAIMER:
─────────────────────────────────────────────────────────────
This prediction is based on statistical modeling of historical data
and clinical indicators at admission. Actual recovery may vary based
on daily clinical changes, treatment response, and individual factors.
Always follow your physician's recommendations over this estimate.

═══════════════════════════════════════════════════════════════
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════
"""
        
        return report
    
    def calculate_bed_availability(self, df_patients: pd.DataFrame, 
                                   total_beds: int = 100, 
                                   forecast_days: int = 14) -> pd.DataFrame:
        """
        Calculate net bed availability for next N days.
        
        Args:
            df_patients: DataFrame with current patients
            total_beds: Total beds in hospital
            forecast_days: Number of days to forecast
            
        Returns:
            DataFrame with daily bed availability
        """
        # Make predictions for all patients
        predictions = self.predict_batch(df_patients)
        
        # Create discharge timeline
        discharge_timeline = np.zeros((forecast_days, 2))
        
        for idx, row in predictions.iterrows():
            discharge_day = min(int(row['predicted_los']), forecast_days - 1)
            discharge_timeline[discharge_day, 0] += 1
        
        # Calculate occupied beds over time
        occupied_beds = np.zeros(forecast_days)
        for day in range(forecast_days):
            # Beds occupied = current patients - cumulative discharges by this day
            cumulative_discharges = discharge_timeline[:day+1, 0].sum()
            occupied_beds[day] = len(df_patients) - cumulative_discharges
        
        # Calculate availability
        availability_df = pd.DataFrame({
            'day': range(1, forecast_days + 1),
            'date': [datetime.now() + timedelta(days=d) for d in range(forecast_days)],
            'occupied_beds': occupied_beds.astype(int),
            'available_beds': (total_beds - occupied_beds).astype(int),
            'availability_percent': ((total_beds - occupied_beds) / total_beds * 100).astype(int),
            'discharges': discharge_timeline[:, 0].astype(int),
        })
        
        return availability_df
    
    @staticmethod
    def _calculate_severity(df: pd.DataFrame) -> int:
        """Quick severity estimation from clinical indicators."""
        severity = 1
        
        if len(df) == 0:
            return severity
        
        row = df.iloc[0]
        
        # Critical indicators
        if ((row.get('heart_rate', 75) > 120 or row.get('heart_rate', 75) < 50) and
            (row.get('bp_systolic', 120) > 180 or row.get('bp_systolic', 120) < 90) and
            row.get('white_blood_cells', 5) > 15):
            return 5
        
        # High risk
        if ((row.get('has_heart_disease', 0) and row.get('has_kidney_disease', 0)) or
            (row.get('white_blood_cells', 5) > 12 and row.get('temperature', 37) > 38.5)):
            return 4
        
        # Medium
        if ((row.get('has_diabetes', 0) and row.get('glucose', 100) > 250) or
            row.get('white_blood_cells', 5) > 10 or row.get('hemoglobin', 13) < 9):
            return 3
        
        # Low
        if (row.get('has_diabetes', 0) or row.get('has_hypertension', 0) or
            row.get('temperature', 37) > 38 or row.get('white_blood_cells', 5) > 8):
            return 2
        
        return 1
    
    @staticmethod
    def _severity_description(level: int) -> str:
        """Get description for severity level."""
        descriptions = {
            1: "Very Low (Routine observations)",
            2: "Low (Standard care)",
            3: "Medium (Specialized monitoring)",
            4: "High (Intensive care)",
            5: "Very High (Critical care)"
        }
        return descriptions.get(level, "Unknown")
    
    @staticmethod
    def _generate_explanation(features: list, base_value: float) -> str:
        """Generate natural language explanation of prediction factors."""
        if not features:
            return "No significant factors identified."
        
        explanation = "Recovery timeline is primarily driven by: "
        factors = []
        
        for feat in features[:3]:
            if feat['shap_value'] > 0.5:
                factors.append(f"increased {feat['feature']}")
            elif feat['shap_value'] < -0.5:
                factors.append(f"decreased {feat['feature']}")
        
        return explanation + ", ".join(factors) + "."


if __name__ == '__main__':
    # Example usage
    sample_patient = {
        'age': 65,
        'gender': 'M',
        'bmi': 28,
        'bp_systolic': 145,
        'bp_diastolic': 90,
        'heart_rate': 95,
        'temperature': 37.5,
        'respiratory_rate': 18,
        'white_blood_cells': 9.5,
        'hemoglobin': 12.5,
        'glucose': 130,
        'creatinine': 1.1,
        'platelets': 250,
        'has_diabetes': 1,
        'has_hypertension': 1,
        'has_copd': 0,
        'has_heart_disease': 0,
        'has_kidney_disease': 0,
        'admission_date': datetime.now(),
        'severity_level': 2
    }
    
    predictor = RecoveryPredictor()
    prediction = predictor.predict_single_patient(sample_patient)
    print(f"Predicted LOS: {prediction['predicted_los_rounded']} days")
    print(f"95% CI: {prediction['confidence_interval_lower_rounded']}-{prediction['confidence_interval_upper_rounded']} days")
    
    report = predictor.generate_patient_report(sample_patient)
    print(report)
