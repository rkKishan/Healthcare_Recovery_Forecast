'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/lib/store'
import { useToast } from '@/components/Toast'
import { GlassmorphicCard } from '@/components/ui'

type AuthMode = 'login' | 'register'

interface LoginPageProps {
  onSuccess?: () => void
  onRegisterClick?: () => void
}

interface RegistrationData {
  hospitalName: string
  professionalId: string
  email: string
  password: string
  confirmPassword: string
  role: 'administrator' | 'doctor' | 'analyst'
}

interface ValidationErrors {
  hospitalName?: string
  professionalId?: string
  email?: string
  password?: string
  confirmPassword?: string
}

/**
 * Page Transition Variants for smooth animations
 */
const pageVariants = {
  initial: (direction: number) => ({
    opacity: 0,
    x: direction > 0 ? 100 : -100,
    y: 20,
  }),
  animate: {
    opacity: 1,
    x: 0,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      duration: 0.4,
    },
  },
  exit: (direction: number) => ({
    opacity: 0,
    x: direction > 0 ? -100 : 100,
    y: 20,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      duration: 0.3,
    },
  }),
}

/**
 * Combined Auth Component with Login and Registration
 * Shows both login and registration forms with toggle capability
 * Perfectly centered on all screen sizes
 */
export const AuthPage: React.FC<{
  onSuccess?: () => void
  initialMode?: AuthMode
}> = ({ onSuccess, initialMode = 'login' }) => {
  const [authMode, setAuthMode] = useState<AuthMode>(initialMode)
  const [direction, setDirection] = useState(0)

  const handleModeChange = (newMode: AuthMode) => {
    setDirection(newMode === 'register' ? 1 : -1)
    setAuthMode(newMode)
  }

  return (
    <div className="relative w-full min-h-screen flex items-center justify-center bg-gradient-to-b from-navy via-navy to-[#0a1419] overflow-hidden p-4 sm:p-6">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-30">
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
        className="absolute top-20 left-10 w-64 h-64 bg-teal rounded-full filter blur-3xl opacity-5 hidden sm:block"
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
        className="absolute bottom-20 right-10 w-64 h-64 bg-teal rounded-full filter blur-3xl opacity-5 hidden sm:block"
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

      {/* Centered Form Container */}
      <div className="relative z-10 w-full max-w-md">
        <AnimatePresence mode="wait" custom={direction}>
          {authMode === 'login' && (
            <motion.div
              key="login"
              custom={direction}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <LoginPage
                onSuccess={onSuccess}
                onRegisterClick={() => handleModeChange('register')}
              />
            </motion.div>
          )}

          {authMode === 'register' && (
            <motion.div
              key="register"
              custom={direction}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <RegisterPage
                onSuccess={onSuccess}
                onBackToLogin={() => handleModeChange('login')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

/**
 * LoginPage Component - Traditional login with Hospital ID + Password
 */
export const LoginPage: React.FC<LoginPageProps> = ({
  onSuccess,
  onRegisterClick,
}) => {
  const [hospitalId, setHospitalId] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const { login } = useAuthStore()
  const { addToast } = useToast()

  // Load remembered email if available
  React.useEffect(() => {
    const remembered = localStorage.getItem('rememberedEmail')
    if (remembered) {
      setHospitalId(remembered)
      setRememberMe(true)
    }
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      if (!hospitalId.trim()) {
        throw new Error('Please enter your Hospital ID or Email')
      }
      if (!password.trim()) {
        throw new Error('Please enter your password')
      }

      await login(hospitalId, password)

      // Save remembered email
      if (rememberMe) {
        localStorage.setItem('rememberedEmail', hospitalId)
      } else {
        localStorage.removeItem('rememberedEmail')
      }

      addToast('🎉 Successfully logged in!', 'success', 2000)
      onSuccess?.()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Invalid credentials. Please try again.'
      setError(errorMessage)
      addToast(`❌ ${errorMessage}`, 'error', 3000)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <GlassmorphicCard className="w-full p-8 space-y-8">
      <motion.div
        className="text-center space-y-2"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-4xl font-bold text-white font-display">Welcome Back</h1>
        <p className="text-teal text-sm">Healthcare Recovery Forecast System</p>
      </motion.div>

      <motion.form
        onSubmit={handleLogin}
        className="space-y-5"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Hospital ID or Email
          </label>
          <input
            type="text"
            value={hospitalId}
            onChange={(e) => setHospitalId(e.target.value)}
            className="input-glass w-full"
            placeholder="Enter your hospital ID or email"
            required
            disabled={isLoading}
          />
        </div>

        <div>
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
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors disabled:opacity-50"
              disabled={isLoading}
            >
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
        </div>

        {/* Remember Me */}
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded bg-glass border border-gray-600 cursor-pointer accent-teal"
              disabled={isLoading}
            />
            <span className="text-gray-300 group-hover:text-teal transition-colors">
              Remember me
            </span>
          </label>
          <button
            type="button"
            className="text-teal hover:underline transition-colors disabled:opacity-50"
            disabled={isLoading}
          >
            Forgot Password?
          </button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500 bg-opacity-20 border border-red-500 text-red-300 px-4 py-3 rounded-lg text-sm"
          >
            {error}
          </motion.div>
        )}

        <motion.button
          type="submit"
          disabled={isLoading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
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
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-700" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-gradient-to-b from-navy via-navy to-[#0a1419] text-gray-500">
            New to platform?
          </span>
        </div>
      </div>

      {/* Register Link */}
      <motion.button
        onClick={onRegisterClick}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full px-6 py-3 bg-teal bg-opacity-10 border border-teal text-teal font-semibold rounded-lg hover:bg-opacity-20 transition-all duration-300 disabled:opacity-50"
        disabled={isLoading}
      >
        Create Account
      </motion.button>

      <motion.p
        className="text-center text-gray-400 text-xs"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        Demo Credentials: Any ID + Password (for testing)
      </motion.p>
    </GlassmorphicCard>
  )
}

/**
 * RegisterPage Component - Registration form for new users
 */
export const RegisterPage: React.FC<{
  onSuccess?: () => void
  onBackToLogin?: () => void
}> = ({ onSuccess, onBackToLogin }) => {
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

  const { register } = useAuthStore()
  const { addToast } = useToast()

  const roles: { value: RegistrationData['role']; label: string; description: string }[] = [
    { value: 'administrator', label: 'Administrator', description: 'Manage settings' },
    { value: 'doctor', label: 'Doctor', description: 'Clinical insights' },
    { value: 'analyst', label: 'Data Analyst', description: 'Analytics & reports' },
  ]

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
      setErrors((prev) => ({ ...prev, [name]: error }))
    }
  }

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setTouched((prev) => ({ ...prev, [name]: true }))
    const error = validateField(name, value)
    setErrors((prev) => ({ ...prev, [name]: error }))
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
      addToast('❌ Please fix the validation errors', 'error', 3000)
      return
    }

    try {
      // Extract registration data (excluding confirmPassword)
      const registrationData = {
        hospitalName: formData.hospitalName,
        professionalId: formData.professionalId,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      }

      // Call register function from auth store
      await register(registrationData)

      // Show success message
      addToast('🎉 Account created successfully!', 'success', 2000)
      onSuccess?.()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed. Please try again.'
      setErrors({ hospitalName: errorMessage })
      addToast(`❌ ${errorMessage}`, 'error', 3000)
    } finally {
      setIsLoading(false)
    }
  }

  const getFieldClassName = (fieldName: keyof ValidationErrors) => {
    const hasError = errors[fieldName]
    const hasValue = formData[fieldName as keyof RegistrationData]
    const baseClass =
      'input-glass w-full transition-all duration-300 focus:ring-2 focus:ring-teal disabled:opacity-50'

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
    <GlassmorphicCard className="w-full p-8 space-y-6">
      <motion.div
        className="text-center space-y-2"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold text-white font-display">Create Account</h1>
        <p className="text-teal text-sm">Join our healthcare platform</p>
      </motion.div>

      <motion.form
        onSubmit={handleSubmit}
        className="space-y-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        {/* Hospital Name */}
        <div>
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
            disabled={isLoading}
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
        </div>

        {/* Professional ID */}
        <div>
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
            disabled={isLoading}
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
        </div>

        {/* Email */}
        <div>
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
            disabled={isLoading}
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
        </div>

        {/* Role Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Your Role
          </label>
          <div className="space-y-2">
            {roles.map((roleOption) => (
              <motion.button
                key={roleOption.value}
                type="button"
                onClick={() =>
                  setFormData((prev) => ({ ...prev, role: roleOption.value }))
                }
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading}
                className={`w-full px-4 py-3 rounded-lg text-left transition-all duration-300 disabled:opacity-50 ${
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
        </div>

        {/* Password */}
        <div>
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
            disabled={isLoading}
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
        </div>

        {/* Confirm Password */}
        <div>
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
            disabled={isLoading}
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
        </div>

        {/* Submit Button */}
        <motion.button
          type="submit"
          disabled={isLoading || !isFormValid()}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
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
      </motion.form>

      {/* Back to Login */}
      <motion.div className="text-center pt-4 border-t border-gray-700">
        <p className="text-gray-400 text-sm">
          Already have an account?{' '}
          <button
            onClick={onBackToLogin}
            disabled={isLoading}
            className="text-teal font-semibold hover:underline transition-colors disabled:opacity-50"
          >
            Sign In
          </button>
        </p>
      </motion.div>
    </GlassmorphicCard>
  )
}
