'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

/**
 * Animated heartbeat transitioning into a data trend line
 * Creates a visual representation of clinical data becoming insights
 */
export const HeroAnimation: React.FC = () => {
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((p) => (p + 1) % 4)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // SVG path for heartbeat
  const heartbeatPath = 'M 20 50 L 30 50 L 35 35 L 40 50 L 50 50 L 60 40 L 70 50 L 80 50'
  
  // SVG path for data trend (upward slope)
  const trendPath = 'M 20 60 L 30 55 L 40 48 L 50 42 L 60 35 L 70 30 L 80 25'

  const containerVariants = {
    animate: {
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3,
      },
    },
  }

  const itemVariants = {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1, transition: { duration: 0.8 } },
  }

  return (
    <div className="relative w-full h-64 flex items-center justify-center">
      {/* SVG Visualization */}
      <svg width="300" height="150" viewBox="0 0 100 100" className="absolute">
        {/* Heartbeat line */}
        <motion.path
          d={heartbeatPath}
          stroke="#20B2AA"
          strokeWidth="1.5"
          fill="none"
          opacity={phase < 2 ? 1 : 0.3}
          animate={{ opacity: phase < 2 ? 1 : 0.3 }}
          transition={{ duration: 0.5 }}
        />

        {/* Transition pulse */}
        {phase === 2 && (
          <motion.circle
            cx="80"
            cy="50"
            r="5"
            fill="#20B2AA"
            animate={{
              r: [5, 15],
              opacity: [1, 0],
            }}
            transition={{ duration: 0.8 }}
          />
        )}

        {/* Data trend line */}
        <motion.path
          d={trendPath}
          stroke="#20B2AA"
          strokeWidth="1.5"
          fill="none"
          opacity={phase >= 2 ? 1 : 0.3}
          animate={{ opacity: phase >= 2 ? 1 : 0.3 }}
          transition={{ duration: 0.5 }}
        />

        {/* Pulse wave background */}
        {[0, 1, 2].map((i) => (
          <motion.circle
            key={i}
            cx="50"
            cy="50"
            r="10"
            fill="none"
            stroke="#20B2AA"
            strokeWidth="0.5"
            animate={{
              r: [10, 40],
              opacity: [0.8, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.6,
            }}
          />
        ))}
      </svg>

      {/* Animated data nodes */}
      <motion.div
        className="absolute inset-0 flex items-center justify-center"
        variants={containerVariants}
        animate="animate"
      >
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-3 h-3 rounded-full bg-teal"
            variants={itemVariants}
            style={{
              left: `${25 + i * 12}%`,
              top: `${50 - i * 8}%`,
            }}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.3, 1, 0.3],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
      </motion.div>
    </div>
  )
}

/**
 * Data Wave animation for background
 */
export const DataWaveBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Wave 1 */}
      <motion.div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          background: `linear-gradient(90deg, transparent, #20B2AA, transparent)`,
        }}
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      {/* Wave 2 */}
      <motion.div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          background: `linear-gradient(90deg, transparent, #20B2AA, transparent)`,
        }}
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: 'linear',
          delay: 1,
        }}
      />

      {/* Wave 3 */}
      <motion.div
        className="absolute inset-0 opacity-[0.01]"
        style={{
          background: `linear-gradient(90deg, transparent, #20B2AA, transparent)`,
        }}
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
          delay: 2,
        }}
      />
    </div>
  )
}
