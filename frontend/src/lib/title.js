/**
 * Per-route document titles.
 *
 * Every page used to be "Recovery Forecast", which makes browser history and a
 * row of pinned tabs useless — and it is the first thing a screen reader
 * announces after a navigation. The suffix is kept so the product is still
 * identifiable when the title is truncated to a narrow tab.
 */
import { useEffect } from 'react'

const SUFFIX = 'Recovery Forecast'

export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} · ${SUFFIX}` : SUFFIX
  }, [title])
}
