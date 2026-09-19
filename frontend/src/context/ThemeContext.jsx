import { createContext, useContext, useEffect, useMemo, useState } from 'react'

/**
 * Theme lives above the router.
 *
 * The attribute this sets is the only thing that switches the palette
 * (styles.css keys everything off `:root[data-theme='dark']`), so it has to be
 * applied on every route. It used to live inside the app shell, which meant a
 * visitor who chose dark mode and then opened the public landing page — which
 * renders outside that shell — got a light page back.
 *
 * The *first* value is not decided here. A blocking script in index.html has
 * already resolved it and stamped the attribute before the first paint, which
 * is the only way to avoid a white flash on a dark-mode load — an effect in
 * React necessarily runs after the browser has painted. This provider reads
 * that decision back rather than repeating it; the fallback below matters only
 * if the document were rendered without that script.
 */

const ThemeContext = createContext(null)
const STORAGE_KEY = 'hrf.theme'

function initialTheme() {
  const stamped = document.documentElement.getAttribute('data-theme')
  if (stamped === 'light' || stamped === 'dark') return stamped

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    /* private browsing — fall through to the system preference */
  }
  // No stored choice: follow the operating system rather than assuming light.
  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'dark'
  return 'light'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(initialTheme)

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', theme)
    // The inline script set these as element styles; keep them in step so a
    // toggle does not leave the pre-paint ground colour behind.
    root.style.colorScheme = theme
    root.style.backgroundColor = ''
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      /* the choice just will not persist */
    }
  }, [theme])

  const value = useMemo(
    () => ({ theme, toggleTheme: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used inside <ThemeProvider>')
  return context
}
