'use client'

import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastMessage {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextType {
  addToast: (message: string, type: ToastType, duration?: number) => void
  removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined)

/**
 * Toast Provider Component - Wrap your app with this
 */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const addToast = useCallback(
    (message: string, type: ToastType = 'info', duration = 3000) => {
      const id = Math.random().toString(36).substr(2, 9)
      const toast: ToastMessage = { id, type, message, duration }

      setToasts((prev) => [...prev, toast])

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id)
        }, duration)
      }
    },
    []
  )

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

/**
 * Hook to use toast notifications
 */
export const useToast = () => {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

/**
 * Toast Container - Displays all toast messages
 */
const ToastContainer: React.FC<{
  toasts: ToastMessage[]
  onRemove: (id: string) => void
}> = ({ toasts, onRemove }) => {
  const getBackground = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'bg-green-500/90'
      case 'error':
        return 'bg-red-500/90'
      case 'warning':
        return 'bg-yellow-500/90'
      case 'info':
        return 'bg-blue-500/90'
      default:
        return 'bg-gray-500/90'
    }
  }

  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✕'
      case 'warning':
        return '⚠'
      case 'info':
        return 'ℹ'
      default:
        return '•'
    }
  }

  return (
    <div className="fixed top-6 right-6 z-50 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, x: 400, y: -20 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, x: 400 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className={`${getBackground(toast.type)} text-white px-6 py-4 rounded-lg shadow-lg backdrop-blur-md border border-white/20 mb-3 pointer-events-auto flex items-center gap-3 min-w-max max-w-md`}
          >
            <span className="text-xl font-bold">{getIcon(toast.type)}</span>
            <span className="flex-1">{toast.message}</span>
            <button
              onClick={() => onRemove(toast.id)}
              className="ml-4 hover:opacity-80 transition-opacity flex-shrink-0"
            >
              ×
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

export default ToastProvider
