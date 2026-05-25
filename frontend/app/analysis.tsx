'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { RecoveryTimeline, FeatureImportance } from '@/components/Analysis'
import { PatientReportCard, PDFReportGeneratorButton } from '@/components/Reports'
import { GlassmorphicCard } from '@/components/ui'
import { useDataStore } from '@/lib/store'

export const AnalysisPage: React.FC = () => {
  const { predictions, selectedSeverity } = useDataStore()
  const chartRef = React.useRef<HTMLDivElement>(null)

  // Mock data - replace with real data from store
  const mockPatientTimeline = {
    patientName: 'John Doe',
    admissionDate: '2026-03-25',
    predictedDischargeDate: '2026-04-05',
    events: [
      { date: '2026-03-25', event: 'Admission & Initial Assessment', status: 'completed' as const },
      { date: '2026-03-26', event: 'Lab Work & Imaging', status: 'completed' as const },
      { date: '2026-03-27', event: 'Treatment Initiated', status: 'completed' as const },
      { date: '2026-03-30', event: 'Clinical Improvement', status: 'ongoing' as const },
      { date: '2026-04-02', event: 'ICU Discharge Planned', status: 'planned' as const },
      { date: '2026-04-05', event: 'Expected Hospital Discharge', status: 'planned' as const },
    ],
  }

  const mockFeaturImportance = [
    { name: 'Age', importance: 0.28, impact: 'positive' as const },
    { name: 'Severity Level', importance: 0.24, impact: 'positive' as const },
    { name: 'Comorbidities', importance: 0.18, impact: 'positive' as const },
    { name: 'Vital Signs', importance: 0.15, impact: 'negative' as const },
    { name: 'Treatment Response', importance: 0.12, impact: 'negative' as const },
    { name: 'Lab Values', importance: 0.03, impact: 'negative' as const },
  ]

  const mockPatients = [
    {
      patientId: 'P001',
      name: 'John Doe',
      severity: 3,
      predictedLOS: 7,
      confidence: 92,
      dischargeDate: '2026-04-05',
      factors: ['Age 65+', 'Comorbidity: HTN', 'Abnormal vitals'],
    },
    {
      patientId: 'P002',
      name: 'Jane Smith',
      severity: 2,
      predictedLOS: 4,
      confidence: 88,
      dischargeDate: '2026-04-02',
      factors: ['Good baseline', 'Early intervention', 'Stable vitals'],
    },
    {
      patientId: 'P003',
      name: 'Robert Johnson',
      severity: 4,
      predictedLOS: 12,
      confidence: 85,
      dischargeDate: '2026-04-10',
      factors: ['Age 78', 'Multiple comorbidities', 'Critical status'],
    },
  ]

  const reportData = {
    hospitalName: 'Central Medical Center',
    reportDate: new Date().toISOString().split('T')[0],
    datasetStats: {
      totalPatients: predictions?.length || 150,
      avgLOS: 6.2,
      criticalCount: 24,
    },
    chartRef,
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Analysis Dashboard</h1>
        <p className="text-gray-400">
          Detailed patient-level predictions and recovery analysis
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          className="glass-card px-4 py-2 rounded-lg text-sm text-teal hover:bg-opacity-20 hover:bg-teal transition"
        >
          📊 All Severity Levels
        </motion.button>
        {[1, 2, 3, 4, 5].map((level) => (
          <motion.button
            key={level}
            whileHover={{ scale: 1.05 }}
            className={`glass-card px-4 py-2 rounded-lg text-sm transition ${
              selectedSeverity === level ? 'bg-teal bg-opacity-30 border-teal' : ''
            }`}
          >
            Level {level}
          </motion.button>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Timeline */}
        <GlassmorphicCard className="lg:col-span-2 p-6" delay={0.1}>
          <RecoveryTimeline {...mockPatientTimeline} />
        </GlassmorphicCard>

        {/* Feature Importance */}
        <GlassmorphicCard className="p-6" delay={0.2}>
          <FeatureImportance features={mockFeaturImportance} />
        </GlassmorphicCard>
      </div>

      {/* Report Export */}
      <GlassmorphicCard className="p-6" delay={0.3}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Generate Comprehensive Report</h3>
            <p className="text-gray-400 text-sm mt-1">
              Export analysis with charts and statistics (PDF optimized for printing)
            </p>
          </div>
          <PDFReportGeneratorButton data={reportData} />
        </div>
      </GlassmorphicCard>

      {/* Patient Cards */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Patient Predictions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockPatients.map((patient, idx) => (
            <motion.div
              key={patient.patientId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <PatientReportCard {...patient} />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Detailed Reference Chart Container (hidden, used for PDF) */}
      <div ref={chartRef} className="hidden">
        <div className="bg-white p-8 space-y-6">
          <h3 className="text-2xl font-bold text-navy">Recovery Analysis Summary</h3>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Total Patients', value: '150' },
              { label: 'Avg LOS (days)', value: '6.2' },
              { label: 'Critical Cases', value: '24' },
              { label: 'Avg Recovery', value: '7.1' },
            ].map((stat) => (
              <div key={stat.label} className="p-4 bg-gray-100 rounded">
                <p className="text-gray-600 text-sm">{stat.label}</p>
                <p className="text-3xl font-bold text-navy">{stat.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalysisPage
