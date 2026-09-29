import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function RequireAuth() {
  const token = useAuthStore((state) => state.accessToken)
  return token ? <Outlet /> : <Navigate to="/login" replace />
}

export function RequireAdmin() {
  const user = useAuthStore((state) => state.user)
  return user?.role === 'ADMIN' ? <Outlet /> : <Navigate to="/" replace />
}

export function GuestOnly() {
  const token = useAuthStore((state) => state.accessToken)
  return token ? <Navigate to="/" replace /> : <Outlet />
}

