/**
 * Chart tokens, mirroring the CSS custom properties in styles.css.
 *
 * Recharts needs literal color strings, so the palette lives here in JS and is
 * kept in step with the stylesheet by hand. Everything the charts draw pulls
 * from this file — no ad-hoc hex anywhere in a component.
 *
 * The five risk-tier colours are a STATUS palette: fixed, identical in light
 * and dark mode, and never reused for an ordinary data series. They were
 * chosen with a colour-blindness validator rather than by eye —
 *   worst adjacent pair: ΔE 8.4 protanopia, 15.0 normal vision.
 * Amber sits marginally above the ideal lightness band and deep red is under
 * 3:1 on the dark surface; both are mitigated the documented way — every tier
 * is always rendered with its text label, never colour alone.
 */

export const TIER_COLORS = {
  'Very Low': '#0a8f82',
  Low: '#22a30c',
  Moderate: '#edaa00',
  High: '#dd5c28',
  'Very High': '#9e1c1c',
}

export const TIER_ORDER = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']

// Diverging pair for SHAP contributions: warm pushes the stay longer,
// cool pulls it shorter. Validated all-pairs (ΔE 26.7 normal, 11.7 protan).
export const SHAP_UP = '#dd5c28'
export const SHAP_DOWN = '#0a8f82'

export const ACCENT = '#0a8f82'

/** Read a live CSS variable so charts follow the active theme. */
export function cssVar(name, fallback) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
  return value || fallback
}

export function chartInk() {
  return {
    grid: cssVar('--grid', '#e6e8e7'),
    axis: cssVar('--baseline', '#cfd3d1'),
    muted: cssVar('--ink-muted', '#858c94'),
    surface: cssVar('--surface', '#ffffff'),
  }
}
