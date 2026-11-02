import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogOut, Moon, Sun } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useUiStore } from '@/stores/uiStore'

export function AppLayout() {
  const user = useAuthStore((state) => state.user)
  const demoMode = useAuthStore((state) => state.demoMode)
  const clearSession = useAuthStore((state) => state.clearSession)
  const darkMode = useUiStore((state) => state.darkMode)
  const toggleTheme = useUiStore((state) => state.toggleTheme)
  const navigate = useNavigate()

  return (
    <div className={darkMode ? 'app app-dark' : 'app'}>
      <aside className="sidebar">
        <Link to="/" className="brand">
          Subtitle Platform
        </Link>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          {!demoMode && <NavLink to="/profile">Profile</NavLink>}
          {!demoMode && user?.role === 'ADMIN' && <NavLink to="/admin">Admin</NavLink>}
        </nav>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <strong>{user?.name}</strong>
            <span>{user?.email}</span>
            {demoMode && <span className="demo-label">Browser-only preview</span>}
          </div>
          <div className="topbar-actions">
            <button type="button" className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              type="button"
              className="icon-button"
              onClick={() => {
                clearSession()
                navigate('/login')
              }}
              aria-label="Sign out"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
