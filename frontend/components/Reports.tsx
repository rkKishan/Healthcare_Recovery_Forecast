'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'

interface PDFReportProps {
  hospitalName: string
  reportDate: string
  datasetStats: {
    totalPatients: number
    avgLOS: number
    criticalCount: number
  }
  chartRef?: React.RefObject<HTMLDivElement>
}

export const PDFReportGeneratorButton: React.FC<{
  data: PDFReportProps
}> = ({ data }) => {
  const [isGenerating, setIsGenerating] = useState(false)

  const generatePDF = async () => {
    setIsGenerating(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const encodedHospitalName = encodeURIComponent(data.hospitalName)
      
      const response = await fetch(
        `${apiUrl}/api/reports/pdf?hospital_name=${encodedHospitalName}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/pdf',
          },
        }
      )
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // Get the blob from response
      const blob = await response.blob()
      
      // Create a download link and trigger it
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Recovery_Forecast_Report_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
    } catch (error) {
      console.error('PDF generation error:', error)
      alert(`Failed to generate PDF: ${error instanceof Error ? error.message : 'Unknown error'}. Make sure the backend server is running on port 8000.`)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={generatePDF}
      disabled={isGenerating}
      className="btn-primary flex items-center gap-2 disabled:opacity-50"
    >
      {isGenerating ? (
        <>
          <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
          Generating...
        </>
      ) : (
        <>
          📄 Download Comprehensive Report
        </>
      )}
    </motion.button>
  )
}

interface PatientReportCardProps {
  patientId: string
  name: string
  severity: number
  predictedLOS: number
  confidence: number
  dischargeDate: string
  factors: string[]
}

export const PatientReportCard: React.FC<PatientReportCardProps> = ({
  patientId,
  name,
  severity,
  predictedLOS,
  confidence,
  dischargeDate,
  factors,
}) => {
  const severityColors = {
    1: 'bg-green-500',
    2: 'bg-yellow-500',
    3: 'bg-orange-500',
    4: 'bg-red-500',
    5: 'bg-purple-600',
  }

  return (
    <motion.div
      className="glass-card p-6 space-y-4"
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-lg font-bold text-white">{name}</h4>
          <p className="text-gray-400 text-sm">ID: {patientId}</p>
        </div>
        <span className={`${severityColors[severity as keyof typeof severityColors]} badge text-white`}>
          Level {severity}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-gray-400 text-xs">Predicted LOS</p>
          <p className="text-2xl font-bold text-teal">{predictedLOS}</p>
          <p className="text-gray-500 text-xs">days</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Confidence</p>
          <p className="text-2xl font-bold text-teal">{confidence}%</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Expected</p>
          <p className="text-sm font-semibold text-teal">{dischargeDate}</p>
        </div>
      </div>

      <div className="border-t border-gray-600 pt-4">
        <p className="text-xs text-gray-400 mb-2">Key Factors:</p>
        <div className="flex flex-wrap gap-2">
          {factors.map((factor, idx) => (
            <span key={idx} className="text-xs badge bg-teal bg-opacity-20 text-teal">
              {factor}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
