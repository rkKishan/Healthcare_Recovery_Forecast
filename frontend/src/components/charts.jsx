/**
 * Chart layer.
 *
 * Conventions held across every chart here:
 *   - recessive grid and axes, thin marks, tabular figures on values
 *   - a hover tooltip on every plot
 *   - a legend whenever two or more things share a plot; a single series is
 *     named by the card title instead
 *   - one y-axis, never two
 *   - colour comes from theme.js, never inline hex
 */

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ACCENT, SHAP_DOWN, SHAP_UP, TIER_COLORS, TIER_ORDER, chartInk } from '../theme'

const AXIS_FONT = 11

function axisProps(ink) {
  return {
    stroke: ink.axis,
    tick: { fill: ink.muted, fontSize: AXIS_FONT },
    tickLine: false,
    axisLine: { stroke: ink.axis },
  }
}

function TooltipShell({ label, rows }) {
  return (
    <div className="tooltip">
      {label && <div className="tooltip-label">{label}</div>}
      {rows.map((row, i) => (
        <div className="tooltip-row" key={i}>
          {row.color && (
            <span className="legend-swatch" style={{ background: row.color }} />
          )}
          <span>{row.name}</span>
          <b style={{ marginLeft: 'auto' }}>{row.value}</b>
        </div>
      ))}
    </div>
  )
}

/* ---------- risk tier distribution -------------------------------------- */

export function RiskDonut({ data, total }) {
  const ink = chartInk()
  const present = data.filter((d) => d.count > 0)

  if (!present.length) return null

  return (
    <div>
      <div style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={present}
              dataKey="count"
              nameKey="tier"
              innerRadius="58%"
              outerRadius="86%"
              startAngle={90}
              endAngle={-270}
              paddingAngle={1.5}
              isAnimationActive={false}
              stroke={ink.surface}
              strokeWidth={2}
            >
              {present.map((entry) => (
                <Cell key={entry.tier} fill={TIER_COLORS[entry.tier]} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) =>
                active && payload?.length ? (
                  <TooltipShell
                    label={payload[0].payload.tier}
                    rows={[
                      {
                        name: 'Patients',
                        value: `${payload[0].payload.count.toLocaleString()} (${payload[0].payload.percentage}%)`,
                        color: TIER_COLORS[payload[0].payload.tier],
                      },
                    ]}
                  />
                ) : null
              }
            />
          </PieChart>
        </ResponsiveContainer>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'grid',
            placeContent: 'center',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <div style={{ fontSize: '1.5rem', fontWeight: 620, letterSpacing: '-0.02em' }}>
            {total.toLocaleString()}
          </div>
          <div className="xs muted">patients</div>
        </div>
      </div>

      {/* Legend doubles as the table view: identity is never colour alone. */}
      <div className="legend">
        {TIER_ORDER.map((tier) => {
          const row = data.find((d) => d.tier === tier)
          if (!row) return null
          return (
            <span className="legend-item" key={tier}>
              <span className="legend-swatch" style={{ background: TIER_COLORS[tier] }} />
              {tier}
              <b className="tnum" style={{ color: 'var(--ink)' }}>
                {row.percentage}%
              </b>
            </span>
          )
        })}
      </div>
    </div>
  )
}

/* ---------- bed occupancy forecast --------------------------------------- */

export function BedForecastChart({ data }) {
  const ink = chartInk()
  if (!data?.length) return null

  const capacity = data[0].capacity
  const peak = Math.max(...data.map((d) => d.occupied_beds), capacity)

  return (
    <div>
      <ResponsiveContainer width="100%" height={258}>
        <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -8 }}>
          <defs>
            <linearGradient id="occupancyFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT} stopOpacity={0.22} />
              <stop offset="100%" stopColor={ACCENT} stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="day"
            {...axisProps(ink)}
            tickFormatter={(d) => `D${d}`}
            interval="preserveStartEnd"
            minTickGap={18}
          />
          <YAxis
            {...axisProps(ink)}
            domain={[0, Math.ceil((peak * 1.08) / 50) * 50]}
            width={46}
          />

          <ReferenceLine
            y={capacity}
            stroke={ink.muted}
            strokeDasharray="4 4"
            strokeWidth={1}
            label={{
              value: `Capacity ${capacity.toLocaleString()}`,
              position: 'insideTopRight',
              fill: ink.muted,
              fontSize: AXIS_FONT,
            }}
          />

          <Area
            isAnimationActive={false}
            type="monotone"
            dataKey="occupied_beds"
            stroke={ACCENT}
            strokeWidth={2}
            fill="url(#occupancyFill)"
            dot={false}
            activeDot={{ r: 4.5, strokeWidth: 2, stroke: ink.surface }}
            name="Occupied beds"
          />

          <Tooltip
            cursor={{ stroke: ink.axis, strokeWidth: 1 }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <TooltipShell
                  label={`Day ${d.day} · ${d.date}`}
                  rows={[
                    { name: 'Occupied', value: d.occupied_beds.toLocaleString(), color: ACCENT },
                    { name: 'Available', value: d.available_beds.toLocaleString() },
                    { name: 'Occupancy', value: `${(d.occupancy_rate * 100).toFixed(1)}%` },
                    { name: 'Discharges', value: d.projected_discharges.toLocaleString() },
                    { name: 'Admissions', value: d.projected_admissions.toLocaleString() },
                  ]}
                />
              )
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ---------- length-of-stay histogram ------------------------------------- */

export function LosHistogram({ data }) {
  const ink = chartInk()
  if (!data?.length) return null

  return (
    <ResponsiveContainer width="100%" height={210}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -12 }} barCategoryGap={2}>
        <XAxis dataKey="range" {...axisProps(ink)} interval={1} />
        <YAxis {...axisProps(ink)} width={44} />
        <Bar dataKey="count" isAnimationActive={false} fill={ACCENT} radius={[4, 4, 0, 0]} name="Patients" />
        <Tooltip
          cursor={{ fill: 'var(--surface-hover)' }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipShell
                label={`${payload[0].payload.range} days`}
                rows={[
                  {
                    name: 'Patients',
                    value: payload[0].payload.count.toLocaleString(),
                    color: ACCENT,
                  },
                ]}
              />
            ) : null
          }
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ---------- department breakdown ----------------------------------------- */

export function DepartmentBars({ data }) {
  const ink = chartInk()
  if (!data?.length) return null

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 34)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 40, bottom: 4, left: 4 }}
        barCategoryGap={4}
      >
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="department"
          {...axisProps(ink)}
          width={132}
          axisLine={false}
        />
        <Bar dataKey="avg_los_days" isAnimationActive={false} fill={ACCENT} radius={[0, 4, 4, 0]} name="Avg LOS">
          {data.map((entry) => (
            <Cell key={entry.department} />
          ))}
        </Bar>
        <Tooltip
          cursor={{ fill: 'var(--surface-hover)' }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipShell
                label={payload[0].payload.department}
                rows={[
                  { name: 'Avg LOS', value: `${payload[0].payload.avg_los_days} days`, color: ACCENT },
                  { name: 'Patients', value: payload[0].payload.patients.toLocaleString() },
                ]}
              />
            ) : null
          }
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ---------- expected discharges (doctor caseload) ------------------------ */

/**
 * Expected discharges per day across the planning horizon.
 *
 * Day 0 is deliberately a different colour and label: it holds both today's
 * discharges and any stay that has already run past its predicted date, which
 * is the bar a clinician acts on first.
 */
export function DischargeSchedule({ data }) {
  const ink = chartInk()
  if (!data?.length) return null

  return (
    <ResponsiveContainer width="100%" height={210}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -12 }} barCategoryGap={3}>
        <XAxis
          dataKey="day"
          {...axisProps(ink)}
          tickFormatter={(day) => (day === 0 ? 'Now' : `+${day}`)}
        />
        <YAxis {...axisProps(ink)} width={44} allowDecimals={false} />
        <Bar dataKey="patients" isAnimationActive={false} radius={[4, 4, 0, 0]} name="Patients">
          {data.map((entry) => (
            <Cell
              key={entry.day}
              fill={entry.day === 0 ? TIER_COLORS.High : ACCENT}
            />
          ))}
        </Bar>
        <Tooltip
          cursor={{ fill: 'var(--surface-hover)' }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipShell
                label={`${payload[0].payload.label} — ${payload[0].payload.date}`}
                rows={[
                  {
                    name: 'Expected discharges',
                    value: payload[0].payload.patients.toLocaleString(),
                    color: payload[0].payload.day === 0 ? TIER_COLORS.High : ACCENT,
                  },
                ]}
              />
            ) : null
          }
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ---------- SHAP contributions -------------------------------------------- */

/**
 * Diverging contribution bars, drawn in plain HTML rather than Recharts so
 * each row can carry its own readable label and signed value.
 *
 * Direction is encoded by side-of-axis as well as by hue, so the chart still
 * reads correctly without colour.
 */
export function ShapBars({ features, unit = 'days' }) {
  if (!features?.length) return null

  const max = Math.max(...features.map((f) => Math.abs(f.shap_value)), 0.001)

  return (
    <div>
      {features.map((feature) => {
        const share = (Math.abs(feature.shap_value) / max) * 50
        const positive = feature.shap_value > 0
        return (
          <div className="shap-row" key={feature.feature}>
            <span className="shap-label truncate" title={feature.label}>
              {feature.label}
            </span>
            <div className="shap-track">
              <span className="shap-axis" />
              <span
                className="shap-bar"
                style={{
                  background: positive ? SHAP_UP : SHAP_DOWN,
                  left: positive ? '50%' : `${50 - share}%`,
                  width: `${share}%`,
                }}
              />
            </div>
            <span
              className="shap-value"
              style={{ color: positive ? SHAP_UP : SHAP_DOWN }}
            >
              {feature.shap_value > 0 ? '+' : ''}
              {feature.shap_value.toFixed(2)}
            </span>
          </div>
        )
      })}
      <div className="legend" style={{ borderTop: '1px solid var(--border)', marginTop: 8 }}>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SHAP_UP }} />
          Lengthens stay
        </span>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SHAP_DOWN }} />
          Shortens stay
        </span>
        <span className="legend-item muted" style={{ marginLeft: 'auto' }}>
          {unit === 'days' ? 'Values in days' : 'Values in log-odds'}
        </span>
      </div>
    </div>
  )
}

/* ---------- global importance -------------------------------------------- */

export function GlobalImportanceBars({ features }) {
  if (!features?.length) return null
  const max = Math.max(...features.map((f) => f.importance), 0.001)

  return (
    <div>
      {features.map((feature) => (
        <div className="shap-row" key={feature.feature} style={{ gridTemplateColumns: 'minmax(120px, 1.1fr) 2fr minmax(48px, auto)' }}>
          <span className="shap-label truncate" title={feature.label}>
            {feature.label}
          </span>
          <div className="shap-track">
            <span
              className="shap-bar"
              style={{
                background: ACCENT,
                left: 0,
                width: `${(feature.importance / max) * 100}%`,
              }}
            />
          </div>
          <span className="shap-value">{feature.importance.toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}
