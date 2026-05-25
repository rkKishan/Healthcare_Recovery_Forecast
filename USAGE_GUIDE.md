"""
USAGE GUIDE - Healthcare Recovery Forecasting System

This guide provides detailed examples for different use cases and workflows.
Copy-paste examples to get started immediately.
"""

# ============================================================================
# USE CASE 1: Individual Patient Prediction
# ============================================================================

"""
Scenario: A clinician needs to predict recovery time for a new admission
with chronic conditions.
"""

from ml.predictor import RecoveryPredictor
from datetime import datetime

# Load predictor (models must be trained first)
predictor = RecoveryPredictor(model_path='./ml/', preprocessor_path='./ml/')

# Create patient profile
patient_data = {
    'age': 72,
    'gender': 'F',
    'bmi': 31,
    'bp_systolic': 155,
    'bp_diastolic': 95,
    'heart_rate': 88,
    'temperature': 37.3,
    'respiratory_rate': 19,
    'white_blood_cells': 11.2,
    'hemoglobin': 11.8,
    'glucose': 185,
    'creatinine': 1.5,
    'platelets': 210,
    'has_diabetes': 1,
    'has_hypertension': 1,
    'has_copd': 1,
    'has_heart_disease': 0,
    'has_kidney_disease': 0,
    'admission_date': datetime.now(),
}

# Get prediction with confidence interval
prediction = predictor.predict_single_patient(patient_data)

print(f"Patient Recovery Prediction:")
print(f"  Expected LOS: {prediction['predicted_los_rounded']} days")
print(f"  90% Confidence Interval: {prediction['confidence_interval_lower_rounded']}-{prediction['confidence_interval_upper_rounded']} days")
print(f"  Estimated Discharge: {prediction['estimated_discharge_date'].strftime('%Y-%m-%d')}")
print(f"  Severity Level: {prediction['severity_level']} ({prediction['severity_description']})")

# Get explanation
explanation = predictor.explain_prediction(patient_data, top_features=5)
print(f"\nTop Factors Affecting Recovery:")
for i, factor in enumerate(explanation['top_features'], 1):
    impact = f"+{factor['shap_value']:.2f}" if factor['shap_value'] > 0 else f"{factor['shap_value']:.2f}"
    print(f"  {i}. {factor['feature']}: {impact} days")

# Generate full report
report = predictor.generate_patient_report(patient_data)
with open('patient_recovery_report.txt', 'w') as f:
    f.write(report)
print(f"\n✓ Report saved to patient_recovery_report.txt")


# ============================================================================
# USE CASE 2: Batch Analysis of Current Inpatients
# ============================================================================

"""
Scenario: Hospital administrator needs to analyze all current inpatients
and get a summary of expected discharges.
"""

import pandas as pd
from ml.data_generator import generate_synthetic_data

# Load current patient census (simulated here, use real data in practice)
current_patients = generate_synthetic_data(n_samples=75)

# Make batch predictions
batch_predictions = predictor.predict_batch(current_patients)
batch_predictions['patient_id'] = range(1, len(batch_predictions) + 1)

# Display summary statistics
print("\nBatch Analysis Results:")
print(f"  Total Patients: {len(batch_predictions)}")
print(f"  Mean Predicted LOS: {batch_predictions['predicted_los'].mean():.1f} days")
print(f"  Median Predicted LOS: {batch_predictions['predicted_los'].median():.1f} days")
print(f"  Std Dev: {batch_predictions['predicted_los'].std():.1f} days")
print(f"  Range: {batch_predictions['predicted_los'].min():.0f}-{batch_predictions['predicted_los'].max():.0f} days")

# Find high-risk patients (predicted long stays)
high_risk = batch_predictions[batch_predictions['predicted_los'] > batch_predictions['predicted_los'].quantile(0.75)]
print(f"\n  High-Risk Patients (longest expected stays): {len(high_risk)}")
print(high_risk[['patient_id', 'predicted_los', 'ci_lower', 'ci_upper']].head())

# Export results
batch_predictions.to_csv('batch_predictions.csv', index=False)
print(f"\n✓ Results exported to batch_predictions.csv")


# ============================================================================
# USE CASE 3: Bed Management & Hospital Capacity Planning
# ============================================================================

"""
Scenario: Bed Management Department needs to forecast bed availability
for the next 2 weeks and identify critical periods.
"""

import matplotlib.pyplot as plt

# Generate availability forecast
availability = predictor.calculate_bed_availability(
    df_patients=current_patients,
    total_beds=150,  # Adjust to your hospital
    forecast_days=14
)

print("\nBed Availability Forecast (Next 14 Days):")
print("="*70)
print(availability[['Day', 'date', 'occupied_beds', 'available_beds', 'availability_percent']].to_string(index=False))
print("="*70)

# Identify critical periods
critical = availability[availability['available_beds'] < 15]
if len(critical) > 0:
    print(f"\n⚠️ ALERT: Days with critically low bed availability (<15 beds):")
    print(f"   Days: {', '.join(map(str, critical['Day'].tolist()))}")
    print(f"   Recommended: Reduce non-urgent admissions or arrange transfers")
else:
    print(f"\n✓ No critical bed shortage identified in forecast period")

# Visualize
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(availability['Day'], availability['available_beds'], marker='o', linewidth=2)
ax.axhline(y=15, color='red', linestyle='--', label='Critical Level')
ax.axhline(y=30, color='orange', linestyle='--', label='Warning Level')
ax.fill_between(availability['Day'], 0, 15, alpha=0.2, color='red')
ax.set_xlabel('Days from Today')
ax.set_ylabel('Available Beds')
ax.set_title('Hospital Bed Availability Forecast')
ax.legend()
ax.grid(alpha=0.3)
plt.savefig('bed_forecast.png', dpi=300, bbox_inches='tight')
plt.show()

# Export for hospital systems
availability.to_csv('bed_availability_14day.csv', index=False)
print(f"\n✓ Forecast exported to bed_availability_14day.csv")


# ============================================================================
# USE CASE 4: Discharge Planning & Patient Communication
# ============================================================================

"""
Scenario: Discharge coordinator wants patient-friendly information
to communicate realistic recovery expectations.
"""

# Generate simplified patient report
patient_data_dc = {
    'age': 58,
    'gender': 'M',
    'bmi': 26,
    'bp_systolic': 125,
    'bp_diastolic': 78,
    'heart_rate': 72,
    'temperature': 37.0,
    'respiratory_rate': 16,
    'white_blood_cells': 7.2,
    'hemoglobin': 14.1,
    'glucose': 105,
    'creatinine': 0.9,
    'platelets': 245,
    'has_diabetes': 0,
    'has_hypertension': 0,
    'has_copd': 0,
    'has_heart_disease': 0,
    'has_kidney_disease': 0,
    'admission_date': datetime.now(),
}

prediction_dc = predictor.predict_single_patient(patient_data_dc)

# Create simple discharge summary
discharge_summary = f"""
RECOVERY OUTLOOK FOR YOUR STAY

Your Expected Stay: {prediction_dc['predicted_los_rounded']} days

Most Likely Scenario:
Our model predicts you will be ready for discharge in about {prediction_dc['predicted_los_rounded']} days.
However, recovery times vary. We expect you'll be home sometime between
{prediction_dc['estimated_discharge_date'].strftime('%B %d')} and {(prediction_dc['estimated_discharge_date'] + pd.Timedelta(days=prediction_dc['confidence_interval_upper_rounded']-prediction_dc['predicted_los_rounded'])).strftime('%B %d')}.

Your Health Status: {prediction_dc['severity_description'].upper()}

This means you are receiving {prediction_dc['severity_description'].lower()} monitoring.
Your recovery is expected to be {['routine', 'standard', 'moderate', 'intensive', 'critical'][prediction_dc['severity_level']-1]}.

What Affects Your Recovery:
- Your age and overall health
- Any chronic conditions you may have
- Your current vital signs and lab values
- How you respond to treatment

When to Call Your Doctor:
If your recovery takes significantly longer than expected (more than
{prediction_dc['confidence_interval_upper_rounded']+3} days), please contact us immediately.

Questions? Ask a member of the healthcare team.
"""

print(discharge_summary)

# Save for printing
with open('patient_discharge_summary.txt', 'w') as f:
    f.write(discharge_summary)
print("\n✓ Discharge summary saved to patient_discharge_summary.txt")


# ============================================================================
# USE CASE 5: Quality Improvement & Outcome Analysis
# ============================================================================

"""
Scenario: Quality team wants to identify patients with unexpectedly
long stays to investigate root causes.
"""

# Create comprehensive analysis
batch_preds = predictor.predict_batch(current_patients)

# Merge actual vs predicted (if available)
analysis_df = pd.DataFrame({
    'predicted_los': batch_preds['predicted_los'],
    'age': current_patients['age'].values,
    'comorbidity_count': current_patients['comorbidity_count'].values,
    'severity_level': current_patients['severity_level'].values,
})

# Calculate prediction error
analysis_df['actual_los'] = current_patients['los_actual'].values
analysis_df['prediction_error'] = analysis_df['actual_los'] - analysis_df['predicted_los']
analysis_df['absolute_error'] = abs(analysis_df['prediction_error'])

# Flag unexpected outliers
long_stays_vs_prediction = analysis_df[analysis_df['prediction_error'] > 5]
short_stays_vs_prediction = analysis_df[analysis_df['prediction_error'] < -3]

print("\nQuality Improvement Analysis:")
print(f"  Total Patients: {len(analysis_df)}")
print(f"  Mean Prediction Error: {analysis_df['prediction_error'].mean():.2f} days")
print(f"  Median Absolute Error: {analysis_df['absolute_error'].median():.2f} days")

if len(long_stays_vs_prediction) > 0:
    print(f"\n  ⚠️ Unexpectedly Long Stays ({len(long_stays_vs_prediction)} patients):")
    print(f"    These patients stayed >5 days longer than predicted")
    print(f"    Recommend: Review clinical notes for complications, infections, or delays")

if len(short_stays_vs_prediction) > 0:
    print(f"\n  ✓ Better Than Expected ({len(short_stays_vs_prediction)} patients):")
    print(f"    These patients were discharged earlier than predicted")
    print(f"    Recommend: Document best practices contributing to faster recovery")

# Export for deeper analysis
analysis_df.to_csv('quality_analysis_output.csv', index=False)
print(f"\n✓ Quality analysis exported to quality_analysis_output.csv")


# ============================================================================
# USE CASE 6: Model Monitoring & Retraining
# ============================================================================

"""
Scenario: ML team needs to monitor model performance over time
and decide when to retrain.
"""

# Calculate performance metrics
from sklearn.metrics import mean_absolute_error, median_absolute_error

mae = mean_absolute_error(analysis_df['actual_los'], analysis_df['predicted_los'])
median_ae = median_absolute_error(analysis_df['actual_los'], analysis_df['predicted_los'])

print("\nModel Performance Monitoring:")
print(f"  Mean Absolute Error: {mae:.3f} days")
print(f"  Median Absolute Error: {median_ae:.3f} days")

# Thresholds for retraining
RETRAINING_THRESHOLD = 1.5  # Median AE

if median_ae > RETRAINING_THRESHOLD:
    print(f"\n  ⚠️ Alert: Model performance degrading")
    print(f"     Current Median AE: {median_ae:.3f} days (threshold: {RETRAINING_THRESHOLD})")
    print(f"     Recommended: Retrain model with recent data")
else:
    print(f"\n  ✓ Model performance within acceptable range")

# Performance over time (if tracking historical data)
print(f"\n  Recommendations:")
print(f"    - Retrain monthly with new patient data")
print(f"    - Monitor for seasonal patterns in recovery")
print(f"    - Track prediction errors by severity level")
print(f"    - Validate with real outcomes once deployed")


# ============================================================================
# USE CASE 7: Integration with Electronic Health Record (EHR)
# ============================================================================

"""
Scenario: Integration where EHR system automatically generates
predictions for all current inpatients.
"""

# Simulated EHR data format
ehr_data = {
    'patient_mrn': ['MRN001', 'MRN002', 'MRN003'],
    'age': [45, 67, 52],
    'gender': ['M', 'F', 'M'],
    'admission_date': [datetime.now(), datetime.now(), datetime.now()],
    # ... other fields
}

# Function to extract features from EHR
def extract_features_from_ehr(ehr_row):
    """Convert EHR record to prediction-ready format"""
    return {
        'age': ehr_row['age'],
        'gender': ehr_row['gender'],
        'bmi': ehr_row.get('bmi', 27),  # Use default if missing
        'bp_systolic': ehr_row.get('bp_systolic', 130),
        'bp_diastolic': ehr_row.get('bp_diastolic', 80),
        # ... map all EHR fields to prediction features
        'admission_date': ehr_row['admission_date'],
    }

# Generate predictions for all current patients
ehr_df = pd.DataFrame(ehr_data)
ehr_df['prediction'] = ehr_df.apply(
    lambda row: predictor.predict_single_patient(extract_features_from_ehr(row))['predicted_los_rounded'],
    axis=1
)

# Send predictions back to EHR
print("\nEHR Integration Results:")
print(ehr_df[['patient_mrn', 'age', 'gender', 'prediction']])

# Alert if high-risk
high_risk_ehr = ehr_df[ehr_df['prediction'] > 10]
if len(high_risk_ehr) > 0:
    print(f"\n  Patients requiring close monitoring (predicted >10 days):")
    for _, patient in high_risk_ehr.iterrows():
        print(f"    - {patient['patient_mrn']}: {patient['prediction']} days")


# ============================================================================
# TROUBLESHOOTING & VALIDATION
# ============================================================================

"""
If you encounter issues, use these diagnostic checks:
"""

# Check 1: Verify models exist
import os
print("\nModel Verification:")
print(f"  XGBoost model exists: {os.path.exists('./ml/xgboost_model.json')}")
print(f"  Preprocessor exists: {os.path.exists('./ml/preprocessor.pkl')}")

# Check 2: Validate data format
print("\nData Format Validation:")
sample_input = {
    'age': 60,
    'gender': 'M',
    'bmi': 27,
    'bp_systolic': 130,
    'bp_diastolic': 80,
    'heart_rate': 75,
    'temperature': 37.2,
    'respiratory_rate': 16,
    'white_blood_cells': 5.5,
    'hemoglobin': 13,
    'glucose': 120,
    'creatinine': 1.0,
    'platelets': 250,
    'has_diabetes': 0,
    'has_hypertension': 0,
    'has_copd': 0,
    'has_heart_disease': 0,
    'has_kidney_disease': 0,
    'admission_date': datetime.now(),
}

try:
    pred = predictor.predict_single_patient(sample_input)
    print(f"  ✓ Sample prediction successful: {pred['predicted_los_rounded']} days")
except Exception as e:
    print(f"  ✗ Error: {str(e)}")

print("\n" + "="*70)
print("For more information, see README.md and run the Jupyter notebook")
print("="*70)
