import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { useTheme } from './context/ThemeContext'
import { Card, EmptyState, Icon, VisuallyHidden } from './components/ui'
import Assistant from './components/Assistant'
import ErrorBoundary from './components/ErrorBoundary'
import {
  CASELOAD_VIEW,
  COHORT_VIEW,
  DATASET_UPLOAD,
  PATIENT_PREDICT,
} from './lib/capabilities'
import { useDocumentTitle } from './lib/title'
import AnalystDashboard from './pages/AnalystDashboard'
import Dashboard from './pages/Dashboard'
import DoctorDashboard from './pages/DoctorDashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import PatientDetail from './pages/PatientDetail'
import Upload from './pages/Upload'

const PAGES = {
  '/caseload': {
    title: 'My caseload',
    subtitle: 'Discharge planning across the admissions you have scored',
  },
  '/cohort': {
    title: 'Cohort analytics',
    subtitle: 'Length-of-stay forecasting and bed capacity planning',
  },
  '/upload': {
    title: 'Dataset upload',
    subtitle: 'Validate and store hospital admission extracts',
  },
  '/patient': {
    title: 'Patient detail',
    subtitle: 'Per-patient prediction with an explanation of the drivers',
  },
}

/**
 * The sidebar is built from the signed-in user's capabilities, which the API
 * sends with every auth response. Nothing here is a permission check — the
 * server enforces the same list — it is only about not showing a doctor a
 * link to a page that would 403.
 */
const NAV = [
  { to: '/caseload', icon: 'dashboard', label: 'My caseload', capability: CASELOAD_VIEW },
  { to: '/patient', icon: 'patient', label: 'Score a patient', capability: PATIENT_PREDICT },
  { to: '/cohort', icon: 'chart', label: 'Cohort analytics', capability: COHORT_VIEW },
  { to: '/upload', icon: 'upload', label: 'Upload data', capability: DATASET_UPLOAD },
]

/** Below this width the sidebar is an overlay drawer rather than a column.
 *  Kept in step with the `max-width: 1000px` block in styles.css. */
const DRAWER_QUERY = '(max-width: 1000px)'

function Shell({ children }) {
  const { user, logout, can } = useAuth()
  const { pathname } = useLocation()
  const { theme, toggleTheme } = useTheme()
  const page = PAGES[pathname] ?? {}

  const [navOpen, setNavOpen] = useState(false)
  const navRef = useRef(null)
  const toggleRef = useRef(null)

  useDocumentTitle(page.title)

  /** Close and hand focus back to the control that opened the drawer.
   *  Used for Escape and for the scrim — but not for navigation, where the
   *  user has deliberately moved on and should not be yanked backwards. */
  const closeNav = useCallback(() => {
    setNavOpen(false)
    toggleRef.current?.focus()
  }, [])

  // A route change closes the drawer: the link that was just followed is
  // inside it, and leaving it covering the page it navigated to is worse than
  // useless on a phone.
  useEffect(() => {
    setNavOpen(false)
  }, [pathname])

  // Growing past the breakpoint turns the drawer back into a static column;
  // the open state would otherwise linger and keep the scrim on screen.
  useEffect(() => {
    const mq = window.matchMedia(DRAWER_QUERY)
    const onChange = (event) => {
      if (!event.matches) setNavOpen(false)
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // While the drawer is open it is a modal surface: Tab stays inside it,
  // Escape dismisses it, and the page behind does not scroll.
  useEffect(() => {
    if (!navOpen) return undefined
    const aside = navRef.current
    if (!aside) return undefined

    const focusable = () =>
      aside.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')

    focusable()[0]?.focus()

    function onKeyDown(event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        setNavOpen(false)
        toggleRef.current?.focus()
        return
      }
      if (event.key !== 'Tab') return

      const items = focusable()
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [navOpen])

  const initials = (user?.full_name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      {/* Only ever visible under the drawer breakpoint; clicking it dismisses. */}
      <div
        className="nav-scrim"
        onClick={closeNav}
        hidden={!navOpen}
        aria-hidden="true"
      />

      <aside
        className={`sidebar${navOpen ? ' open' : ''}`}
        id="app-nav"
        ref={navRef}
        aria-label="Main"
      >
        <div className="brand">
          <div className="brand-mark">
            <Icon name="pulse" size={17} />
          </div>
          <div>
            <div className="brand-name">Recovery Forecast</div>
            <div className="brand-sub">BED MANAGEMENT</div>
          </div>
          <button
            className="btn btn-ghost btn-sm nav-close"
            onClick={closeNav}
            aria-label="Close navigation"
          >
            <Icon name="close" />
          </button>
        </div>

        <nav className="nav">
          {NAV.filter((item) => can(item.capability)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              /* The label is visible in the drawer and the column alike, but
                 the name is asserted here as well: it is the only thing
                 standing between this link and being an anonymous icon if the
                 text is ever clipped or hidden at some width. */
              aria-label={item.label}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          <button
            className="btn btn-ghost btn-sm"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
            <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>

          <div className="user-chip">
            {user?.avatar_url ? (
              <img className="avatar" src={user.avatar_url} alt="" referrerPolicy="no-referrer" />
            ) : (
              <div className="avatar">{initials}</div>
            )}
            <div className="grow truncate">
              <div className="user-name truncate">{user?.full_name}</div>
              <div className="user-role">{user?.role_label ?? user?.role}</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={logout} aria-label="Sign out">
              <Icon name="logout" />
            </button>
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            className="btn btn-ghost nav-toggle"
            ref={toggleRef}
            onClick={() => setNavOpen((open) => !open)}
            aria-expanded={navOpen}
            aria-controls="app-nav"
          >
            <Icon name="menu" size={20} />
            <VisuallyHidden>Navigation menu</VisuallyHidden>
          </button>

          <div className="page-title-group">
            <h1>{page.title ?? 'Recovery Forecast'}</h1>
            {page.subtitle && <p className="page-subtitle">{page.subtitle}</p>}
          </div>
        </header>
        {/* tabIndex -1 so the skip link can actually land focus here. */}
        <main className="content" id="main-content" tabIndex={-1}>
          {/* Keyed by route so navigating away clears a caught error. */}
          <ErrorBoundary key={pathname}>{children}</ErrorBoundary>
        </main>

        {/* Signed-in surface only -- it renders nothing when the server
            reports the assistant unconfigured. */}
        <Assistant />
      </div>
    </div>
  )
}

function RequireAuth({ children }) {
  const { user, checking } = useAuth()

  if (checking) {
    return (
      <div className="state" style={{ minHeight: '100vh' }} role="status">
        <span className="spinner" />
        <span className="small secondary">Restoring your session…</span>
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <Shell>{children}</Shell>
}

/**
 * A route the current role has no business on.
 *
 * It renders an explanation rather than redirecting: a doctor who followed a
 * colleague's link to /cohort should be told the link is not for them, not
 * silently bounced somewhere else and left wondering what happened.
 */
function RequireCapability({ capability, children }) {
  const { can, user } = useAuth()
  if (can(capability)) return children

  return (
    <Card>
      <EmptyState icon="alert" title="Not available to your role">
        This area belongs to the other side of the system. Your account is
        signed in as {user?.role_label ?? user?.role}.
        <div style={{ marginTop: 14 }}>
          <NavLink className="btn btn-primary btn-sm" to="/dashboard">
            Back to your dashboard
          </NavLink>
        </div>
      </EmptyState>
    </Card>
  )
}

function Protected({ capability, children }) {
  return (
    <RequireAuth>
      <RequireCapability capability={capability}>{children}</RequireCapability>
    </RequireAuth>
  )
}

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      {/* Public marketing route. Signed-in visitors still see it -- the CTAs
          switch to "Open dashboard" rather than bouncing them away. */}
      <Route path="/" element={<Landing />} />
      <Route
        path="/login"
        element={user ? <Navigate to="/dashboard" replace /> : <Login />}
      />

      {/* Role-neutral entry point: sends each account to the dashboard it
          actually has. */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />

      <Route
        path="/caseload"
        element={
          <Protected capability={CASELOAD_VIEW}>
            <DoctorDashboard />
          </Protected>
        }
      />
      <Route
        path="/cohort"
        element={
          <Protected capability={COHORT_VIEW}>
            <AnalystDashboard />
          </Protected>
        }
      />
      <Route
        path="/upload"
        element={
          <Protected capability={DATASET_UPLOAD}>
            <Upload />
          </Protected>
        }
      />
      <Route
        path="/patient"
        element={
          <Protected capability={PATIENT_PREDICT}>
            <PatientDetail />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
