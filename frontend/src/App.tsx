import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { GuestOnly, RequireAdmin, RequireAuth } from '@/components/routing/Guards'
import { AdminPage } from '@/pages/Admin'
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from '@/pages/auth/AuthPages'
import { DashboardPage } from '@/pages/Dashboard'
import { EditorPage } from '@/pages/EditorPage'
import { ProfilePage } from '@/pages/Profile'
import { ProjectPage } from '@/pages/ProjectPage'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route element={<GuestOnly />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Route>
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="/projects/:id" element={<ProjectPage />} />
            <Route path="/tracks/:id" element={<EditorPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route element={<RequireAdmin />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
