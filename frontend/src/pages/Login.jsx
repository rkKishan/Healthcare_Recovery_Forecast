import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import GoogleButton from '../components/GoogleButton'
import { ErrorBlock, Icon, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useDocumentTitle } from '../lib/title'

/**
 * Sign-in, registration, and Google Sign-In on one screen.
 *
 * The role picker is what routes a new account to one of the two dashboards.
 * It is a *preference*, not a permission: the server accepts only "doctor" or
 * "analyst" from it and applies it once, when the account is created. An
 * existing account keeps the role it already has however it signs in, so
 * nothing on this page can escalate anyone.
 */

// What each demo login is for. The addresses, the password, and whether any
// exist at all come from /api/auth/config -- hard-coding them here meant this
// page offered an administrator's credentials on a deployment that had turned
// seeding off and deleted the account.
const DEMO_NOTES = {
  doctor: 'Caseload and per-patient scoring',
  analyst: 'Cohort capacity and model metrics',
  admin: 'Both dashboards',
}

const ROLE_ICONS = { doctor: 'patient', analyst: 'chart' }

export default function Login() {
  const { login, register, loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState('signin')
  const [config, setConfig] = useState(null)
  const [role, setRole] = useState('doctor')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .authConfig()
      .then((data) => {
        setConfig(data)
        if (data.default_role) setRole(data.default_role)
        // Only a deployment that actually seeds demo logins gets a filled-in
        // form; everywhere else both fields stay empty.
        const [first] = data.demo_accounts || []
        if (first && data.demo_password) {
          setEmail(first.email)
          setPassword(data.demo_password)
        }
      })
      // A server that cannot answer this still supports password login, so
      // the form stays usable; only the Google button goes missing.
      .catch(() => setConfig({ google_enabled: false, roles: [] }))
  }, [])

  const registering = mode === 'register'
  const demoAccounts = (config?.demo_password && config?.demo_accounts) || []

  useDocumentTitle(registering ? 'Create an account' : 'Sign in')

  async function onSubmit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (registering) {
        await register({ email: email.trim(), password, fullName: fullName.trim(), role })
      } else {
        await login(email.trim(), password)
      }
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  async function onGoogleCredential(credential) {
    setError(null)
    setBusy(true)
    try {
      await loginWithGoogle({ credential, role })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  function fillFromDemo(account) {
    setMode('signin')
    setEmail(account.email)
    setPassword(config?.demo_password || '')
    setError(null)
  }

  function switchMode(next) {
    setMode(next)
    setError(null)
    if (next === 'register') {
      setEmail('')
      setPassword('')
    }
  }

  const roles = config?.roles ?? []

  return (
    <div className="auth-page">
      <aside className="auth-aside">
        <div className="row" style={{ gap: 10 }}>
          <div className="brand-mark" style={{ background: 'rgba(255,255,255,0.16)' }}>
            <Icon name="pulse" size={17} />
          </div>
          <div>
            <div className="brand-name" style={{ color: '#fff' }}>
              Recovery Forecast
            </div>
            <div className="brand-sub" style={{ color: 'rgba(255,255,255,0.62)' }}>
              Bed Management System
            </div>
          </div>
        </div>

        <div>
          <h2>One model. Two very different jobs.</h2>
          <p>
            Doctors get a per-patient length-of-stay estimate with the reasoning
            behind it and a discharge worklist. Analysts get ward occupancy
            projections, cohort quality, and the numbers behind the model.
          </p>
        </div>

        <div className="auth-stats">
          <div>
            <div className="auth-stat-value">0.61 d</div>
            <div className="auth-stat-label">LOS error (RMSE)</div>
          </div>
          <div>
            <div className="auth-stat-value">91.9%</div>
            <div className="auth-stat-label">Risk-tier accuracy</div>
          </div>
          <div>
            <div className="auth-stat-value">&lt;50 ms</div>
            <div className="auth-stat-label">Per prediction</div>
          </div>
        </div>
      </aside>

      <main className="auth-panel">
        <form className="auth-form" onSubmit={onSubmit}>
          <div>
            <h1>{registering ? 'Create an account' : 'Sign in'}</h1>
            <p className="secondary" style={{ marginTop: 4 }}>
              {registering
                ? 'Pick the role that matches how you will use the system.'
                : 'Access the recovery forecasting dashboard.'}
            </p>
          </div>

          <div className="auth-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={!registering}
              className={`auth-tab${!registering ? ' active' : ''}`}
              onClick={() => switchMode('signin')}
            >
              Sign in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={registering}
              className={`auth-tab${registering ? ' active' : ''}`}
              onClick={() => switchMode('register')}
            >
              Create account
            </button>
          </div>

          <ErrorBlock error={error} />

          {/* The role choice governs which dashboard a NEW account opens on,
              whether it is created here or through Google. */}
          <div className="field">
            <label className="label">
              {registering ? 'I am a' : 'New here? Sign in as'}
            </label>
            <div className="role-picker">
              {roles.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`role-option${role === option.value ? ' active' : ''}`}
                  onClick={() => setRole(option.value)}
                  aria-pressed={role === option.value}
                >
                  <span className="role-option-head">
                    <Icon name={ROLE_ICONS[option.value] ?? 'patient'} size={15} />
                    <strong>{option.label}</strong>
                  </span>
                  <span className="role-option-note">{option.description}</span>
                </button>
              ))}
            </div>
            {!registering && (
              <span className="hint">
                Only used the first time an account is created. Existing
                accounts keep the role they already have.
              </span>
            )}
          </div>

          {config?.google_enabled && (
            <>
              <GoogleButton
                clientId={config.google_client_id}
                text={registering ? 'signup_with' : 'signin_with'}
                onCredential={onGoogleCredential}
              />
              <div className="auth-divider">
                <span>or continue with email</span>
              </div>
            </>
          )}

          {registering && (
            <div className="field">
              <label className="label" htmlFor="full_name">
                Full name
              </label>
              <input
                id="full_name"
                className="input"
                type="text"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="field">
            <label className="label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label className="label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete={registering ? 'new-password' : 'current-password'}
              minLength={registering ? 8 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {registering && <span className="hint">At least 8 characters.</span>}
          </div>

          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? (
              <>
                <Spinner /> {registering ? 'Creating account…' : 'Signing in…'}
              </>
            ) : registering ? (
              'Create account'
            ) : (
              'Sign in'
            )}
          </button>

          {demoAccounts.length > 0 && (
            <div className="demo-note">
              <div className="xs muted" style={{ marginBottom: 8 }}>
                Demo accounts — password <code>{config.demo_password}</code>
              </div>
              <div className="demo-accounts">
                {demoAccounts.map((account) => (
                  <button
                    key={account.email}
                    type="button"
                    className="demo-account"
                    onClick={() => fillFromDemo(account)}
                    title={`Fill the form with ${account.email}`}
                  >
                    <strong>{account.label}</strong>
                    <span className="xs muted">{DEMO_NOTES[account.role]}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>
      </main>
    </div>
  )
}
