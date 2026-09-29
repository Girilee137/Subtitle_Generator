import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, HardDrive, KeyRound, LockKeyhole, ShieldCheck, UserRound } from 'lucide-react'
import { userApi } from '@/api/routes'
import { queryKeys } from '@/hooks/useApi'
import { useAuthStore } from '@/stores/authStore'

export function ProfilePage() {
  const user = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.setUser)
  const [name, setName] = useState(user?.name ?? '')
  const [password, setPassword] = useState('')
  const queryClient = useQueryClient()
  const quota = useQuery({
    queryKey: ['quota'],
    queryFn: userApi.quota,
    enabled: Boolean(user),
  })
  const update = useMutation({
    mutationFn: () => userApi.updateMe({ name }),
    onSuccess: (updated) => {
      setUser(updated)
      queryClient.invalidateQueries({ queryKey: queryKeys.me })
    },
  })
  const updatePassword = useMutation({
    mutationFn: () => userApi.updateMe({ password }),
    onSuccess: () => setPassword(''),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    update.mutate()
  }

  function submitPassword(event: FormEvent) {
    event.preventDefault()
    if (password.length >= 8) updatePassword.mutate()
  }

  const storageUsed = quota.data?.storage_used ?? user?.storage_used ?? 0
  const storageQuota = quota.data?.storage_quota ?? 5_000 * 1024 * 1024
  const quotaPercent = Math.min(100, (storageUsed / storageQuota) * 100)
  const initials = user?.name
    ?.split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'U'
  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }
  const joinedDate = user?.created_at ? new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' }).format(new Date(user.created_at)) : '—'

  return (
    <section className="panel-page profile-page">
      <div className="profile-heading">
        <div>
          <p className="eyebrow">Account center</p>
          <h1>Your profile</h1>
          <p className="profile-intro">Manage your identity, security, and privacy preferences.</p>
        </div>
        <span className="profile-status"><CheckCircle2 size={16} /> Account active</span>
      </div>

      <div className="profile-hero">
        <div className="profile-avatar">{initials}</div>
        <div className="profile-hero-copy">
          <h2>{user?.name || 'Your account'}</h2>
          <p>{user?.email}</p>
          <span>Member since {joinedDate}</span>
        </div>
        <div className="profile-role"><ShieldCheck size={17} /> {user?.role === 'ADMIN' ? 'Administrator' : 'Creator'}</div>
      </div>

      <div className="profile-grid">
        <div className="profile-card profile-details-card">
          <div className="card-heading"><span className="card-icon blue"><UserRound size={18} /></span><div><h2>Personal details</h2><p>Keep your account information up to date.</p></div></div>
          <form className="profile-form" onSubmit={submit}>
            <label>Display name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" /></label>
            <label>Email address<div className="readonly-field">{user?.email}<span>Verified</span></div></label>
            <button type="submit" disabled={update.isPending || !name.trim() || name === user?.name}>{update.isPending ? 'Saving…' : 'Save changes'}</button>
            {update.isSuccess && <p className="form-success">Your profile has been updated.</p>}
          </form>
        </div>

        <div className="profile-card storage-card">
          <div className="card-heading"><span className="card-icon purple"><HardDrive size={18} /></span><div><h2>Storage usage</h2><p>Your subtitle media allocation.</p></div></div>
          <div className="storage-summary"><strong>{formatBytes(storageUsed)}</strong><span>of {formatBytes(storageQuota)} used</span></div>
          <div className="storage-bar"><span style={{ width: `${quotaPercent}%` }} /></div>
          <div className="storage-meta"><span>{quotaPercent.toFixed(1)}% occupied</span><span>{formatBytes(Math.max(0, storageQuota - storageUsed))} remaining</span></div>
        </div>

        <div className="profile-card">
          <div className="card-heading"><span className="card-icon green"><LockKeyhole size={18} /></span><div><h2>Password & security</h2><p>Use a strong password you do not reuse elsewhere.</p></div></div>
          <form className="profile-form" onSubmit={submitPassword}>
            <label>New password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} placeholder="At least 8 characters" /></label>
            <button type="submit" className="secondary-action" disabled={updatePassword.isPending || password.length < 8}>{updatePassword.isPending ? 'Updating…' : 'Update password'}<KeyRound size={16} /></button>
            {updatePassword.isSuccess && <p className="form-success">Password updated successfully.</p>}
          </form>
        </div>

        <div className="profile-card privacy-card">
          <div className="card-heading"><span className="card-icon amber"><ShieldCheck size={18} /></span><div><h2>Privacy preference</h2><p>Choose how processing works for your projects.</p></div></div>
          <div className="privacy-row"><div><strong>Server processing consent</strong><span>{user?.server_processing_consent_at ? 'You have enabled server fallback processing.' : 'Not enabled yet. Your browser remains the default.'}</span></div><span className={`consent-badge ${user?.server_processing_consent_at ? 'enabled' : ''}`}>{user?.server_processing_consent_at ? 'Enabled' : 'Not enabled'}</span></div>
          <p className="privacy-note">Media processed in browser mode stays on your device unless you explicitly choose to save it.</p>
        </div>
      </div>
    </section>
  )
}
