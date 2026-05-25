'use client'

import React from 'react'
import { motion } from 'framer-motion'

interface PatientTimelineEvent {
  date: string
  event: string
  status: 'completed' | 'ongoing' | 'planned'
}

interface RecoveryTimelineProps {
  patientName: string
  admissionDate: string
  predictedDischargeDate: string
  events: PatientTimelineEvent[]
}

export const RecoveryTimeline: React.FC<RecoveryTimelineProps> = ({
  patientName,
  admissionDate,
  predictedDischargeDate,
  events,
}) => {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">{patientName}</h3>
        <p className="text-gray-400 text-sm">
          Admitted: {admissionDate} | Expected Discharge: {predictedDischargeDate}
        </p>
      </div>

      <div className="relative">
        {events.map((event, idx) => {
          const statusColors = {
            completed: 'bg-green-500',
            ongoing: 'bg-teal',
            planned: 'bg-gray-600',
          }

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="flex items-start mb-8 relative"
            >
              {/* Timeline line */}
              {idx < events.length - 1 && (
                <div className="absolute left-5 top-16 w-0.5 h-12 bg-teal opacity-30" />
              )}

              {/* Timeline dot */}
              <div className="relative z-10 flex-shrink-0">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${statusColors[event.status]}`}>
                  <div className="w-4 h-4 bg-navy rounded-full" />
                </div>
              </div>

              {/* Event content */}
              <div className="ml-6 glass-card p-4 flex-1">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-white">{event.event}</p>
                  <span className="text-xs px-2 py-1 rounded bg-opacity-20 bg-teal text-teal">
                    {event.status}
                  </span>
                </div>
                <p className="text-gray-400 text-sm mt-1">{event.date}</p>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

interface FeatureImportanceProps {
  features: Array<{
    name: string
    importance: number
    impact: 'positive' | 'negative'
  }>
}

export const FeatureImportance: React.FC<FeatureImportanceProps> = ({
  features,
}) => {
  const maxImportance = Math.max(...features.map((f) => f.importance))

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-white">Key Factors Influencing Recovery</h3>

      {features.map((feature, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: idx * 0.1 }}
          className="space-y-2"
        >
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-300 font-medium">{feature.name}</span>
            <span className={`text-xs font-semibold ${
              feature.impact === 'positive' ? 'text-green-400' : 'text-red-400'
            }`}>
              {feature.impact === 'positive' ? '+' : '-'}{(feature.importance * 100).toFixed(1)}%
            </span>
          </div>

          <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                feature.impact === 'positive'
                  ? 'bg-green-500'
                  : 'bg-red-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${(feature.importance / maxImportance) * 100}%` }}
              transition={{ duration: 0.8, delay: idx * 0.1 }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  )
}
