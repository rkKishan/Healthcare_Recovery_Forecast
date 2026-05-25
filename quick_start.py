#!/usr/bin/env python3
"""
Quick Start Guide - Healthcare Recovery Forecasting System

This script provides a minimal working example to get started quickly.
Run this to understand the full system in ~5 minutes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from ml.data_generator import generate_synthetic_data
from ml.train import RecoveryModelTrainer
from ml.predictor import RecoveryPredictor
from datetime import datetime, timedelta
import pandas as pd

def main():
    print("\n" + "="*80)
    print("HEALTHCARE RECOVERY FORECASTING - QUICK START GUIDE".center(80))
    print("="*80 + "\n")
    
    # Step 1: Generate data
    print("Step 1: Generating synthetic patient data...")
    df = generate_synthetic_data(n_samples=500, random_state=42)
    print(f"   ✓ Generated {len(df)} patient records")
    print(f"   - Mean LOS: {df['los_actual'].mean():.1f} days")
    print(f"   - Severity distribution: L1:{(df['severity_level']==1).sum()}, ", end="")
    print(f"L5:{(df['severity_level']==5).sum()}\n")
    
    # Step 2: Train models
    print("Step 2: Training machine learning models...")
    trainer = RecoveryModelTrainer(random_state=42)
    X_train, X_test, y_train, y_test, feature_names = trainer.prepare_data(df)
    
    trainer.train_xgboost(X_train, y_train)
    trainer.train_random_forest(X_train, y_train)
    
    metrics = trainer.evaluate_models(X_test, y_test, feature_names)
    print(f"   ✓ Models trained and evaluated")
    print(f"   - XGBoost Median AE: {metrics['xgboost']['median_ae']:.3f} days")
    print(f"   - Random Forest Median AE: {metrics['random_forest']['median_ae']:.3f} days\n")
    
    # Step 3: Save models
    print("Step 3: Saving trained models...")
    trainer.save_models(output_dir='./ml')
    print("   ✓ Models saved to ./ml/\n")
    
    # Step 4: Make predictions
    print("Step 4: Making predictions for new patient...")
    predictor = RecoveryPredictor(model_path='./ml/', preprocessor_path='./ml/')
    
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
    }
    
    prediction = predictor.predict_single_patient(sample_patient)
    print(f"   ✓ Prediction generated")
    print(f"   - Expected LOS: {prediction['predicted_los_rounded']} days")
    print(f"   - 90% CI: {prediction['confidence_interval_lower_rounded']}-{prediction['confidence_interval_upper_rounded']} days")
    print(f"   - Severity: Level {prediction['severity_level']}")
    print(f"   - Est. Discharge: {prediction['estimated_discharge_date'].strftime('%Y-%m-%d')}\n")
    
    # Step 5: Batch predictions
    print("Step 5: Batch predictions for multiple patients...")
    df_batch = generate_synthetic_data(n_samples=50)
    batch_preds = predictor.predict_batch(df_batch)
    print(f"   ✓ Processed {len(batch_preds)} patients")
    print(f"   - Mean predicted LOS: {batch_preds['predicted_los'].mean():.1f} days")
    print(f"   - Median predicted LOS: {batch_preds['predicted_los'].median():.1f} days\n")
    
    # Step 6: Bed availability
    print("Step 6: Calculating bed availability forecast...")
    availability = predictor.calculate_bed_availability(
        df_batch, 
        total_beds=100,
        forecast_days=14
    )
    print(f"   ✓ 14-day forecast generated")
    print(f"   - Today's occupancy: {availability.iloc[0]['occupied_beds']}/100 beds")
    print(f"   - Peak occupancy: {availability['occupied_beds'].max()}/100 beds")
    print(f"   - Days with <10 available: {(availability['available_beds'] < 10).sum()}\n")
    
    # Step 7: Patient report
    print("Step 7: Generating patient report...")
    report = predictor.generate_patient_report(sample_patient)
    print("   ✓ Patient report generated (sample below):\n")
    lines = report.split('\n')
    for line in lines[5:20]:  # Show excerpt
        print("   " + line)
    print("   ...\n")
    
    # Summary
    print("="*80)
    print("✅ QUICK START COMPLETE - ALL SYSTEMS OPERATIONAL".center(80))
    print("="*80)
    print("\nNext Steps:")
    print("  1. Run full Jupyter notebook for comprehensive analysis:")
    print("     → jupyter notebook Healthcare_Recovery_Forecasting_Complete_Pipeline.ipynb")
    print("\n  2. Launch interactive dashboard:")
    print("     → streamlit run app/app.py")
    print("\n  3. Train with your own data:")
    print("     → Modify data_generator.py to load real patient data")
    print("     → Run: python -m ml.train")
    print("\n  4. Integrate into production:")
    print("     → Use ml.predictor.RecoveryPredictor class in your application")
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
