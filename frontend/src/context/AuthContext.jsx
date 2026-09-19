import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, tokenStore } from '../api/client'
import { can } from '../lib/capabilities'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStore.getUser())
  const [checking, setChecking] = useState(() => Boolean(tokenStore.get()))

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  // Confirm a persisted token is still valid before trusting the cached user.
  // This also refreshes the capability list, so a role changed server-side
  // takes effect on the next page load rather than persisting in localStorage.
  useEffect(() => {
    if (!tokenStore.get()) {
      setChecking(false)
      return
    }
    let active = true
    api
      .me()
      .then((data) => {
        if (!active) return
        tokenStore.set(tokenStore.get(), data.user)
        setUser(data.user)
      })
      .catch(() => active && logout())
      .finally(() => active && setChecking(false))
    return () => {
      active = false
    }
  }, [logout])

  // A 401 from any request anywhere drops the session.
  useEffect(() => {
    window.addEventListener('hrf:unauthorized', logout)
    return () => window.removeEventListener('hrf:unauthorized', logout)
  }, [logout])

  const adopt = useCallback((data) => {
    tokenStore.set(data.access_token, data.user)
    setUser(data.user)
    return data.user
  }, [])

  const login = useCallback(
    async (email, password) => adopt(await api.login(email, password)),
    [adopt],
  )

  const register = useCallback(
    async (details) => adopt(await api.register(details)),
    [adopt],
  )

  /**
   * `role` is a preference, not an assertion: the server applies it only when
   * this Google account has never been seen before, and ignores anything
   * outside the two clinical roles.
   */
  const loginWithGoogle = useCallback(
    async ({ credential, role }) => adopt(await api.googleLogin({ credential, role })),
    [adopt],
  )

  const value = useMemo(
    () => ({
      user,
      checking,
      login,
      register,
      loginWithGoogle,
      logout,
      // Convenience so components ask `can('cohort.view')` rather than
      // reaching into the user object and testing role names by hand.
      can: (capability) => can(user, capability),
    }),
    [user, checking, login, register, loginWithGoogle, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
