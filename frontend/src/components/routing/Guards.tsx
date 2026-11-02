import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function RequireAuth() {
  const token = useAuthStore((state) => state.accessToken)
  const demoMode = useAuthStore((state) => state.demoMode)
  return token || demoMode ? <Outlet /> : <Navigate to="/login" replace />
}

export function RequireServerAuth() {
  const demoMode = useAuthStore((state) => state.demoMode)
  return demoMode ? <Navigate to="/" replace /> : <Outlet />
}

export function RequireAdmin() {
  const user = useAuthStore((state) => state.user)
  return user?.role === 'ADMIN' ? <Outlet /> : <Navigate to="/" replace />
}

export function GuestOnly() {
  const token = useAuthStore((state) => state.accessToken)
  const demoMode = useAuthStore((state) => state.demoMode)
  return token || demoMode ? <Navigate to="/" replace /> : <Outlet />
}
