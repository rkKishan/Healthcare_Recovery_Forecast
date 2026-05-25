// This exports the main dashboard as the home page
'use client'

import React from 'react'
import { useAuthStore } from '@/lib/store'
import { AuthPage } from '@/components/Auth'
import DashboardLayout from './dashboard'
import { ToastProvider } from '@/components/Toast'

export default function Page() {
  const { isAuthenticated } = useAuthStore()

  return (
    <ToastProvider>
      {isAuthenticated ? <DashboardLayout /> : <AuthPage initialMode="login" />}
    </ToastProvider>
  )
}
