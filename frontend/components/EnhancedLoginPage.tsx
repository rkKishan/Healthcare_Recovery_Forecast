'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/lib/store'
import { GlassmorphicCard } from '@/components/ui'

interface ForgotPasswordState {
  isOpen: boolean
  email: string
  step: 'email' | 'code' | 'reset'
  isLoading: boolean
  message?: string
}

export const EnhancedLoginPage: React.FC<{
  onSuccess?: () => void
  onRegister?: () => void
}> = ({ onSuccess, onRegister }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const [forgotPassword, setForgotPassword] = useState<ForgotPasswordState>({
    isOpen: false,
    email: '',
    step: 'email',
    isLoading: false,
  })

  const { login } = useAuthStore()

  // Load remembered email if available
  React.useEffect(() => {
    const remembered = localStorage.getItem('rememberedEmail')
    if (remembered) {
      setEmail(remembered)
      setRememberMe(true)
    }
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await login(email, password)

      // Save remembered email
      if (rememberMe) {
        localStorage.setItem('rememberedEmail', email)
      } else {
        localStorage.removeItem('rememberedEmail')
      }

      onSuccess?.()
    } catch (err) {
      setError('Invalid email or password. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPasswordStep = async () => {
    if (!forgotPassword.email) {
      setForgotPassword((prev) => ({
        ...prev,
        message: 'Please enter your email',
      }))
      return
    }

    setForgotPassword((prev) => ({ ...prev, isLoading: true }))

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      if (forgotPassword.step === 'email') {
        setForgotPassword((prev) => ({
          ...prev,
          step: 'code',
          message: 'Check your email for the reset code',
        }))
      } else if (forgotPassword.step === 'code') {
        setForgotPassword((prev) => ({
          ...prev,
          step: 'reset',
          message: 'Enter your new password',
        }))
      }
    } finally {
      setForgotPassword((prev) => ({ ...prev, isLoading: false }))
    }
  }

  const closeForgotPassword = () => {
    setForgotPassword({
      isOpen: false,
      email: '',
      step: 'email',
      isLoading: false,
    })
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.1 },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  }

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-gradient-to-br from-navy via-navy to-[#0a1419] p-4">
      {/* Animated background waves */}
      <div className="absolute inset-0 opacity-20">
        {[...Array(2)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute inset-0 opacity-[0.03]"
            style={{
              background: `linear-gradient(90deg, transparent, #20B2AA, transparent)`,
            }}
            animate={{ x: ['-100%', '100%'] }}
            transition={{
              duration: 8 + i * 2,
              repeat: Infinity,
              ease: 'linear',
              delay: i,
            }}
          />
        ))}
      </div>

      {/* Floating orbs */}
      <motion.div
        className="absolute top-20 left-10 w-64 h-64 bg-teal rounded-full filter blur-3xl opacity-5"
        animate={{
          y: [0, 50, 0],
          x: [0, 30, 0],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      <motion.div
        className="absolute bottom-20 right-10 w-64 h-64 bg-teal rounded-full filter blur-3xl opacity-5"
        animate={{
          y: [0, -50, 0],
          x: [0, -30, 0],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Main Login Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        <GlassmorphicCard className="p-8 space-y-8">
          {/* Header */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="text-center space-y-2"
          >
            <motion.div variants={itemVariants} className="text-4xl font-bold text-white">
              Welcome Back
            </motion.div>
            <motion.p variants={itemVariants} className="text-teal text-sm">
              Healthcare Recovery Forecast System
            </motion.p>
          </motion.div>

          {/* Login Form */}
          <motion.form
            onSubmit={handleLogin}
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-5"
          >
            {/* Email Field */}
            <motion.div variants={itemVariants}>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-glass w-full"
                placeholder="Enter your email"
                required
              />
            </motion.div>

            {/* Password Field */}
            <motion.div variants={itemVariants}>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-glass w-full pr-10"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </motion.div>

            {/* Remember Me & Forgot Password */}
            <motion.div
              variants={itemVariants}
              className="flex items-center justify-between text-sm"
            >
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded bg-glass border border-gray-600 cursor-pointer accent-teal"
                />
                <span className="text-gray-300 group-hover:text-teal transition-colors">
                  Remember me
                </span>
              </label>
              <button
                type="button"
                onClick={() =>
                  setForgotPassword((prev) => ({
                    ...prev,
                    isOpen: true,
                    step: 'email',
                  }))
                }
                className="text-teal hover:text-teal hover:underline transition-colors"
              >
                Forgot Password?
              </button>
            </motion.div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-red-500 bg-opacity-20 border border-red-500 text-red-300 px-4 py-3 rounded-lg text-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              variants={itemVariants}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                'Sign In'
              )}
            </motion.button>
          </motion.form>

          {/* Divider */}
          <motion.div
            variants={itemVariants}
            className="relative"
          >
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gradient-to-b from-navy via-navy to-[#0a1419] text-gray-500">
                New to platform?
              </span>
            </div>
          </motion.div>

          {/* Register Link */}
          <motion.div variants={itemVariants} className="text-center">
            <button
              onClick={onRegister}
              className="px-6 py-3 bg-teal bg-opacity-10 border border-teal text-teal font-semibold rounded-lg hover:bg-opacity-20 transition-all duration-300 w-full"
            >
              Create Account
            </button>
          </motion.div>
        </GlassmorphicCard>

        {/* Security Note */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center mt-6 text-xs text-gray-500"
        >
          🔒 HIPAA Compliant • Encrypted Connection • Secure Login
        </motion.div>
      </motion.div>

      {/* Forgot Password Modal */}
      <AnimatePresence>
        {forgotPassword.isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeForgotPassword}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md"
            >
              <GlassmorphicCard className="p-8 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-white">Reset Password</h2>
                  <button
                    onClick={closeForgotPassword}
                    className="text-gray-400 hover:text-white transition-colors text-2xl leading-none"
                  >
                    ×
                  </button>
                </div>

                {/* Content based on step */}
                <div className="space-y-4">
                  {forgotPassword.step === 'email' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-4"
                    >
                      <p className="text-gray-300">
                        Enter your email address and we'll send you a reset code.
                      </p>
                      <input
                        type="email"
                        value={forgotPassword.email}
                        onChange={(e) =>
                          setForgotPassword((prev) => ({
                            ...prev,
                            email: e.target.value,
                          }))
                        }
                        className="input-glass w-full"
                        placeholder="your.email@hospital.com"
                      />
                    </motion.div>
                  )}

                  {forgotPassword.step === 'code' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-4"
                    >
                      <p className="text-gray-300">
                        Enter the 6-digit code sent to {forgotPassword.email}
                      </p>
                      <input
                        type="text"
                        placeholder="000000"
                        maxLength={6}
                        className="input-glass w-full text-center text-2xl tracking-widest"
                      />
                    </motion.div>
                  )}

                  {forgotPassword.step === 'reset' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-4"
                    >
                      <p className="text-gray-300">Enter your new password</p>
                      <input
                        type="password"
                        placeholder="New password"
                        className="input-glass w-full"
                      />
                      <input
                        type="password"
                        placeholder="Confirm password"
                        className="input-glass w-full"
                      />
                    </motion.div>
                  )}

                  {forgotPassword.message && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-teal text-sm text-center"
                    >
                      {forgotPassword.message}
                    </motion.p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={closeForgotPassword}
                    className="flex-1 px-4 py-3 bg-gray-700 bg-opacity-50 text-white rounded-lg hover:bg-opacity-70 transition-all duration-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleForgotPasswordStep}
                    disabled={forgotPassword.isLoading}
                    className="flex-1 btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {forgotPassword.isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
                      </>
                    ) : (
                      'Continue'
                    )}
                  </button>
                </div>
              </GlassmorphicCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
