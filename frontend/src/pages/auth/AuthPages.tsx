import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/routes'
import { useRegisterMutation } from '@/hooks/useApi'
import { useAuthStore } from '@/stores/authStore'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const setDemoSession = useAuthStore((state) => state.setDemoSession)
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    const normalizedEmail = email.trim().toLowerCase()
    const name = normalizedEmail.split('@')[0] || 'Demo user'
    setDemoSession({
      user_id: 'local-demo-user',
      name,
      email: normalizedEmail,
      role: 'USER',
      is_active: true,
      storage_used: 0,
      server_processing_consent_at: null,
      created_at: new Date().toISOString(),
    })
    navigate('/')
  }

  return (
    <AuthShell title="Sign in">
      <div className="demo-notice" role="note">
        Preview access only. Enter any valid email and a password of at least 8 characters. Nothing is sent to a
        server; this is not secure authentication.
      </div>
      <form onSubmit={submit} className="form">
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          placeholder="Email"
          autoComplete="email"
          required
        />
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          placeholder="Password"
          autoComplete="current-password"
          minLength={8}
          required
        />
        <button type="submit">Open preview</button>
      </form>
    </AuthShell>
  )
}

export function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const register = useRegisterMutation()
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    register.mutate(
      { name, email, password },
      {
        onSuccess: () => navigate('/'),
      },
    )
  }

  return (
    <AuthShell title="Create account">
      <form onSubmit={submit} className="form">
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name" />
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="Email" />
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          placeholder="Password"
        />
        {register.isError && <p className="form-error">Account could not be created.</p>}
        <button type="submit" disabled={register.isPending}>
          Create account
        </button>
      </form>
      <p className="auth-link">
        <Link to="/login">Sign in</Link>
      </p>
    </AuthShell>
  )
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    await authApi.forgotPassword(email)
    setSent(true)
  }

  return (
    <AuthShell title="Reset password">
      <form onSubmit={submit} className="form">
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="Email" />
        {sent && <p className="form-success">Reset email sent.</p>}
        <button type="submit">Send reset email</button>
      </form>
      <p className="auth-link">
        <Link to="/reset-password">Enter token</Link>
      </p>
    </AuthShell>
  )
}

export function ResetPasswordPage() {
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [done, setDone] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    await authApi.resetPassword({ token, password })
    setDone(true)
  }

  return (
    <AuthShell title="New password">
      <form onSubmit={submit} className="form">
        <input value={token} onChange={(event) => setToken(event.target.value)} placeholder="Reset token" />
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          placeholder="New password"
        />
        {done && <p className="form-success">Password updated.</p>}
        <button type="submit">Save password</button>
      </form>
    </AuthShell>
  )
}

function AuthShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main className="auth-page">
      <section className="auth-panel">
        <h1>{title}</h1>
        {children}
      </section>
    </main>
  )
}
