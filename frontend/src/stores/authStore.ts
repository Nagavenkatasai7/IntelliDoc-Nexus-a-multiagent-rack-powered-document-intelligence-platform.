import { create } from 'zustand'
import api from '@/services/api'

interface AuthState {
  token: string | null
  user: { id: string; email: string; full_name: string | null } | null
  isAuthenticated: boolean

  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  loadFromStorage: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    const token = data.access_token
    localStorage.setItem('token', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`

    const { data: user } = await api.get('/auth/me')
    set({ token, user, isAuthenticated: true })
  },

  register: async (email, password, fullName) => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    })
    const token = data.access_token
    localStorage.setItem('token', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`

    const { data: user } = await api.get('/auth/me')
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
    set({ token: null, user: null, isAuthenticated: false })
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('token')
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      set({ token, isAuthenticated: true })
      // Fetch user profile
      api
        .get('/auth/me')
        .then(({ data }) => set({ user: data }))
        .catch(() => {
          localStorage.removeItem('token')
          delete api.defaults.headers.common['Authorization']
          set({ token: null, user: null, isAuthenticated: false })
        })
    }
  },
}))
