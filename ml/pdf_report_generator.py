"""
Comprehensive PDF Report Generator for Healthcare Recovery Forecasting
Uses ReportLab for layout and Matplotlib for charts
"""

import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Clinical Modernist Color Theme
NAVY = "#1A2B3C"
TEAL = "#20B2AA"
NAVY_RGB = (26, 43, 60)
TEAL_RGB = (32, 178, 170)


class PDFReportGenerator:
    """Generates comprehensive multi-page PDF reports with embedded charts"""
    
    def __init__(self, hospital_name="Central Medical Center"):
        self.hospital_name = hospital_name
        self.report_date = datetime.now().strftime("%B %d, %Y")
        self.style_sheet = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_styles(self):
        """Setup custom paragraph styles matching Clinical Modernist theme"""
        self.style_sheet.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.style_sheet['Heading1'],
            fontSize=28,
            textColor=colors.HexColor(NAVY),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.style_sheet.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.style_sheet['Heading2'],
            fontSize=16,
            textColor=colors.HexColor(TEAL),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        self.style_sheet.add(ParagraphStyle(
            name='CustomBody',
            parent=self.style_sheet['BodyText'],
            fontSize=10,
            textColor=colors.HexColor(NAVY),
            spaceAfter=6
        ))
    
    def _create_severity_chart(self):
        """Create severity distribution donut chart"""
        fig, ax = plt.subplots(figsize=(6, 6), facecolor='white')
        
        severity_levels = ['Level 1\n(Minimal)', 'Level 2\n(Mild)', 'Level 3\n(Moderate)', 
                          'Level 4\n(Severe)', 'Level 5\n(Critical)']
        severity_counts = [45, 120, 180, 95, 24]
        
        colors_list = ['#2ca02c', '#90ee90', '#ffd700', '#ff8c00', '#dc143c']
        
        wedges, texts, autotexts = ax.pie(
            severity_counts,
            labels=severity_levels,
            autopct='%1.1f%%',
            colors=colors_list,
            startangle=90,
            textprops={'fontsize': 9, 'weight': 'bold'}
        )
        
        # Create donut hole
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)
        
        # Add center text
        ax.text(0, 0, 'Total\n464', ha='center', va='center', 
               fontsize=14, weight='bold', color=NAVY)
        
        plt.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        img.seek(0)
        plt.close()
        return img
    
    def _create_bed_occupancy_chart(self):
        """Create 14-day bed occupancy forecast"""
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
        
        days = np.arange(1, 15)
        bed_gains = np.array([3, 5, 2, 6, 4, 2, 3, 5, 1, 4, 3, 2, 5, 2])
        bed_losses = np.array([2, 3, 4, 2, 3, 5, 2, 3, 4, 2, 3, 4, 2, 3])
        net_change = bed_gains - bed_losses
        
        colors_bars = [TEAL if x > 0 else NAVY for x in net_change]
        
        bars = ax.bar(days, net_change, color=colors_bars, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_xlabel('Day', fontsize=11, weight='bold', color=NAVY)
        ax.set_ylabel('Net Bed Change', fontsize=11, weight='bold', color=NAVY)
        ax.set_title('14-Day Bed Occupancy Forecast', fontsize=13, weight='bold', color=NAVY, pad=15)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_xticks(days)
        
        # Color the axis
        ax.spines['bottom'].set_color(NAVY)
        ax.spines['left'].set_color(NAVY)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        plt.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        img.seek(0)
        plt.close()
        return img
    
    def _create_los_distribution_chart(self):
        """Create length of stay distribution histogram"""
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
        
        # Generate realistic LOS data
        los_data = np.concatenate([
            np.random.normal(5, 1.5, 150),
            np.random.normal(10, 2, 95),
            np.random.normal(15, 3, 24)
        ])
        los_data = np.clip(los_data, 1, 30)
        
        median_los = np.median(los_data)
        
        n, bins, patches = ax.hist(los_data, bins=15, color=TEAL, alpha=0.7, 
                                    edgecolor=NAVY, linewidth=1.5)
        
        # Highlight median
        ax.axvline(median_los, color=NAVY, linestyle='--', linewidth=2.5, label=f'Median: {median_los:.1f} days')
        
        ax.set_xlabel('Days', fontsize=11, weight='bold', color=NAVY)
        ax.set_ylabel('Number of Patients', fontsize=11, weight='bold', color=NAVY)
        ax.set_title('Length of Stay Distribution', fontsize=13, weight='bold', color=NAVY, pad=15)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Color the axis
        ax.spines['bottom'].set_color(NAVY)
        ax.spines['left'].set_color(NAVY)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        plt.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        img.seek(0)
        plt.close()
        return img
    
    def _create_feature_importance_chart(self):
        """Create feature importance horizontal bar chart"""
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
        
        features = ['Age', 'Severity Level', 'Comorbidities', 'Vital Signs', 'Lab Results']
        importance = [0.28, 0.24, 0.18, 0.15, 0.12]
        
        bars = ax.barh(features, importance, color=[TEAL, TEAL, NAVY, NAVY, NAVY], 
                       alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, importance)):
            ax.text(val + 0.01, i, f'{val:.0%}', va='center', fontsize=10, weight='bold', color=NAVY)
        
        ax.set_xlabel('Relative Importance', fontsize=11, weight='bold', color=NAVY)
        ax.set_title('Top Feature Importance for Recovery Predictions', fontsize=13, weight='bold', color=NAVY, pad=15)
        ax.set_xlim(0, 0.35)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Color the axis
        ax.spines['bottom'].set_color(NAVY)
        ax.spines['left'].set_color(NAVY)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        plt.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        img.seek(0)
        plt.close()
        return img
    
    def _create_summary_stats_boxes(self):
        """Create summary statistics visualization"""
        stats = [
            {'label': 'Total Patients', 'value': '464', 'trend': '+12%'},
            {'label': 'Average LOS', 'value': '6.2 days', 'trend': '-2%'},
            {'label': 'Critical Cases', 'value': '24', 'trend': '+5%'},
            {'label': 'Bed Utilization', 'value': '78%', 'trend': '+3%'},
        ]
        
        # Create a figure with stat boxes
        fig, ax = plt.subplots(figsize=(8, 2.5), facecolor='white')
        ax.axis('off')
        
        box_width = 0.22
        box_height = 0.8
        
        for i, stat in enumerate(stats):
            x_pos = 0.05 + i * 0.24
            
            # Draw box
            rect = Rectangle((x_pos, 0.05), box_width, box_height, 
                            linewidth=2, edgecolor=NAVY, facecolor=TEAL, alpha=0.2)
            ax.add_patch(rect)
            
            # Add text
            ax.text(x_pos + box_width/2, 0.65, stat['value'], 
                   ha='center', va='center', fontsize=12, weight='bold', color=NAVY)
            ax.text(x_pos + box_width/2, 0.35, stat['label'], 
                   ha='center', va='center', fontsize=8, color=NAVY)
            ax.text(x_pos + box_width - 0.01, 0.75, stat['trend'], 
                   ha='right', va='top', fontsize=8, weight='bold', color=TEAL)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        img.seek(0)
        plt.close()
        return img
    
    def generate_report(self, output_path=None):
        """Generate complete multi-page PDF report"""
        if output_path is None:
            output_path = f"Recovery_Forecast_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.5*inch, 
                              leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # PAGE 1: Executive Summary
        story.extend(self._page_executive_summary())
        story.append(PageBreak())
        
        # PAGE 2: Hospital Resource Insights
        story.extend(self._page_bed_management())
        story.append(PageBreak())
        
        # PAGE 3: Recovery Analytics
        story.extend(self._page_recovery_analytics())
        story.append(PageBreak())
        
        # PAGE 4: Detailed Patient Data
        story.extend(self._page_patient_data())
        
        doc.build(story)
        return output_path
    
    def _page_executive_summary(self):
        """Build Page 1: Executive Summary"""
        elements = []
        
        # Header
        elements.append(Spacer(1, 0.3*inch))
        title = Paragraph("PredictMed Healthcare Recovery Forecast", self.style_sheet['CustomTitle'])
        elements.append(title)
        
        hospital_info = Paragraph(
            f"<b>{self.hospital_name}</b><br/>Report Date: {self.report_date}",
            ParagraphStyle(name='HospitalInfo', parent=self.style_sheet['Normal'], 
                         fontSize=11, textColor=colors.HexColor(TEAL), alignment=TA_LEFT)
        )
        elements.append(hospital_info)
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary Stats
        subtitle = Paragraph("Executive Summary & Vital Signs", self.style_sheet['CustomHeading'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.15*inch))
        
        # Add stats boxes image
        stats_img = self._create_summary_stats_boxes()
        img = Image(stats_img, width=6.5*inch, height=2*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Patient Severity Overview
        severity_subtitle = Paragraph("Patient Severity Distribution", self.style_sheet['CustomHeading'])
        elements.append(severity_subtitle)
        elements.append(Spacer(1, 0.15*inch))
        
        severity_img = self._create_severity_chart()
        img = Image(severity_img, width=4*inch, height=4*inch)
        elements.append(img)
        
        return elements
    
    def _page_bed_management(self):
        """Build Page 2: Hospital Resource Insights"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        title = Paragraph("Hospital Resource Insights", self.style_sheet['CustomHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.1*inch))
        
        subtitle = Paragraph(
            "14-Day Bed Occupancy Forecast & Predictions",
            ParagraphStyle(name='Subtitle2', parent=self.style_sheet['Normal'], fontSize=11)
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        # Bed occupancy chart
        bed_img = self._create_bed_occupancy_chart()
        img = Image(bed_img, width=6.5*inch, height=4*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Beds Opening Soon Table
        table_title = Paragraph("<b>Beds Opening Soon (Next 14 Days)</b>", 
                               ParagraphStyle(name='TableTitle', parent=self.style_sheet['Normal'], fontSize=10))
        elements.append(table_title)
        elements.append(Spacer(1, 0.1*inch))
        
        bed_data = [
            ['Date', 'Ward', 'Beds Available', 'Expected Patients'],
            ['Mar 30, 2026', 'ICU', '3', '2'],
            ['Mar 31, 2026', 'General Ward', '5', '4'],
            ['Apr 2, 2026', 'Recovery Ward', '2', '1'],
            ['Apr 4, 2026', 'ICU', '6', '5'],
            ['Apr 6, 2026', 'General Ward', '4', '3'],
        ]
        
        bed_table = Table(bed_data, colWidths=[1.3*inch, 1.3*inch, 1.4*inch, 1.5*inch])
        bed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(TEAL)),
            ('ALPHA', (0, 1), (-1, -1), 0.15),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(NAVY)),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(TEAL)]),
        ]))
        elements.append(bed_table)
        
        return elements
    
    def _page_recovery_analytics(self):
        """Build Page 3: Recovery Analytics"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        title = Paragraph("Recovery Analytics", self.style_sheet['CustomHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Length of Stay Distribution
        los_title = Paragraph("<b>Length of Stay Distribution</b>", 
                             ParagraphStyle(name='LosTitle', parent=self.style_sheet['Normal'], fontSize=10))
        elements.append(los_title)
        elements.append(Spacer(1, 0.1*inch))
        
        los_img = self._create_los_distribution_chart()
        img = Image(los_img, width=6.5*inch, height=4*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Feature Importance
        features_title = Paragraph("<b>Key Factors Impacting Recovery</b>", 
                                  ParagraphStyle(name='FeaturesTitle', parent=self.style_sheet['Normal'], fontSize=10))
        elements.append(features_title)
        elements.append(Spacer(1, 0.1*inch))
        
        features_img = self._create_feature_importance_chart()
        img = Image(features_img, width=6.5*inch, height=4*inch)
        elements.append(img)
        
        return elements
    
    def _page_patient_data(self):
        """Build Page 4: Detailed Patient Data"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        title = Paragraph("Detailed Patient Data (First 20 Records)", self.style_sheet['CustomHeading'])
        elements.append(title)
        elements.append(Spacer(1, 0.15*inch))
        
        # Generate sample patient data
        patient_data = [['Patient ID', 'Severity Level', 'Predicted LOS (Days)', 'Estimated Discharge']]
        
        severity_labels = {1: 'Level 1', 2: 'Level 2', 3: 'Level 3', 4: 'Level 4', 5: 'Level 5'}
        base_date = datetime.now()
        
        for i in range(1, 21):
            severity = np.random.randint(1, 6)
            los = np.random.randint(2, 20)
            discharge_date = (base_date + timedelta(days=los)).strftime('%b %d, %Y')
            
            patient_data.append([
                f'P{i:03d}',
                severity_labels[severity],
                str(los),
                discharge_date
            ])
        
        patient_table = Table(patient_data, colWidths=[1.2*inch, 1.3*inch, 1.5*inch, 1.5*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(TEAL)),
            ('ALPHA', (0, 1), (-1, -1), 0.1),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(NAVY)),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(TEAL)]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(patient_table)
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            "<i>This report is generated by PredictMed Healthcare Recovery Forecast System. "
            "All predictions are based on historical data and clinical models.</i>",
            ParagraphStyle(name='Footer', parent=self.style_sheet['Normal'], 
                         fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        elements.append(footer)
        
        return elements


def generate_pdf_report(hospital_name="Central Medical Center", output_path=None):
    """Convenience function to generate PDF report"""
    generator = PDFReportGenerator(hospital_name=hospital_name)
    return generator.generate_report(output_path=output_path)
