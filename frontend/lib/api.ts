import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for authentication
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const api = {
  // Auth endpoints
  auth: {
    login: (hospitalId: string, password: string) =>
      apiClient.post('/api/auth/login', { hospitalId, password }),
    logout: () => apiClient.post('/api/auth/logout'),
  },

  // Upload endpoints
  upload: {
    file: (file: File, hospitalId: string) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('hospital_id', hospitalId)
      return apiClient.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
  },

  // Prediction endpoints
  predictions: {
    analyze: (data: any[]) =>
      apiClient.post('/api/predict/batch', { patients: data }),
    single: (patientData: any) =>
      apiClient.post('/api/predict/single', patientData),
    explain: (patientId: string) =>
      apiClient.get(`/api/predict/explain/${patientId}`),
  },

  // Dashboard endpoints
  dashboard: {
    bedOccupancy: () => apiClient.get('/api/dashboard/bed-occupancy'),
    severityDistribution: () => apiClient.get('/api/dashboard/severity'),
    stats: () => apiClient.get('/api/dashboard/stats'),
  },

  // Report endpoints
  reports: {
    generate: (data: any) =>
      apiClient.post('/api/reports/generate', data, {
        responseType: 'blob',
      }),
  },
}

export default apiClient
