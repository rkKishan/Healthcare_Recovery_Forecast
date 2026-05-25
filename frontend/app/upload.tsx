'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { DataUploadZone } from '@/components/DataUpload'
import { GlassmorphicCard } from '@/components/ui'
import { useDataStore } from '@/lib/store'

export const UploadPage: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<string | null>(null)
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'complete'>('idle')
  const setUploadedData = useDataStore((s) => s.setUploadedData)
  const setPredictions = useDataStore((s) => s.setPredictions)

  const handleUpload = async (files: File[]) => {
    setProcessingStatus('processing')
    setUploadedFile(files[0]?.name || 'Unknown file')

    // Simulate backend processing
    setTimeout(() => {
      // Mock data - replace with actual API call
      const mockPatients = Array.from({ length: 50 }, (_, i) => ({
        id: `P${String(i + 1).padStart(3, '0')}`,
        name: `Patient ${i + 1}`,
        age: Math.floor(Math.random() * 80) + 18,
        severity: Math.floor(Math.random() * 5) + 1,
        ward: ['ICU', 'General Ward', 'Recovery Ward'][Math.floor(Math.random() * 3)],
        admissionDate: new Date().toISOString().split('T')[0],
      }))

      setUploadedData(mockPatients)
      setPredictions(
        mockPatients.map((p) => ({
          ...p,
          predictedLOS: Math.floor(Math.random() * 14) + 2,
          confidence: Math.floor(Math.random() * 30) + 70,
        }))
      )

      setProcessingStatus('complete')
    }, 3000)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Data Upload Hub</h1>
        <p className="text-gray-400">
          Upload your patient dataset for recovery prediction analysis
        </p>
      </div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <DataUploadZone
          onUpload={handleUpload}
          isLoading={processingStatus === 'processing'}
        />
      </motion.div>

      {/* Upload Info */}
      {uploadedFile && (
        <GlassmorphicCard className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">File: {uploadedFile}</h3>
                <p className="text-gray-400 text-sm mt-1">Processing dataset...</p>
              </div>
              <div className="text-right">
                {processingStatus === 'processing' && (
                  <div className="animate-spin w-8 h-8 border-2 border-teal border-t-transparent rounded-full" />
                )}
                {processingStatus === 'complete' && (
                  <span className="text-3xl">✅</span>
                )}
              </div>
            </div>

            {processingStatus === 'complete' && (
              <div className="border-t border-gray-600 pt-4">
                <p className="text-teal font-semibold mb-3">Processing Complete</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="glass-card p-3">
                    <p className="text-gray-400">Total Records</p>
                    <p className="text-2xl font-bold text-teal">50</p>
                  </div>
                  <div className="glass-card p-3">
                    <p className="text-gray-400">Avg. Age</p>
                    <p className="text-2xl font-bold text-teal">54</p>
                  </div>
                  <div className="glass-card p-3">
                    <p className="text-gray-400">Critical Cases</p>
                    <p className="text-2xl font-bold text-teal">12</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </GlassmorphicCard>
      )}

      {/* File Format Guide */}
      <GlassmorphicCard className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📋 Expected File Format</h3>
        <div className="space-y-4">
          <div>
            <p className="text-teal font-semibold mb-2">Required Columns:</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                'Patient ID',
                'Age',
                'Gender',
                'Admission Date',
                'Severity',
                'Ward',
                'Comorbidities',
                'Vital Signs',
              ].map((col) => (
                <div key={col} className="glass-card p-3 rounded">
                  <p className="text-sm text-teal font-mono">{col}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-gray-600 pt-4">
            <p className="text-gray-400 text-sm">
              💡 <strong>CSV Format Example:</strong>
            </p>
            <pre className="bg-black bg-opacity-50 p-4 rounded mt-2 text-xs text-green-400 overflow-x-auto">
{`Patient_ID,Age,Gender,Admission,Severity,Ward
P001,65,M,2026-03-29,3,ICU
P002,42,F,2026-03-29,2,General Ward
P003,78,M,2026-03-28,4,ICU`}
            </pre>
          </div>
        </div>
      </GlassmorphicCard>

      {/* Best Practices */}
      <GlassmorphicCard className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">✅ Best Practices</h3>
        <ul className="space-y-3 text-gray-300">
          {[
            'Ensure all required columns are present',
            'Remove duplicate patient records before upload',
            'Standardize date format (YYYY-MM-DD)',
            'Check for missing values in critical fields',
            'Maximum file size: 50 MB',
            'Supported formats: CSV, XLSX, XLS',
          ].map((practice, idx) => (
            <motion.li
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="flex items-center gap-3"
            >
              <span className="text-teal text-lg">✓</span>
              {practice}
            </motion.li>
          ))}
        </ul>
      </GlassmorphicCard>
    </div>
  )
}

export default UploadPage
