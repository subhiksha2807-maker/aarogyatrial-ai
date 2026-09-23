import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import type { User } from './types'

type AuthValue = { user: User | null; loading: boolean; login: (username: string, password: string) => Promise<void>; logout: () => void }
const AuthContext = createContext<AuthValue | null>(null)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('aarogya_token')))
  useEffect(() => { if (!localStorage.getItem('aarogya_token')) return; api<User>('/me').then(setUser).catch(() => localStorage.removeItem('aarogya_token')).finally(() => setLoading(false)) }, [])
  const login = async (username: string, password: string) => { const result = await api<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }); localStorage.setItem('aarogya_token', result.access_token); setUser(result.user) }
  const logout = () => { localStorage.removeItem('aarogya_token'); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider missing'); return value }
