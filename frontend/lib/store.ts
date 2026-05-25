import { create } from 'zustand'

interface User {
  id: string
  hospitalId: string
  name: string
  email: string
  role: 'administrator' | 'doctor' | 'analyst'
  hospitalName: string
  professionalId: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (hospitalId: string, password: string) => Promise<void>
  register: (data: {
    hospitalName: string
    professionalId: string
    email: string
    password: string
    role: 'administrator' | 'doctor' | 'analyst'
  }) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (hospitalId: string, password: string) => {
    set({ isLoading: true })
    try {
      // API call to backend - replace with real endpoint
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hospitalId, password }),
      }).catch(() => {
        // Fallback mock authentication for development
        throw new Error('Backend not available')
      })

      if (!response.ok) {
        throw new Error('Invalid credentials')
      }

      const data = await response.json()
      const mockUser: User = {
        id: data.id || '1',
        hospitalId,
        name: data.name || 'Dr. Sarah Johnson',
        email: data.email || 'sarah@hospital.com',
        role: data.role || 'doctor',
        hospitalName: data.hospitalName || 'General Hospital',
        professionalId: data.professionalId || 'MD12345',
      }
      set({ user: mockUser, isAuthenticated: true })
    } catch (error) {
      // Mock fallback for development
      if (hospitalId && password) {
        const mockUser: User = {
          id: '1',
          hospitalId,
          name: 'Dr. Sarah Johnson',
          email: 'sarah@hospital.com',
          role: 'doctor',
          hospitalName: 'General Hospital',
          professionalId: 'MD12345',
        }
        set({ user: mockUser, isAuthenticated: true })
      } else {
        set({ isAuthenticated: false })
        throw error
      }
    } finally {
      set({ isLoading: false })
    }
  },

  register: async (data) => {
    set({ isLoading: true })
    try {
      // API call to backend - replace with real endpoint
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }).catch(() => {
        // Fallback mock registration for development
        throw new Error('Backend not available')
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Registration failed')
      }

      const responseData = await response.json()
      const newUser: User = {
        id: responseData.id || Math.random().toString(36).substr(2, 9),
        hospitalId: data.email,
        name: data.professionalId,
        email: data.email,
        role: data.role,
        hospitalName: data.hospitalName,
        professionalId: data.professionalId,
      }
      set({ user: newUser, isAuthenticated: true })
    } catch (error) {
      // Mock fallback for development
      const newUser: User = {
        id: Math.random().toString(36).substr(2, 9),
        hospitalId: data.email,
        name: data.professionalId,
        email: data.email,
        role: data.role,
        hospitalName: data.hospitalName,
        professionalId: data.professionalId,
      }
      set({ user: newUser, isAuthenticated: true })
    } finally {
      set({ isLoading: false })
    }
  },

  logout: () => {
    set({ user: null, isAuthenticated: false })
  },

  setUser: (user) => {
    set({ user, isAuthenticated: !!user })
  },
}))

interface DataStore {
  uploadedData: any[] | null
  predictions: any[] | null
  selectedSeverity: number | null
  selectedWard: string | null
  setUploadedData: (data: any[]) => void
  setPredictions: (predictions: any[]) => void
  setFilters: (severity: number | null, ward: string | null) => void
}

export const useDataStore = create<DataStore>((set) => ({
  uploadedData: null,
  predictions: null,
  selectedSeverity: null,
  selectedWard: null,

  setUploadedData: (data) => set({ uploadedData: data }),
  setPredictions: (predictions) => set({ predictions }),
  setFilters: (severity, ward) =>
    set({
      selectedSeverity: severity,
      selectedWard: ward,
    }),
}))
