export const THEME = {
  colors: {
    primary: '#20B2AA', // Soft Teal
    secondary: '#1A2B3C', // Deep Navy
    background: '#0A1116',
    surface: 'rgba(255, 255, 255, 0.1)',
    text: {
      primary: '#FFFFFF',
      secondary: '#B3B9C4',
      muted: '#6E7681',
    },
    severity: {
      1: '#10B981', // Green
      2: '#F59E0B', // Amber
      3: '#F97316', // Orange
      4: '#EF4444', // Red
      5: '#7C3AED', // Purple
    },
    status: {
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
  },
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
}

export const SEVERITY_LABELS: Record<number, string> = {
  1: 'Minimal',
  2: 'Mild',
  3: 'Moderate',
  4: 'Severe',
  5: 'Critical',
}

export const SEVERITY_DESCRIPTIONS: Record<number, string> = {
  1: 'Routine recovery, minimal complications',
  2: 'Mild complications present',
  3: 'Moderate complications requiring close monitoring',
  4: 'Severe complications, intensive care needed',
  5: 'Critical condition, high-risk discharge',
}

export const WARD_TYPES = [
  'ICU',
  'General Ward',
  'Recovery Ward',
  'Pediatric',
  'Emergency',
]

export const ANIMATION_DURATION = {
  fast: 150,
  normal: 300,
  slow: 500,
}
