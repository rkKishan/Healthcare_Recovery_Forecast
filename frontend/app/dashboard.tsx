'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/lib/store'
import { LoginPage } from '@/components/Auth'
import { BedGrid, SeverityDonut } from '@/components/Dashboard'
import { AnimatedBackground, GlassmorphicCard, Badge } from '@/components/ui'
import { UploadPage } from './upload'
import { AnalysisPage } from './analysis'

interface SidebarProps {
  isOpen: boolean
  patient?: any
  onClose?: () => void
}

const PatientDetailSidebar: React.FC<SidebarProps> = ({
  isOpen,
  patient,
  onClose,
}) => {
  return (
    <motion.div
      className="fixed right-0 top-0 h-screen w-80 glass-card border-l border-gray-600 p-6 overflow-y-auto z-40"
      animate={{ x: isOpen ? 0 : 400 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white">Patient Details</h3>
        <button
          onClick={onClose}
          className="text-2xl text-gray-400 hover:text-white transition"
        >
          ×
        </button>
      </div>

      {patient ? (
        <div className="space-y-6">
          <div>
            <p className="text-gray-400 text-xs mb-1">Name</p>
            <p className="text-lg font-semibold text-white">{patient.name}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="glass-card p-3">
              <p className="text-gray-400 text-xs mb-1">Age</p>
              <p className="text-lg font-bold text-teal">{patient.age}</p>
            </div>
            <div className="glass-card p-3">
              <p className="text-gray-400 text-xs mb-1">Severity</p>
              <Badge level={patient.severity} />
            </div>
          </div>

          <div>
            <p className="text-gray-400 text-xs mb-2">Predictive Summary</p>
            <div className="glass-card p-4 space-y-3">
              <div>
                <p className="text-gray-400 text-xs">Predicted LOS</p>
                <p className="text-2xl font-bold text-teal">{patient.predictedLOS}</p>
              </div>
              <div>
                <p className="text-gray-400 text-xs">90% Confidence Interval</p>
                <p className="text-sm text-gray-300">
                  {patient.confidenceLower} - {patient.confidenceUpper} days
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-xs">Expected Discharge</p>
                <p className="text-sm text-teal font-semibold">{patient.dischargeDate}</p>
              </div>
            </div>
          </div>

          <div>
            <p className="text-gray-400 text-xs mb-2">Key Factors</p>
            <div className="space-y-2">
              {patient.keyFactors?.map((factor: string, idx: number) => (
                <div key={idx} className="text-sm text-gray-300 flex items-center gap-2">
                  <span className="text-teal">•</span>
                  {factor}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <p className="text-gray-400 text-sm">Select a patient to view details</p>
      )}
    </motion.div>
  )
}

const DashboardPage: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<any>(null)

  const mockPatients = [
    {
      id: '001',
      name: 'John Doe',
      age: 65,
      severity: 3,
      ward: 'ICU',
      predictedLOS: 7,
      confidenceLower: 5,
      confidenceUpper: 9,
      dischargeDate: '2026-04-05',
      keyFactors: ['Age 65+', 'Comorbidity: HTN', 'Abnormal vitals'],
    },
    {
      id: '002',
      name: 'Jane Smith',
      age: 42,
      severity: 2,
      ward: 'General Ward',
      predictedLOS: 4,
      confidenceLower: 3,
      confidenceUpper: 5,
      dischargeDate: '2026-04-02',
      keyFactors: ['Good baseline health', 'Early intervention'],
    },
    {
      id: '003',
      name: 'Robert Johnson',
      age: 78,
      severity: 4,
      ward: 'ICU',
      predictedLOS: 12,
      confidenceLower: 10,
      confidenceUpper: 15,
      dischargeDate: '2026-04-10',
      keyFactors: ['Age 78', 'Multiple comorbidities', 'Critical condition'],
    },
  ]

  return (
    <div className="space-y-8">
      {/* Stats Header */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Admitted', value: '847', trend: '+12%' },
          { label: 'Avg. LOS', value: '6.2d', trend: '-2%' },
          { label: 'Critical Cases', value: '124', trend: '+5%' },
          { label: 'Bed Utilization', value: '78%', trend: '+3%' },
        ].map((stat, idx) => (
          <GlassmorphicCard key={idx} delay={idx * 0.1}>
            <div className="p-6 space-y-3">
              <p className="text-gray-400 text-sm">{stat.label}</p>
              <div className="flex items-end justify-between">
                <p className="text-3xl font-bold text-white">{stat.value}</p>
                <span className="text-green-400 text-sm">{stat.trend}</span>
              </div>
            </div>
          </GlassmorphicCard>
        ))}
      </div>

      {/* Main Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bed Grid */}
        <GlassmorphicCard className="lg:col-span-2 p-6" delay={0.3}>
          <BedGrid />
        </GlassmorphicCard>

        {/* Severity Distribution */}
        <GlassmorphicCard className="p-6" delay={0.4}>
          <h3 className="text-lg font-semibold text-white mb-4">Severity Levels</h3>
          <SeverityDonut />
        </GlassmorphicCard>
      </div>

      {/* Current Patients */}
      <GlassmorphicCard className="p-6" delay={0.5}>
        <h3 className="text-lg font-semibold text-white mb-4">Critical Cases Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockPatients.map((patient) => (
            <motion.div
              key={patient.id}
              whileHover={{ scale: 1.02 }}
              onClick={() => setSelectedPatient(patient)}
              className="glass-card p-4 cursor-pointer transition-all duration-300"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-semibold text-white">{patient.name}</p>
                  <p className="text-xs text-gray-400">{patient.ward}</p>
                </div>
                <Badge level={patient.severity} />
              </div>
              <div className="text-sm space-y-1 text-gray-300">
                <p>LOS: ~{patient.predictedLOS} days</p>
                <p className="text-teal text-xs">📅 {patient.dischargeDate}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassmorphicCard>

      {/* Patient Detail Sidebar */}
      <PatientDetailSidebar
        isOpen={!!selectedPatient}
        patient={selectedPatient}
        onClose={() => setSelectedPatient(null)}
      />
    </div>
  )
}

const DashboardLayout: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuthStore()
  const [currentPage, setCurrentPage] = useState('dashboard')

  if (!isAuthenticated) {
    return <LoginPage onSuccess={() => setCurrentPage('dashboard')} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy via-navy to-blue-900 relative">
      <AnimatedBackground />

      {/* Sidebar Navigation */}
      <motion.div
        className="fixed left-0 top-0 w-64 h-screen glass-card border-r border-gray-600 p-6 flex flex-col"
        initial={{ x: -264 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">HRF</h1>
          <p className="text-xs text-teal">Recovery Forecast</p>
        </div>

        <nav className="flex-1 space-y-3">
          {[
            { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
            { id: 'upload', label: '📤 Data Upload', icon: '📤' },
            { id: 'analysis', label: '🔍 Analysis', icon: '🔍' },
          ].map((item) => (
            <motion.button
              key={item.id}
              whileHover={{ x: 5 }}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all duration-300 ${
                currentPage === item.id
                  ? 'bg-teal bg-opacity-20 text-teal border border-teal'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {item.label}
            </motion.button>
          ))}
        </nav>

        <div className="border-t border-gray-600 pt-4 space-y-3">
          <div className="px-4 py-2">
            <p className="text-xs text-gray-400">Hospital</p>
            <p className="text-sm font-semibold text-white">{user?.hospitalId}</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={logout}
            className="btn-secondary w-full"
          >
            Sign Out
          </motion.button>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="ml-64 p-8">
        {currentPage === 'dashboard' && <DashboardPage />}
        {currentPage === 'upload' && <UploadPage />}
        {currentPage === 'analysis' && <AnalysisPage />}
      </div>
    </div>
  )
}

export default DashboardLayout
