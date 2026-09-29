import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/routes'
import { useLoginMutation, useRegisterMutation } from '@/hooks/useApi'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const login = useLoginMutation()
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    login.mutate(
      { email, password },
      {
        onSuccess: () => navigate('/'),
      },
    )
  }

  return (
    <AuthShell title="Sign in">
      <form onSubmit={submit} className="form">
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="Email" />
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          placeholder="Password"
        />
        {login.isError && <p className="form-error">Credentials were not accepted.</p>}
        <button type="submit" disabled={login.isPending}>
          Sign in
        </button>
      </form>
      <p className="auth-link">
        <Link to="/register">Create account</Link>
        <Link to="/forgot-password">Reset password</Link>
      </p>
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
