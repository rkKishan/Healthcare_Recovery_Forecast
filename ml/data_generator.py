"""
Generate synthetic healthcare data for training recovery prediction models.
Includes realistic distributions reflecting medical patterns.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple


def generate_synthetic_data(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic patient data with realistic patterns for recovery time prediction.
    
    Args:
        n_samples: Number of patient records to generate
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with patient data and actual LOS (Length of Stay)
    """
    np.random.seed(random_state)
    
    data = {
        # Demographics
        'age': np.random.normal(55, 18, n_samples).clip(18, 95).astype(int),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'bmi': np.random.normal(27, 5, n_samples).clip(15, 50),
        
        # Clinical indicators at admission
        'bp_systolic': np.random.normal(130, 15, n_samples).clip(80, 200),
        'bp_diastolic': np.random.normal(80, 10, n_samples).clip(50, 120),
        'heart_rate': np.random.normal(75, 12, n_samples).clip(40, 140),
        'temperature': np.random.normal(37.2, 0.8, n_samples).clip(35, 40),
        'respiratory_rate': np.random.normal(16, 3, n_samples).clip(8, 35),
        
        # Blood markers
        'white_blood_cells': np.random.lognormal(3.9, 0.6, n_samples),  # Log-normal distribution
        'hemoglobin': np.random.normal(13, 1.5, n_samples).clip(7, 20),
        'glucose': np.random.normal(120, 40, n_samples).clip(60, 400),
        'creatinine': np.random.lognormal(-0.5, 0.9, n_samples),
        'platelets': np.random.normal(250, 50, n_samples).clip(50, 500),
        
        # Comorbidities (binary flags)
        'has_diabetes': np.random.binomial(1, 0.25, n_samples),
        'has_hypertension': np.random.binomial(1, 0.3, n_samples),
        'has_copd': np.random.binomial(1, 0.1, n_samples),
        'has_heart_disease': np.random.binomial(1, 0.15, n_samples),
        'has_kidney_disease': np.random.binomial(1, 0.08, n_samples),
        
        # Admission dates
        'admission_date': [datetime.now() - timedelta(days=int(x)) 
                          for x in np.random.uniform(0, 365, n_samples)],
    }
    
    df = pd.DataFrame(data)
    
    # Generate realistic LOS based on features (long-tail distribution)
    los = _calculate_realistic_los(df)
    df['los_actual'] = los
    df['discharge_date'] = df['admission_date'] + pd.to_timedelta(df['los_actual'], unit='D')
    
    # Add diagnosis severity level (1-5) based on clinical indicators
    df['severity_level'] = _calculate_severity_level(df)
    
    return df


def _calculate_realistic_los(df: pd.DataFrame) -> np.ndarray:
    """
    Calculate Length of Stay with realistic long-tail distribution.
    Most patients stay 2-5 days, some stay much longer.
    """
    base_los = np.ones(len(df)) * 3  # Base 3 days
    
    # Age factor: older patients stay longer
    age_factor = (df['age'] / 50 - 1.1) * 0.5
    age_factor = np.maximum(age_factor, 0)
    
    # Comorbidity factor: multiple conditions increase stay
    comorbidity_score = (df['has_diabetes'] + df['has_hypertension'] + 
                         df['has_copd'] + df['has_heart_disease'] + df['has_kidney_disease'])
    comorbidity_factor = comorbidity_score * 1.5
    
    # Clinical indicator factor: abnormal vitals increase stay
    bp_abnormality = np.abs(df['bp_systolic'] - 120) / 20 + np.abs(df['bp_diastolic'] - 80) / 10
    bp_abnormality = np.minimum(bp_abnormality, 2) / 2
    heart_rate_abnormality = np.abs(df['heart_rate'] - 75) / 20
    
    clinical_factor = (bp_abnormality + heart_rate_abnormality) * 2
    
    # WBC abnormality: infection indicator
    wbc_abnormality = np.abs(np.log(df['white_blood_cells']) - np.log(5)) * 2
    wbc_abnormality = np.minimum(wbc_abnormality, 2)
    
    # Glucose factor: high glucose increases stay
    glucose_factor = np.maximum(df['glucose'] - 100, 0) / 100 * 0.5
    
    # Combine factors with some randomness (long-tail)
    los = (base_los + age_factor + comorbidity_factor + clinical_factor + 
           wbc_abnormality + glucose_factor)
    
    # Add long-tail: 5% of patients stay much longer
    long_stay_mask = np.random.random(len(df)) < 0.05
    los[long_stay_mask] *= np.random.uniform(3, 8, np.sum(long_stay_mask))
    
    # Add random noise
    los += np.random.normal(0, 0.5, len(df))
    
    return np.maximum(los, 1).astype(int)


def _calculate_severity_level(df: pd.DataFrame) -> np.ndarray:
    """
    Calculate diagnostic severity level (1-5) based on clinical indicators.
    Uses a decision tree-like logic.
    """
    severity = np.ones(len(df), dtype=int)
    
    # Level 5 (Critical): Multiple severe indicators
    critical_mask = (
        ((df['heart_rate'] > 120) | (df['heart_rate'] < 50)) &
        ((df['bp_systolic'] > 180) | (df['bp_systolic'] < 90)) &
        (df['white_blood_cells'] > 15)
    )
    severity[critical_mask] = 5
    
    # Level 4 (High): Major conditions or multiple moderate ones
    high_mask = (
        ~critical_mask & (
            (df['has_heart_disease'] & df['has_kidney_disease']) |
            (df['has_copd'] & (df['respiratory_rate'] > 25)) |
            ((df['white_blood_cells'] > 12) & (df['temperature'] > 38.5)) |
            (df['creatinine'] > 2)
        )
    )
    severity[high_mask] = 4
    
    # Level 3 (Medium): Moderate conditions
    medium_mask = (
        ~critical_mask & ~high_mask & (
            (df['has_diabetes'] & (df['glucose'] > 250)) |
            (df['has_hypertension'] & (df['bp_systolic'] > 160)) |
            ((df['white_blood_cells'] > 10) | (df['white_blood_cells'] < 4)) |
            (df['hemoglobin'] < 9)
        )
    )
    severity[medium_mask] = 3
    
    # Level 2 (Low): Minor conditions
    low_mask = (
        ~critical_mask & ~high_mask & ~medium_mask & (
            (df['has_diabetes']) | (df['has_hypertension']) |
            (df['temperature'] > 38) | (df['white_blood_cells'] > 8)
        )
    )
    severity[low_mask] = 2
    
    # Level 1 (Very Low): Routine, largely default
    
    return severity


if __name__ == '__main__':
    # Generate and save sample data
    df = generate_synthetic_data(n_samples=2000)
    df.to_csv('patient_data.csv', index=False)
    print(f"Generated {len(df)} patient records")
    print(f"\nSeverity distribution:\n{df['severity_level'].value_counts().sort_index()}")
    print(f"\nLOS statistics:\n{df['los_actual'].describe()}")
