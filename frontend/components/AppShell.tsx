'use client'

import React, { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LandingPage } from '@/components/LandingPage'
import { RegistrationPage } from '@/components/RegistrationPage'
import { EnhancedLoginPage } from '@/components/EnhancedLoginPage'
import { useAuthStore } from '@/lib/store'

// Dynamically import Dashboard to avoid circular dependencies
const DashboardComponent = React.lazy(() => import('@/components/Dashboard'))

type Page = 'landing' | 'login' | 'register' | 'dashboard'

interface AppShellProps {
  initialPage?: Page
  onDashboardReady?: () => void
}

export const AppShell: React.FC<AppShellProps> = ({
  initialPage = 'landing',
  onDashboardReady,
}) => {
  const [currentPage, setCurrentPage] = useState<Page>(initialPage)
  const { isAuthenticated } = useAuthStore()

  // Smooth page transitions
  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  }

  const transitionConfig = {
    duration: 0.3,
    ease: 'easeInOut',
  }

  // Determine which page to show based on auth state
  useEffect(() => {
    if (isAuthenticated && currentPage !== 'dashboard') {
      setCurrentPage('dashboard')
      onDashboardReady?.()
    }
  }, [isAuthenticated, currentPage, onDashboardReady])

  const handleGetStarted = () => {
    setCurrentPage('login')
  }

  const handleRegister = () => {
    setCurrentPage('register')
  }

  const handleBackToLogin = () => {
    setCurrentPage('login')
  }

  const handleLoginSuccess = () => {
    setCurrentPage('dashboard')
    onDashboardReady?.()
  }

  return (
    <div className="relative w-full min-h-screen overflow-hidden">
      <AnimatePresence mode="wait">
        {currentPage === 'landing' && (
          <motion.div
            key="landing"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={transitionConfig}
            className="absolute inset-0 w-full"
          >
            <LandingPage onGetStarted={handleGetStarted} />
          </motion.div>
        )}

        {currentPage === 'login' && (
          <motion.div
            key="login"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={transitionConfig}
            className="absolute inset-0 w-full"
          >
            <EnhancedLoginPage
              onSuccess={handleLoginSuccess}
              onRegister={handleRegister}
            />
          </motion.div>
        )}

        {currentPage === 'register' && (
          <motion.div
            key="register"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={transitionConfig}
            className="absolute inset-0 w-full"
          >
            <RegistrationPage
              onSuccess={handleLoginSuccess}
              onBackToLogin={handleBackToLogin}
            />
          </motion.div>
        )}

        {currentPage === 'dashboard' && (
          <motion.div
            key="dashboard"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={transitionConfig}
            className="absolute inset-0 w-full"
          >
            <React.Suspense
              fallback={
                <div className="min-h-screen bg-gradient-to-b from-navy via-navy to-[#0a1419] flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-12 h-12 border-4 border-teal border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-teal">Loading dashboard...</p>
                  </div>
                </div>
              }
            >
              <DashboardComponent />
            </React.Suspense>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AppShell