import { Component } from 'react'

/**
 * Catches render-time errors so one broken component cannot blank the whole
 * dashboard.
 *
 * Without this, a single undefined field in a chart takes down the entire
 * page: React unmounts the tree and the user is left with a white screen and
 * nothing to act on. A boundary keeps the failure local and, crucially, keeps
 * the navigation available so they can get somewhere useful.
 *
 * Error boundaries have no hook equivalent -- this has to be a class.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // Left as console output deliberately: there is no error-reporting
    // service wired up, and swallowing it silently would be worse.
    console.error('Render error:', error, info?.componentStack)
  }

  reset = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="state" style={{ padding: 32 }}>
        <div className="alert alert-error" role="alert" style={{ maxWidth: 560 }}>
          <div className="alert-body">
            <div className="alert-title">Something went wrong on this page.</div>
            <p className="xs" style={{ marginTop: 6, opacity: 0.85 }}>
              The rest of the app is still working — try again, or move to
              another page using the sidebar.
            </p>
            {import.meta.env.DEV && (
              <pre
                className="xs"
                style={{ marginTop: 10, whiteSpace: 'pre-wrap', opacity: 0.75 }}
              >
                {error.message}
              </pre>
            )}
            <button className="btn btn-sm" style={{ marginTop: 12 }} onClick={this.reset}>
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }
}
