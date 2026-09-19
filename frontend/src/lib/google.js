/**
 * Google Identity Services loader.
 *
 * The library is fetched from Google rather than bundled -- it is the only
 * supported way to use it, and it has to run on Google's origin to reach the
 * session cookie. Everything it hands back is a signed ID token that the
 * backend verifies; the browser never decides who the user is.
 */

const SRC = 'https://accounts.google.com/gsi/client'

let loader = null

export function loadGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve(window.google)

  // A failed load nulls this out so a later attempt can retry rather than
  // being permanently stuck on the first rejected promise.
  if (loader) return loader

  loader = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${SRC}"]`)
    const script = existing ?? document.createElement('script')

    script.addEventListener('load', () => {
      if (window.google?.accounts?.id) resolve(window.google)
      else {
        loader = null
        reject(new Error('Google Sign-In loaded but did not initialise.'))
      }
    })
    script.addEventListener('error', () => {
      loader = null
      reject(new Error('Could not reach Google Sign-In.'))
    })

    if (!existing) {
      script.src = SRC
      script.async = true
      script.defer = true
      document.head.appendChild(script)
    }
  })

  return loader
}
