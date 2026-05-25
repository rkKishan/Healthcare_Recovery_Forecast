'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

export const AnimatedBackground: React.FC = () => {
  const [nodes, setNodes] = useState<Array<{ id: number; x: number; y: number }>>([])

  useEffect(() => {
    const newNodes = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
    }))
    setNodes(newNodes)
  }, [])

  return (
    <div className="floating-bg">
      {nodes.map((node) => (
        <motion.div
          key={node.id}
          className="data-node"
          style={{
            left: `${node.x}%`,
            top: `${node.y}%`,
          }}
          animate={{
            y: [0, 20, 0],
            opacity: [0.2, 0.5, 0.2],
          }}
          transition={{
            duration: 4 + Math.random() * 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  )
}

export const GlassmorphicCard: React.FC<{
  children: React.ReactNode
  className?: string
  delay?: number
}> = ({ children, className = '', delay = 0 }) => {
  return (
    <motion.div
      className={`glass-card ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
    >
      {children}
    </motion.div>
  )
}

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({
  size = 'md',
}) => {
  const sizeClass = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  }

  return (
    <div className={`${sizeClass[size]} border-4 border-teal border-t-transparent rounded-full animate-spin`} />
  )
}

export const Badge: React.FC<{
  level: number
  text?: string
}> = ({ level, text }) => {
  const levels = {
    1: 'badge-low',
    2: 'badge-low',
    3: 'badge-medium',
    4: 'badge-high',
    5: 'badge-critical',
  }

  return (
    <span className={`badge ${levels[level as keyof typeof levels]}`}>
      {text || `Level ${level}`}
    </span>
  )
}
