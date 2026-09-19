import { useEffect, useRef, useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { loadGoogleIdentity } from '../lib/google'
import { Spinner } from './ui'

/**
 * Google's own rendered sign-in button.
 *
 * It has to be Google's button rather than one of ours: the credential is
 * only issued to a genuine GIS button, and their branding guidelines require
 * the real thing. What comes back is a signed ID token, which is forwarded
 * untouched to `onCredential` for the backend to verify -- nothing here
 * inspects or trusts it.
 */
export default function GoogleButton({
  clientId,
  onCredential,
  onError,
  text = 'signin_with',
}) {
  const host = useRef(null)
  const [status, setStatus] = useState('loading')
  const { theme } = useTheme()

  // Held in refs so a re-render with a new callback does not tear down and
  // re-render Google's button, which flickers and loses focus.
  const handlers = useRef({ onCredential, onError })
  handlers.current = { onCredential, onError }

  useEffect(() => {
    if (!clientId) return undefined
    let active = true

    loadGoogleIdentity()
      .then((google) => {
        if (!active || !host.current) return

        google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => handlers.current.onCredential?.(response.credential),
          // The One Tap prompt is deliberately not shown: an auto-appearing
          // dialog on a clinical login screen is the wrong default. The
          // button is an explicit action.
          auto_select: false,
          cancel_on_tap_outside: true,
        })

        host.current.replaceChildren()
        google.accounts.id.renderButton(host.current, {
          type: 'standard',
          theme: theme === 'dark' ? 'filled_black' : 'outline',
          size: 'large',
          text,
          shape: 'rectangular',
          logo_alignment: 'left',
          // GIS wants an explicit pixel width and caps it at 400.
          width: Math.min(Math.round(host.current.offsetWidth) || 320, 400),
        })
        setStatus('ready')
      })
      .catch((error) => {
        if (!active) return
        setStatus('error')
        handlers.current.onError?.(error)
      })

    return () => {
      active = false
    }
  }, [clientId, theme, text])

  if (!clientId) return null

  return (
    <div className="google-signin">
      <div ref={host} className="google-signin-host" />
      {status === 'loading' && (
        <div className="google-signin-fallback small secondary">
          <Spinner /> Loading Google Sign-In…
        </div>
      )}
      {status === 'error' && (
        <div className="google-signin-fallback small secondary">
          Google Sign-In is unavailable. Use an email and password below.
        </div>
      )}
    </div>
  )
}
