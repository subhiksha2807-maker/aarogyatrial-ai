const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
export class ApiError extends Error { status: number; constructor(message: string, status: number) { super(message); this.status = status } }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('aarogya_token')
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } })
  if (!response.ok) {
    let message = 'Something went wrong. Please try again.'
    try { const payload = await response.json(); message = Array.isArray(payload.detail) ? payload.detail.map((item: { msg: string }) => item.msg).join(' ') : payload.detail || message } catch { /* fallback */ }
    if (response.status === 401 && path !== '/auth/login') localStorage.removeItem('aarogya_token')
    throw new ApiError(message, response.status)
  }
  return response.json()
}
export const formatDate = (value: string) => new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${value.slice(0, 10)}T00:00:00`))
export const formatDateTime = (value: string) => new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
