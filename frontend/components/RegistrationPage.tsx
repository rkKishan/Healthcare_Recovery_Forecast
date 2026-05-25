'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { GlassmorphicCard } from '@/components/ui'

type Role = 'administrator' | 'doctor' | 'analyst'

interface RegistrationData {
  hospitalName: string
  professionalId: string
  email: string
  password: string
  confirmPassword: string
  role: Role
}

interface ValidationErrors {
  hospitalName?: string
  professionalId?: string
  email?: string
  password?: string
  confirmPassword?: string
}

export const RegistrationPage: React.FC<{ onSuccess?: () => void; onBackToLogin?: () => void }> = ({
  onSuccess,
  onBackToLogin,
}) => {
  const [formData, setFormData] = useState<RegistrationData>({
    hospitalName: '',
    professionalId: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'doctor',
  })

  const [errors, setErrors] = useState<ValidationErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({})

  const roles: { value: Role; label: string; description: string }[] = [
    { value: 'administrator', label: 'Administrator', description: 'Manage hospital settings' },
    { value: 'doctor', label: 'Doctor', description: 'Clinical insights & predictions' },
    { value: 'analyst', label: 'Data Analyst', description: 'Analytics & reports' },
  ]

  // Real-time validation
  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case 'hospitalName':
        return value.length < 3 ? 'Hospital name must be at least 3 characters' : undefined
      case 'professionalId':
        return value.length < 4 ? 'Professional ID required' : undefined
      case 'email':
        return !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? 'Invalid email address' : undefined
      case 'password':
        return value.length < 8 ? 'Password must be at least 8 characters' : undefined
      case 'confirmPassword':
        return value !== formData.password ? 'Passwords do not match' : undefined
      default:
        return undefined
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))

    if (touched[name]) {
      const error = validateField(name, value)
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }))
    }
  }

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setTouched((prev) => ({ ...prev, [name]: true }))
    const error = validateField(name, value)
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }))
  }

  const isFormValid = () => {
    const newErrors: ValidationErrors = {}
    Object.entries(formData).forEach(([key, value]) => {
      if (key !== 'role') {
        const error = validateField(key, value)
        if (error) newErrors[key as keyof ValidationErrors] = error
      }
    })
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Validate all fields
    const newErrors: ValidationErrors = {}
    Object.entries(formData).forEach(([key, value]) => {
      if (key !== 'role') {
        const error = validateField(key, value)
        if (error) newErrors[key as keyof ValidationErrors] = error
      }
    })

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      setIsLoading(false)
      return
    }

    try {
      // Simulate registration API call
      await new Promise((resolve) => setTimeout(resolve, 1500))
      onSuccess?.()
    } catch (err) {
      setErrors({ hospitalName: 'Registration failed. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.5 } },
  }

  const getFieldClassName = (fieldName: keyof ValidationErrors) => {
    const hasError = errors[fieldName]
    const hasValue = formData[fieldName as keyof RegistrationData]
    const baseClass =
      'input-glass w-full transition-all duration-300 focus:ring-2 focus:ring-teal'

    if (!touched[fieldName]) return baseClass

    if (hasError) {
      return `${baseClass} border-2 border-red-500 ring-2 ring-red-500 ring-opacity-30`
    }
    if (hasValue) {
      return `${baseClass} border-2 border-green-500 ring-2 ring-green-500 ring-opacity-30`
    }
    return baseClass
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-gradient-to-b from-navy via-navy to-[#0a1419]">
      {/* Animated background */}
      <div className="absolute inset-0 opacity-30">
        {[...Array(3)].map((_, i) => (
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

      {/* Split Screen Container */}
      <div className="relative z-10 min-h-screen flex flex-col md:flex-row overflow-hidden">
        {/* Left Side - Medical Imagery & Quote */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="hidden md:flex md:w-1/2 flex-col items-center justify-center relative p-8"
        >
          {/* Gradient overlay background */}
          <div className="absolute inset-0 bg-gradient-to-br from-teal/10 via-transparent to-transparent" />

          {/* Animated medical icons */}
          <div className="relative z-20 space-y-12 text-center max-w-md">
            {/* Icons */}
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-7xl"
            >
              🏥
            </motion.div>

            {/* Quote */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 1 }}
              className="space-y-4"
            >
              <p className="text-2xl font-light italic text-teal">
                "Data-driven healthcare starts with a single patient."
              </p>
              <p className="text-sm text-gray-400">
                Join thousands of healthcare professionals leveraging AI for better outcomes
              </p>
            </motion.div>

            {/* Stats or features */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="pt-8 space-y-4"
            >
              {[
                { icon: '✓', text: 'HIPAA Compliant' },
                { icon: '✓', text: '99.9% Uptime' },
                { icon: '✓', text: 'Real-time Analytics' },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  variants={itemVariants}
                  className="flex items-center gap-3 justify-center text-gray-300"
                >
                  <span className="text-teal text-xl font-bold">{item.icon}</span>
                  <span>{item.text}</span>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </motion.div>

        {/* Right Side - Registration Form */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="w-full md:w-1/2 flex items-center justify-center p-6 md:p-8 relative"
        >
          <GlassmorphicCard className="w-full max-w-md p-8 space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
              <h1 className="text-3xl font-bold text-white">Create Account</h1>
              <p className="text-teal text-sm">
                Join our healthcare platform
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Hospital Name */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Hospital Name
                </label>
                <input
                  type="text"
                  name="hospitalName"
                  value={formData.hospitalName}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={getFieldClassName('hospitalName')}
                  placeholder="Your hospital name"
                  required
                />
                {errors.hospitalName && touched.hospitalName && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-xs mt-1"
                  >
                    {errors.hospitalName}
                  </motion.p>
                )}
              </motion.div>

              {/* Professional ID */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Professional ID
                </label>
                <input
                  type="text"
                  name="professionalId"
                  value={formData.professionalId}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={getFieldClassName('professionalId')}
                  placeholder="e.g., MD12345"
                  required
                />
                {errors.professionalId && touched.professionalId && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-xs mt-1"
                  >
                    {errors.professionalId}
                  </motion.p>
                )}
              </motion.div>

              {/* Email */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={getFieldClassName('email')}
                  placeholder="your.email@hospital.com"
                  required
                />
                {errors.email && touched.email && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-xs mt-1"
                  >
                    {errors.email}
                  </motion.p>
                )}
              </motion.div>

              {/* Role Selector - Custom Chips */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Your Role
                </label>
                <div className="space-y-2">
                  {roles.map((roleOption) => (
                    <motion.button
                      key={roleOption.value}
                      type="button"
                      onClick={() => setFormData((prev) => ({ ...prev, role: roleOption.value }))}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`w-full px-4 py-3 rounded-lg text-left transition-all duration-300 ${
                        formData.role === roleOption.value
                          ? 'bg-teal bg-opacity-30 border-2 border-teal text-teal'
                          : 'bg-opacity-10 border-2 border-gray-600 text-gray-300 hover:border-teal hover:bg-teal hover:bg-opacity-10'
                      }`}
                    >
                      <div className="font-semibold">{roleOption.label}</div>
                      <div className="text-xs opacity-75">{roleOption.description}</div>
                    </motion.button>
                  ))}
                </div>
              </motion.div>

              {/* Password */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={getFieldClassName('password')}
                  placeholder="At least 8 characters"
                  required
                />
                {errors.password && touched.password && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-xs mt-1"
                  >
                    {errors.password}
                  </motion.p>
                )}
              </motion.div>

              {/* Confirm Password */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Confirm Password
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={getFieldClassName('confirmPassword')}
                  placeholder="Re-enter password"
                  required
                />
                {errors.confirmPassword && touched.confirmPassword && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-xs mt-1"
                  >
                    {errors.confirmPassword}
                  </motion.p>
                )}
              </motion.div>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={isLoading || !isFormValid()}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </motion.button>
            </form>

            {/* Back to Login */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="text-center pt-4 border-t border-gray-700"
            >
              <p className="text-gray-400 text-sm">
                Already have an account?{' '}
                <button
                  onClick={onBackToLogin}
                  className="text-teal font-semibold hover:text-teal hover:underline transition-colors"
                >
                  Sign In
                </button>
              </p>
            </motion.div>
          </GlassmorphicCard>
        </motion.div>
      </div>
    </div>
  )
}
