"""
Visualization utilities for healthcare recovery forecasting dashboard.
Includes plots for predictions, feature importance, SHAP analysis, and bed availability.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Optional, Tuple

import shap

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class RecoveryVisualizer:
    """Create visualizations for recovery forecasting models."""
    
    @staticmethod
    def plot_length_of_stay_distribution(actual_los: np.ndarray, predicted_los: np.ndarray,
                                        title: str = "Length of Stay: Actual vs Predicted") -> plt.Figure:
        """
        Plot distribution comparison of actual vs predicted LOS.
        
        Args:
            actual_los: Array of actual lengths of stay
            predicted_los: Array of predicted lengths of stay
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram comparison
        axes[0].hist(actual_los, bins=30, alpha=0.6, label='Actual', color='blue', edgecolor='black')
        axes[0].hist(predicted_los, bins=30, alpha=0.6, label='Predicted', color='orange', edgecolor='black')
        axes[0].set_xlabel('Length of Stay (days)')
        axes[0].set_ylabel('Frequency')
        axes[0].set_title('Distribution Comparison')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Scatter plot with perfect prediction line
        axes[1].scatter(actual_los, predicted_los, alpha=0.5, s=30)
        max_los = max(actual_los.max(), predicted_los.max())
        axes[1].plot([0, max_los], [0, max_los], 'r--', lw=2, label='Perfect Prediction')
        axes[1].set_xlabel('Actual LOS (days)')
        axes[1].set_ylabel('Predicted LOS (days)')
        axes[1].set_title('Prediction Accuracy')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_residuals(actual_los: np.ndarray, predicted_los: np.ndarray,
                      title: str = "Prediction Residuals Analysis") -> plt.Figure:
        """
        Plot residual analysis for model evaluation.
        
        Args:
            actual_los: Array of actual lengths of stay
            predicted_los: Array of predicted lengths of stay
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        residuals = actual_los - predicted_los
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Residual histogram
        axes[0, 0].hist(residuals, bins=40, edgecolor='black', alpha=0.7, color='steelblue')
        axes[0, 0].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Error')
        axes[0, 0].set_xlabel('Residual (days)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Residual Distribution')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # Residuals vs predicted
        axes[0, 1].scatter(predicted_los, residuals, alpha=0.5, s=30)
        axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=2)
        axes[0, 1].set_xlabel('Predicted LOS (days)')
        axes[0, 1].set_ylabel('Residual (days)')
        axes[0, 1].set_title('Residuals vs Predicted Values')
        axes[0, 1].grid(alpha=0.3)
        
        # Q-Q plot for normality check
        from scipy import stats as sp_stats
        sp_stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot (Normality Check)')
        axes[1, 0].grid(alpha=0.3)
        
        # Absolute error distribution
        abs_error = np.abs(residuals)
        axes[1, 1].hist(abs_error, bins=40, edgecolor='black', alpha=0.7, color='coral')
        axes[1, 1].axvline(x=np.median(abs_error), color='red', linestyle='--', 
                           linewidth=2, label=f'Median: {np.median(abs_error):.2f} days')
        axes[1, 1].set_xlabel('Absolute Error (days)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Absolute Error Distribution')
        axes[1, 1].legend()
        axes[1, 1].grid(alpha=0.3)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_feature_importance(importance_df: pd.DataFrame, top_n: int = 15,
                               title: str = "Top Features by Importance") -> plt.Figure:
        """
        Plot feature importance comparison.
        
        Args:
            importance_df: DataFrame with features and importance scores
            top_n: Number of top features to display
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        models = importance_df['model'].unique()
        
        for idx, model in enumerate(models):
            model_data = importance_df[importance_df['model'] == model].head(top_n)
            model_data = model_data.sort_values('importance')
            
            axes[idx].barh(model_data['feature'], model_data['importance'], 
                          color='steelblue', edgecolor='black')
            axes[idx].set_xlabel('Importance Score')
            axes[idx].set_title(f'{model}')
            axes[idx].grid(axis='x', alpha=0.3)
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_bed_availability(availability_df: pd.DataFrame,
                             title: str = "Predicted Bed Availability (14 Days)") -> plt.Figure:
        """
        Plot bed availability forecast.
        
        Args:
            availability_df: DataFrame with bed availability predictions
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        
        # Occupied vs available beds
        x = availability_df['day']
        axes[0].fill_between(x, 0, availability_df['occupied_beds'], 
                            alpha=0.6, label='Occupied Beds', color='coral')
        axes[0].fill_between(x, availability_df['occupied_beds'], 
                            availability_df['occupied_beds'] + availability_df['available_beds'],
                            alpha=0.6, label='Available Beds', color='lightgreen')
        axes[0].set_xlabel('Days')
        axes[0].set_ylabel('Number of Beds')
        axes[0].set_title('Bed Occupancy Forecast')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Availability percentage
        colors = ['green' if pct >= 30 else 'orange' if pct >= 15 else 'red' 
                 for pct in availability_df['availability_percent']]
        axes[1].bar(x, availability_df['availability_percent'], color=colors, edgecolor='black', alpha=0.7)
        axes[1].axhline(y=30, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Good Availability')
        axes[1].axhline(y=15, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Moderate')
        axes[1].axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Critical')
        axes[1].set_xlabel('Days')
        axes[1].set_ylabel('Availability %')
        axes[1].set_title('Bed Availability Percentage')
        axes[1].set_ylim(0, 100)
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_severity_distribution(severity_levels: np.ndarray,
                                  title: str = "Patient Severity Distribution") -> plt.Figure:
        """
        Plot severity level distribution.
        
        Args:
            severity_levels: Array of severity levels (1-5)
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Count plot
        severity_counts = pd.Series(severity_levels).value_counts().sort_index()
        severity_names = {
            1: 'Very Low',
            2: 'Low',
            3: 'Medium',
            4: 'High',
            5: 'Very High'
        }
        
        colors_map = {1: 'green', 2: 'lightgreen', 3: 'yellow', 4: 'orange', 5: 'red'}
        colors = [colors_map.get(level, 'gray') for level in severity_counts.index]
        
        axes[0].bar([severity_names[level] for level in severity_counts.index],
                   severity_counts.values, color=colors, edgecolor='black', alpha=0.7)
        axes[0].set_ylabel('Number of Patients')
        axes[0].set_title('Severity Count')
        axes[0].grid(alpha=0.3, axis='y')
        
        # Pie chart
        axes[1].pie(severity_counts.values, 
                   labels=[severity_names[level] for level in severity_counts.index],
                   colors=colors, autopct='%1.1f%%', startangle=90)
        axes[1].set_title('Severity Distribution')
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_confidence_intervals(predictions_df: pd.DataFrame,
                                 title: str = "Predictions with Confidence Intervals") -> plt.Figure:
        """
        Plot predictions with 90% confidence intervals.
        
        Args:
            predictions_df: DataFrame with predicted_los, ci_lower, ci_upper
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        x = np.arange(len(predictions_df))
        
        # Plot point estimates
        ax.scatter(x, predictions_df['predicted_los'], color='steelblue', 
                  s=50, zorder=3, label='Point Estimate')
        
        # Plot confidence intervals
        errors = [
            predictions_df['predicted_los'] - predictions_df['ci_lower'],
            predictions_df['ci_upper'] - predictions_df['predicted_los']
        ]
        ax.errorbar(x, predictions_df['predicted_los'], yerr=errors,
                   fmt='none', ecolor='gray', capsize=5, alpha=0.6, label='90% CI')
        
        ax.set_xlabel('Patient ID')
        ax.set_ylabel('Length of Stay (days)')
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_model_comparison(metrics_dict: dict, title: str = "Model Performance Comparison") -> plt.Figure:
        """
        Compare performance metrics between models.
        
        Args:
            metrics_dict: Dictionary with model metrics from trainer
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        models = list(metrics_dict.keys())
        metrics_list = ['mae', 'median_ae', 'rmse', 'r2']
        metric_labels = ['MAE', 'Median AE', 'RMSE', 'R²']
        
        for idx, (metric, label) in enumerate(zip(metrics_list, metric_labels)):
            ax = axes[idx // 2, idx % 2]
            
            values = [metrics_dict[model].get(metric, 0) for model in models]
            
            bars = ax.bar(models, values, color=['steelblue', 'coral'], 
                         edgecolor='black', alpha=0.7)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom')
            
            ax.set_ylabel(label)
            ax.set_title(f'{label} Comparison')
            ax.grid(alpha=0.3, axis='y')
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_age_recovery_relationship(df: pd.DataFrame,
                                      title: str = "Age vs Recovery Time") -> plt.Figure:
        """
        Plot relationship between patient age and recovery time.
        
        Args:
            df: DataFrame with age and los_actual columns
            title: Plot title
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Scatter plot with trend
        ax.scatter(df['age'], df['los_actual'], alpha=0.5, s=40, color='steelblue', edgecolor='black')
        
        # Add trend line
        z = np.polyfit(df['age'], df['los_actual'], 2)
        p = np.poly1d(z)
        age_range = np.linspace(df['age'].min(), df['age'].max(), 100)
        ax.plot(age_range, p(age_range), "r-", linewidth=2, label='Trend')
        
        ax.set_xlabel('Age (years)')
        ax.set_ylabel('Length of Stay (days)')
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        return fig


if __name__ == '__main__':
    print("Visualization utilities module loaded successfully")
