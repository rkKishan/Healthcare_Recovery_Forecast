import { TIER_COLORS } from '../theme'

/* ---------- icons (inline, so there is no icon-font dependency) ---------- */

const paths = {
  dashboard: 'M3 3h7v7H3zM14 3h7v4h-7zM14 11h7v10h-7zM3 14h7v7H3z',
  upload: 'M12 16V4M7 9l5-5 5 5M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2',
  patient: 'M12 11a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0',
  logout: 'M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9',
  file: 'M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9zM13 2v7h7',
  alert: 'M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L14.7 3.9a2 2 0 00-3.4 0z',
  check: 'M20 6L9 17l-5-5',
  chart: 'M3 3v18h18M8 16V10M13 16V6M18 16v-4',
  sun: 'M12 17a5 5 0 100-10 5 5 0 000 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4',
  moon: 'M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z',
  inbox: 'M22 12h-6l-2 3h-4l-2-3H2M5.5 5h13l3.5 7v6a2 2 0 01-2 2H4a2 2 0 01-2-2v-6z',
  pulse: 'M22 12h-4l-3 9L9 3l-3 9H2',
  'arrow-right': 'M5 12h14M13 6l6 6-6 6',
  download: 'M12 4v12M7 11l5 5 5-5M4 19v1a1 1 0 001 1h14a1 1 0 001-1v-1',
  compare: 'M9 3v18M15 3v18M3 8h6M15 16h6',
  reset: 'M3 12a9 9 0 109-9 9 9 0 00-6.4 2.6L3 8M3 3v5h5',
  menu: 'M3 6h18M3 12h18M3 18h18',
  close: 'M18 6L6 18M6 6l12 12',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  clock: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 7v5l3 2',
  // Both carets: the neutral "this column can be sorted" affordance.
  sort: 'M8 10l4-4 4 4M8 14l4 4 4-4',
  'sort-asc': 'M7 14l5-5 5 5',
  'sort-desc': 'M7 10l5 5 5-5',
}

export function Icon({ name, size = 16, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      <path d={paths[name]} />
    </svg>
  )
}

/* ---------- accessibility helpers --------------------------------------- */

/** Text for screen readers only. Icons are aria-hidden, so anything that is
 *  drawn as an icon alone needs one of these to have a name at all. */
export function VisuallyHidden({ children, as: Tag = 'span', ...rest }) {
  return (
    <Tag className="sr-only" {...rest}>
      {children}
    </Tag>
  )
}

/**
 * A polite live region.
 *
 * Loading a dashboard swaps a skeleton for a screenful of numbers with no
 * announcement at all — a screen-reader user is left listening to silence and
 * has to go hunting to find out whether anything arrived. Mount this once per
 * page and pass it a short sentence when the data lands.
 *
 * It is always in the tree (an aria-live region added to the DOM at the same
 * moment as its text is unreliably announced) and empty until there is
 * something to say.
 */
export function LiveRegion({ message }) {
  return (
    <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
      {message || ''}
    </div>
  )
}

/* ---------- risk badge --------------------------------------------------- */

/**
 * The tier name is always rendered beside the colour. The five-step
 * green-to-red scale cannot be made fully colourblind-safe on its own, so the
 * text label — not the hue — is what actually carries the meaning.
 */
export function RiskBadge({ tier, size }) {
  const color = TIER_COLORS[tier] || 'var(--ink-muted)'
  return (
    <span
      className={`risk-badge${size === 'lg' ? ' lg' : ''}`}
      style={{
        background: `color-mix(in srgb, ${color} 11%, var(--surface))`,
        borderColor: `color-mix(in srgb, ${color} 34%, transparent)`,
        color: `color-mix(in srgb, ${color} 82%, var(--ink))`,
      }}
    >
      <span className="risk-dot" style={{ background: color }} />
      {tier}
    </span>
  )
}

/* ---------- states ------------------------------------------------------- */

export function EmptyState({ icon = 'inbox', title, children, action }) {
  return (
    <div className="state">
      <div className="state-icon">
        <Icon name={icon} size={20} />
      </div>
      <div className="state-title">{title}</div>
      {children && <p className="state-text">{children}</p>}
      {action}
    </div>
  )
}

export function ErrorBlock({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="alert alert-error" role="alert">
      <Icon name="alert" size={16} style={{ marginTop: 2, flexShrink: 0 }} />
      <div className="alert-body grow">
        <div className="alert-title">{error.message}</div>
        {error.details?.length > 0 && (
          <ul>
            {error.details.map((detail, i) => (
              <li key={i}>{detail}</li>
            ))}
          </ul>
        )}
        {error.hint && (
          <p className="xs" style={{ marginTop: 6, opacity: 0.85 }}>
            {error.hint}
          </p>
        )}
        {onRetry && (
          <button className="btn btn-sm" style={{ marginTop: 10 }} onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

export function CardSkeleton({ height = 240 }) {
  return <div className="skeleton" style={{ height }} />
}

/** Loading placeholder shaped like the KPI row it replaces. */
export function KpiSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-kpi">
      {Array.from({ length: count }, (_, i) => (
        <div className="skeleton" key={i} style={{ height: 96 }} />
      ))}
    </div>
  )
}

export function Card({ title, note, action, children, bodyStyle }) {
  return (
    <section className="card">
      {(title || action) && (
        <header className="card-head">
          <div>
            {title && <h2 className="card-title">{title}</h2>}
            {note && <p className="card-note">{note}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="card-body" style={bodyStyle}>
        {children}
      </div>
    </section>
  )
}

/**
 * A KPI tile.
 *
 * `tone` and `lead` exist because a wall of identically-weighted cards makes
 * "3 patients overdue" look exactly as urgent as "average stay 5.2 days".
 * `lead` marks the figure a page is actually about; `tone` ('critical' |
 * 'warn') tints it, and callers are expected to pass it only when the number
 * has genuinely crossed a threshold — a permanently red tile is just wallpaper.
 *
 * The tone is never the only signal: it rides on top of a label and a footnote
 * that already say what the number means, which is what keeps it readable in
 * greyscale and for a colourblind reader.
 */
export function KpiCard({ label, value, unit, foot, tone, lead }) {
  const className = ['card', 'kpi', lead ? 'kpi-lead' : '', tone ? `kpi-${tone}` : '']
    .filter(Boolean)
    .join(' ')

  return (
    <div className={className}>
      <span className="kpi-label">{label}</span>
      <div>
        <span className="kpi-value tnum">{value}</span>
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {foot && <span className="kpi-foot">{foot}</span>}
    </div>
  )
}

/* ---------- sortable table header --------------------------------------- */

/**
 * A `<th>` that sorts the column.
 *
 * `aria-sort` goes on the header cell rather than the button, which is where
 * assistive technology looks for it, and the button carries a spoken
 * description of what activating it will do — "sort by risk, descending" —
 * because the caret alone conveys nothing without sight.
 */
export function SortHeader({ label, field, sort, onSort, align = 'left', width }) {
  const active = sort.field === field
  const direction = active ? sort.direction : null
  const next = active && direction === 'desc' ? 'asc' : 'desc'

  return (
    <th
      className={`sortable${align === 'right' ? ' num' : ''}`}
      aria-sort={active ? (direction === 'asc' ? 'ascending' : 'descending') : 'none'}
      style={width ? { width } : undefined}
    >
      <button
        type="button"
        className={`th-sort${active ? ' active' : ''}`}
        onClick={() => onSort({ field, direction: next })}
      >
        <span>{label}</span>
        <Icon
          name={active ? (direction === 'asc' ? 'sort-asc' : 'sort-desc') : 'sort'}
          size={13}
          className="th-sort-icon"
        />
        <VisuallyHidden>
          {active
            ? `, sorted ${direction === 'asc' ? 'ascending' : 'descending'}. Activate to sort ${
                next === 'asc' ? 'ascending' : 'descending'
              }.`
            : `, not sorted. Activate to sort by ${label.toLowerCase()}.`}
        </VisuallyHidden>
      </button>
    </th>
  )
}
