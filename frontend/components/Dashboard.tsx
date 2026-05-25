'use client'

import React from 'react'
import { motion } from 'framer-motion'

interface BedGridProps {
  data?: Array<{
    day: number
    current: number
    predicted: number
    available: number
  }>
}

export const BedGrid: React.FC<BedGridProps> = ({
  data = Array.from({ length: 14 }, (_, i) => ({
    day: i + 1,
    current: Math.floor(Math.random() * 50) + 30,
    predicted: Math.floor(Math.random() * 50) + 30,
    available: Math.floor(Math.random() * 100),
  })),
}) => {
  const maxValue = 100

  return (
    <div className="w-full space-y-4">
      <h3 className="text-lg font-semibold text-white">14-Day Bed Occupancy Forecast</h3>
      <div className="grid grid-cols-7 gap-3">
        {data.map((day, idx) => {
          const occupancyPercent = (day.current / maxValue) * 100
          const intensity = occupancyPercent / 100

          return (
            <motion.div
              key={idx}
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <div
                className="rounded-lg p-2 mb-2 transition-all duration-300"
                style={{
                  background: `rgba(32, 178, 170, ${intensity * 0.7})`,
                  border: `1px solid rgba(32, 178, 170, ${intensity})`,
                }}
              >
                <div className="text-xs text-gray-300">Day {day.day}</div>
                <div className="text-sm font-bold text-teal">{day.current}</div>
                <div className="text-xs text-gray-400">{day.available} available</div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

interface SeverityDonutProps {
  data?: Record<number, number>
}

export const SeverityDonut: React.FC<SeverityDonutProps> = ({
  data = {
    1: 180,
    2: 245,
    3: 312,
    4: 189,
    5: 74,
  },
}) => {
  const colors = ['#10B981', '#F59E0B', '#F97316', '#EF4444', '#7C3AED']
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  const radius = 80
  const circumference = 2 * Math.PI * radius

  let offset = 0
  const segments = Object.entries(data).map(([level, value], idx) => {
    const percentage = (value / total) * 100
    const segmentLength = (percentage / 100) * circumference
    const currentOffset = offset
    offset += segmentLength

    return {
      level: parseInt(level),
      value,
      percentage,
      color: colors[idx],
      offset: currentOffset,
      length: segmentLength,
    }
  })

  return (
    <div className="flex flex-col items-center space-y-6">
      <svg width="200" height="200" className="transform -rotate-90">
        {segments.map((seg, idx) => (
          <motion.circle
            key={idx}
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke={seg.color}
            strokeWidth="20"
            strokeDasharray={`${seg.length} ${circumference}`}
            strokeDashoffset={-seg.offset}
            initial={{ strokeDashoffset: 0 }}
            animate={{ strokeDashoffset: -seg.offset }}
            transition={{ duration: 1, delay: idx * 0.1 }}
            opacity="0.8"
          />
        ))}
      </svg>

      <div className="grid grid-cols-2 gap-4 text-sm">
        {segments.map((seg) => (
          <div key={seg.level} className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: seg.color }}
            />
            <span className="text-gray-300">
              Level {seg.level}: {seg.value} ({seg.percentage.toFixed(1)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Main Dashboard Component
 */
const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-navy via-[#1a3a3a] to-[#0f2626] p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-4xl font-bold text-white">Healthcare Recovery Dashboard</h1>
          <p className="text-gray-400">Real-time forecasting and patient insights</p>
        </motion.div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Bed Occupancy - Takes 2 columns on large screens */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 bg-glass backdrop-blur-md rounded-xl p-6 border border-white border-opacity-10"
          >
            <BedGrid />
          </motion.div>

          {/* Severity Donut - Takes 1 column */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-glass backdrop-blur-md rounded-xl p-6 border border-white border-opacity-10"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Patient Severity Distribution</h3>
            <SeverityDonut />
          </motion.div>
        </div>

        {/* Footer Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          {[
            { label: 'Active Patients', value: '1,247' },
            { label: 'Avg Recovery Time', value: '14.2 days' },
            { label: 'System Accuracy', value: '94.7%' },
            { label: 'Alert Threshold', value: '85%' },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-glass backdrop-blur-md rounded-lg p-4 border border-white border-opacity-10 text-center"
            >
              <p className="text-gray-400 text-sm">{stat.label}</p>
              <p className="text-2xl font-bold text-teal mt-1">{stat.value}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

export default Dashboard
