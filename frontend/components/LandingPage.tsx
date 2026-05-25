'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { HeroAnimation, DataWaveBackground } from '@/components/HeroAnimation'
import { GlassmorphicCard } from '@/components/ui'

export const LandingPage: React.FC<{ onGetStarted?: () => void }> = ({
  onGetStarted,
}) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  }

  const features = [
    {
      icon: '📊',
      title: 'Predictive Analytics',
      description: 'AI-powered insights across recovery levels 1-5 for precise care planning',
    },
    {
      icon: '🛏️',
      title: 'Real-time Bed Management',
      description: 'Dynamic patient-to-bed allocation optimizing hospital resources',
    },
    {
      icon: '🤖',
      title: 'Automated Reporting',
      description: 'Generate comprehensive clinical reports instantly with one click',
    },
  ]

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-gradient-to-b from-navy via-navy to-[#0a1419]">
      {/* Animated background waves */}
      <DataWaveBackground />

      {/* Hero Section with gradient overlay */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 pt-20">
        {/* Hero Content */}
        <motion.div
          className="text-center max-w-4xl mx-auto space-y-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          {/* Animated Hero Graphic */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="flex justify-center"
          >
            <HeroAnimation />
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            variants={itemVariants}
            className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-white via-teal to-white bg-clip-text text-transparent leading-tight"
          >
            Predicting Recovery, <br /> Optimizing Care.
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            variants={itemVariants}
            className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed"
          >
            The AI-driven bridge between clinical data and hospital bed management.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            variants={itemVariants}
            className="pt-6"
          >
            <motion.button
              onClick={onGetStarted}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="group px-8 md:px-12 py-4 bg-gradient-to-r from-teal to-[#1aa89e] text-navy font-bold text-lg rounded-lg shadow-[0_0_30px_rgba(32,178,170,0.3)] hover:shadow-[0_0_50px_rgba(32,178,170,0.5)] transition-all duration-300"
            >
              <span className="flex items-center gap-2">
                Get Started
                <motion.span
                  animate={{ x: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  →
                </motion.span>
              </span>
            </motion.button>
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="text-teal text-sm">Scroll to explore</div>
          <div className="text-2xl text-teal">↓</div>
        </motion.div>
      </div>

      {/* Feature Cards Section */}
      <motion.div
        className="relative z-10 py-20 px-4"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
      >
        <div className="max-w-6xl mx-auto">
          {/* Section Title */}
          <motion.div
            variants={itemVariants}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Powerful Features for Modern Healthcare
            </h2>
            <div className="h-1 w-20 bg-gradient-to-r from-teal to-transparent mx-auto" />
          </motion.div>

          {/* Feature Cards Grid */}
          <div className="grid md:grid-cols-3 gap-8 lg:gap-10">
            {features.map((feature, index) => (
              <GlassmorphicCard
                key={index}
                delay={index * 0.1}
                className="group p-8 hover:scale-105 cursor-default"
              >
                <motion.div
                  initial={{ scale: 1 }}
                  whileHover={{ scale: 1.1 }}
                  className="text-5xl mb-4 inline-block"
                >
                  {feature.icon}
                </motion.div>
                <h3 className="text-2xl font-bold mb-3 text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-300 leading-relaxed">
                  {feature.description}
                </p>
                <motion.div
                  className="mt-6 h-1 bg-gradient-to-r from-teal to-transparent rounded-full"
                  initial={{ width: 0 }}
                  whileHover={{ width: '100%' }}
                  transition={{ duration: 0.3 }}
                />
              </GlassmorphicCard>
            ))}
          </div>
        </div>
      </motion.div>

      {/* CTA Banner at Bottom */}
      <motion.div
        className="relative z-10 py-20 px-4"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <GlassmorphicCard className="max-w-3xl mx-auto p-12 text-center">
          <h3 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Transform Your Hospital's Care?
          </h3>
          <p className="text-gray-300 mb-8 text-lg">
            Join leading healthcare providers using AI to predict patient recovery and optimize bed management.
          </p>
          <motion.button
            onClick={onGetStarted}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-10 py-4 bg-teal text-navy font-bold text-lg rounded-lg hover:shadow-[0_0_30px_rgba(32,178,170,0.4)] transition-all duration-300"
          >
            Start Your Free Trial
          </motion.button>
        </GlassmorphicCard>
      </motion.div>
    </div>
  )
}
