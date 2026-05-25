'use client'

import React from 'react'
import { motion } from 'framer-motion'

interface DataUploadProps {
  onUpload?: (files: File[]) => Promise<void>
  isLoading?: boolean
}

export const DataUploadZone: React.FC<DataUploadProps> = ({
  onUpload,
  isLoading = false,
}) => {
  const [isDragging, setIsDragging] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [uploaded, setUploaded] = React.useState(false)

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    handleUpload(files)
  }

  const handleUpload = async (files: File[]) => {
    if (onUpload) {
      setProgress(0)
      const interval = setInterval(() => {
        setProgress((p) => (p < 90 ? p + 10 : p))
      }, 300)

      try {
        await onUpload(files)
        setProgress(100)
        setUploaded(true)
      } finally {
        clearInterval(interval)
      }
    }
  }

  return (
    <motion.div
      className="w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {!uploaded ? (
        <div
          onDragOver={() => setIsDragging(true)}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`glass-card border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragging
              ? 'border-teal bg-opacity-20 bg-teal scale-105'
              : 'border-gray-500'
          }`}
        >
          <div className="space-y-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-xl font-semibold text-white">
                Drop your dataset here
              </h3>
              <p className="text-gray-400 mt-2">
                or click to select CSV/Excel files
              </p>
            </div>

            {isLoading && (
              <div className="mt-6 space-y-2">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <motion.div
                    className="bg-teal h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <p className="text-sm text-gray-400">{progress}% Processing...</p>
              </div>
            )}

            <input
              type="file"
              multiple
              accept=".csv,.xlsx,.xls"
              className="hidden"
              id="file-input"
              onChange={(e) =>
                handleUpload(Array.from(e.currentTarget.files || []))
              }
            />
            <label htmlFor="file-input" className="btn-primary inline-block">
              Select Files
            </label>
          </div>
        </div>
      ) : (
        <div className="glass-card p-8 text-center">
          <div className="text-5xl mb-4">✅</div>
          <h3 className="text-2xl font-bold text-teal">Upload Successful!</h3>
          <p className="text-gray-400 mt-2">Your dataset is being analyzed</p>
        </div>
      )}
    </motion.div>
  )
}
