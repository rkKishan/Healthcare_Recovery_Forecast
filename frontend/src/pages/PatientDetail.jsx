import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import { ShapBars } from '../components/charts'
import {
  Card,
  EmptyState,
  ErrorBlock,
  Icon,
  LiveRegion,
  RiskBadge,
  Spinner,
} from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { PATIENT_REPORT } from '../lib/capabilities'
import { TIER_COLORS, TIER_ORDER } from '../theme'

/**
 * Single-patient prediction, built as a what-if tool rather than a form.
 *
 * The form is driven entirely by /api/predict/schema — field names, ranges and
 * the categorical vocabulary all come from the server, so the model's input
 * contract is declared once and the UI cannot drift from it.
 */

const DEFAULT_PATIENT = {
  age: 68,
  gender: 'F',
  admission_type: 'Emergency',
  diagnosis_code: 'CIRC',
  comorbidity_count: 3,
  prior_admissions: 1,
  department: 'Cardiology',
}

/**
 * Starting points chosen to span the risk tiers, so the page is useful
 * immediately without typing a full record.
 */
const PRESETS = [
  {
    id: 'elderly-cardiac',
    label: 'Elderly emergency cardiac',
    note: '78, multiple comorbidities',
    record: {
      age: 78, gender: 'M', admission_type: 'Emergency', diagnosis_code: 'CIRC',
      comorbidity_count: 5, prior_admissions: 3, department: 'Cardiology',
    },
  },
  {
    id: 'young-elective',
    label: 'Young elective ortho',
    note: '31, planned admission',
    record: {
      age: 31, gender: 'F', admission_type: 'Elective', diagnosis_code: 'MUSC',
      comorbidity_count: 0, prior_admissions: 0, department: 'Orthopedics',
    },
  },
  {
    id: 'complex-onco',
    label: 'Complex oncology',
    note: '64, long expected stay',
    record: {
      age: 64, gender: 'F', admission_type: 'Urgent', diagnosis_code: 'ONCO',
      comorbidity_count: 4, prior_admissions: 2, department: 'Oncology',
    },
  },
  {
    id: 'respiratory',
    label: 'Respiratory admission',
    note: '55, frequent readmitter',
    record: {
      age: 55, gender: 'M', admission_type: 'Emergency', diagnosis_code: 'RESP',
      comorbidity_count: 2, prior_admissions: 6, department: 'Pulmonology',
    },
  },
]

const DEBOUNCE_MS = 450

function labelFor(name) {
  return name.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
}

/** Validate against the server's schema so the rules live in one place. */
function validate(form, schema) {
  if (!schema) return {}
  const errors = {}

  for (const field of schema.numeric) {
    const raw = form[field.name]
    if (raw === '' || raw === null || raw === undefined) {
      errors[field.name] = 'Required.'
      continue
    }
    const value = Number(raw)
    if (Number.isNaN(value)) {
      errors[field.name] = 'Must be a number.'
    } else if (field.min !== null && value < field.min) {
      errors[field.name] = `Must be at least ${field.min}.`
    } else if (field.max !== null && value > field.max) {
      errors[field.name] = `Must be at most ${field.max}.`
    }
  }

  for (const field of schema.categorical) {
    const value = form[field.name]
    if (!value) {
      errors[field.name] = 'Required.'
      continue
    }
    // An unknown category is encoded as all-zeros by the model rather than
    // rejected, so warn here instead of letting it score as a blank field.
    const known = field.categories?.length ? field.categories : field.examples
    if (known?.length && !known.includes(value)) {
      errors[field.name] = 'The model was not trained on this value.'
    }
  }

  return errors
}

/** Signed difference between two predictions, for comparison mode. */
function Delta({ current, baseline }) {
  const diff = Number((current - baseline).toFixed(2))
  if (diff === 0) return <span className="pd-delta pd-delta-flat">no change</span>
  const up = diff > 0
  return (
    <span className={`pd-delta ${up ? 'pd-delta-up' : 'pd-delta-down'}`}>
      {up ? '▲' : '▼'} {Math.abs(diff).toFixed(2)} days {up ? 'longer' : 'shorter'}
    </span>
  )
}

export default function PatientDetail() {
  const { can } = useAuth()
  const [form, setForm] = useState(DEFAULT_PATIENT)
  const [schema, setSchema] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [live, setLive] = useState(true)
  const [pinned, setPinned] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [activePreset, setActivePreset] = useState(null)

  useEffect(() => {
    api.schema().then(setSchema).catch(setError)
  }, [])

  const errors = useMemo(() => validate(form, schema), [form, schema])
  const isValid = schema && Object.keys(errors).length === 0

  const predict = useCallback(async (record) => {
    setError(null)
    setBusy(true)
    try {
      setResult(await api.predict(record))
    } catch (err) {
      setError(err)
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [])

  // Live mode: re-predict shortly after the record stops changing. The delay
  // matters — dragging a slider would otherwise fire a request per pixel.
  const latest = useRef(form)
  latest.current = form

  useEffect(() => {
    if (!live || !isValid) return
    const timer = setTimeout(() => predict(latest.current), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [form, live, isValid, predict])

  function update(field, value) {
    setActivePreset(null)
    setForm((current) => ({ ...current, [field]: value }))
  }

  function applyPreset(preset) {
    setActivePreset(preset.id)
    setForm(preset.record)
    if (!live) setResult(null)
  }

  function reset() {
    setActivePreset(null)
    setForm(DEFAULT_PATIENT)
    setPinned(null)
    if (!live) setResult(null)
  }

  async function downloadReport() {
    setDownloading(true)
    try {
      await api.downloadPatientReport(form)
    } catch (err) {
      setError(err)
    } finally {
      setDownloading(false)
    }
  }

  const numeric = schema?.numeric ?? []
  const categorical = schema?.categorical ?? []

  return (
    <div
      className="grid pd-layout"
      style={{ gridTemplateColumns: 'minmax(300px, 380px) 1fr', alignItems: 'start' }}
    >
      {/* A prediction replaces the panel on the right with no announcement of
          its own; this is the only thing that tells a screen-reader user the
          number they asked for has arrived. */}
      <LiveRegion
        message={
          result
            ? `Predicted stay ${result.los_days} days, ${result.risk_tier} risk, ${(
                result.confidence * 100
              ).toFixed(0)}% confidence.`
            : ''
        }
      />

      <div className="stack">
        <Card title="Patient record" note="Values at admission">
          <div className="pd-presets">
            <span className="xs muted" style={{ width: '100%', marginBottom: 2 }}>
              Start from an example
            </span>
            {PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className={`pd-preset${activePreset === preset.id ? ' active' : ''}`}
                onClick={() => applyPreset(preset)}
                title={preset.note}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <form
            className="stack"
            style={{ gap: 15, marginTop: 16 }}
            onSubmit={(event) => {
              event.preventDefault()
              if (isValid) predict(form)
            }}
          >
            {!schema && (
              <div className="stack" style={{ gap: 10 }}>
                {Array.from({ length: 6 }, (_, i) => (
                  <div className="skeleton" key={i} style={{ height: 58 }} />
                ))}
              </div>
            )}

            {numeric.map((field) => (
              <div className="field" key={field.name}>
                <div className="pd-field-head">
                  <label className="label" htmlFor={field.name}>
                    {labelFor(field.name)}
                  </label>
                  <input
                    id={field.name}
                    className={`input pd-number${errors[field.name] ? ' invalid' : ''}`}
                    type="number"
                    min={field.min ?? undefined}
                    max={field.max ?? undefined}
                    value={form[field.name]}
                    onChange={(e) => update(field.name, e.target.value)}
                    aria-invalid={Boolean(errors[field.name])}
                    aria-describedby={`${field.name}-hint`}
                  />
                </div>
                <input
                  className="pd-slider"
                  type="range"
                  min={field.min ?? 0}
                  max={field.max ?? 100}
                  value={Number(form[field.name]) || 0}
                  onChange={(e) => update(field.name, Number(e.target.value))}
                  aria-label={`${labelFor(field.name)} slider`}
                  tabIndex={-1}
                />
                <span className="hint" id={`${field.name}-hint`}>
                  {errors[field.name] ? (
                    <span className="pd-error">{errors[field.name]}</span>
                  ) : (
                    field.description
                  )}
                </span>
              </div>
            ))}

            {categorical.map((field) => {
              const options = field.categories?.length ? field.categories : field.examples
              return (
                <div className="field" key={field.name}>
                  <label className="label" htmlFor={field.name}>
                    {labelFor(field.name)}
                  </label>
                  <select
                    id={field.name}
                    className={`input${errors[field.name] ? ' invalid' : ''}`}
                    value={form[field.name]}
                    onChange={(e) => update(field.name, e.target.value)}
                    aria-invalid={Boolean(errors[field.name])}
                  >
                    {/* A value the model does not know still renders, so the
                        field never silently shows the wrong selection. */}
                    {!options.includes(form[field.name]) && (
                      <option value={form[field.name]}>{form[field.name]} (unknown)</option>
                    )}
                    {options.map((option) => (
                      <option value={option} key={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                  <span className="hint">
                    {errors[field.name] ? (
                      <span className="pd-error">{errors[field.name]}</span>
                    ) : (
                      field.description
                    )}
                  </span>
                </div>
              )
            })}

            <label className="pd-live">
              <input
                type="checkbox"
                checked={live}
                onChange={(e) => setLive(e.target.checked)}
              />
              <span>
                <strong>Live prediction</strong>
                <span className="xs muted" style={{ display: 'block' }}>
                  Re-score automatically as you change the record
                </span>
              </span>
            </label>

            <div className="row" style={{ gap: 8 }}>
              {!live && (
                <button className="btn btn-primary grow" type="submit" disabled={busy || !isValid}>
                  {busy ? (
                    <>
                      <Spinner /> Predicting…
                    </>
                  ) : (
                    'Predict recovery'
                  )}
                </button>
              )}
              <button
                className={`btn${live ? ' grow' : ''}`}
                type="button"
                onClick={reset}
                title="Restore the default record"
              >
                <Icon name="reset" size={14} /> Reset
              </button>
            </div>
          </form>
        </Card>
      </div>

      <div className="stack">
        {error && <ErrorBlock error={error} />}

        {!result && !error && (
          <Card>
            <EmptyState icon="patient" title="No prediction yet">
              Pick an example or fill in the admission record. You will get a
              length-of-stay estimate, a discharge-risk tier, and the factors
              behind both.
            </EmptyState>
          </Card>
        )}

        {result && (
          <>
            <Card>
              <div className="row-between" style={{ alignItems: 'flex-start' }}>
                <div>
                  <span className="kpi-label">Predicted length of stay</span>
                  <div style={{ marginTop: 4 }}>
                    <span
                      className="tnum"
                      style={{ fontSize: '2.5rem', fontWeight: 620, letterSpacing: '-0.03em' }}
                    >
                      {result.los_days}
                    </span>
                    <span className="kpi-unit" style={{ fontSize: '1rem' }}>
                      days
                    </span>
                    {busy && <span className="pd-refreshing"><Spinner /></span>}
                  </div>
                  <p className="small secondary" style={{ marginTop: 2 }}>
                    Estimated discharge {result.estimated_discharge}
                  </p>
                  {pinned && (
                    <p style={{ marginTop: 8 }}>
                      <Delta current={result.los_days} baseline={pinned.result.los_days} />
                      <span className="xs muted"> vs pinned</span>
                    </p>
                  )}
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span className="kpi-label">Discharge risk</span>
                  <div style={{ marginTop: 8 }}>
                    <RiskBadge tier={result.risk_tier} size="lg" />
                  </div>
                  <p className="xs muted" style={{ marginTop: 6 }}>
                    {(result.confidence * 100).toFixed(1)}% confidence · {result.latency_ms} ms
                  </p>
                </div>
              </div>

              <p className="narrative" style={{ marginTop: 16 }}>
                {result.guidance}
              </p>

              <div className="row" style={{ gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                <button
                  className="btn btn-sm"
                  onClick={() => setPinned({ record: form, result })}
                  title="Keep this prediction as a baseline to compare against"
                >
                  <Icon name="compare" size={14} />
                  {pinned ? 'Replace pinned' : 'Pin for comparison'}
                </button>
                {pinned && (
                  <button className="btn btn-sm btn-ghost" onClick={() => setPinned(null)}>
                    Clear pin
                  </button>
                )}
                {/* The clinical report is a doctor's document; an account
                    without that capability would only get a 403. */}
                {can(PATIENT_REPORT) && (
                  <button
                    className="btn btn-sm"
                    onClick={downloadReport}
                    disabled={downloading || !isValid}
                    style={{ marginLeft: 'auto' }}
                  >
                    {downloading ? <Spinner /> : <Icon name="download" size={14} />}
                    {downloading ? 'Preparing…' : 'PDF report'}
                  </button>
                )}
              </div>
            </Card>

            {pinned && (
              <Card title="Comparison" note="Pinned record against the current one">
                <div className="pd-compare">
                  <div className="pd-compare-col">
                    <span className="kpi-label">Pinned</span>
                    <div className="pd-compare-value tnum">{pinned.result.los_days}<span className="kpi-unit"> days</span></div>
                    <RiskBadge tier={pinned.result.risk_tier} />
                  </div>
                  <div className="pd-compare-arrow"><Icon name="arrow-right" size={18} /></div>
                  <div className="pd-compare-col">
                    <span className="kpi-label">Current</span>
                    <div className="pd-compare-value tnum">{result.los_days}<span className="kpi-unit"> days</span></div>
                    <RiskBadge tier={result.risk_tier} />
                  </div>
                </div>

                <table className="pd-diff">
                  <caption className="sr-only">
                    Fields that differ between the pinned baseline and the
                    current record.
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Field</th>
                      <th scope="col">Pinned</th>
                      <th scope="col">Current</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(form)
                      .filter((key) => String(pinned.record[key]) !== String(form[key]))
                      .map((key) => (
                        <tr key={key}>
                          <td>{labelFor(key)}</td>
                          <td className="muted">{String(pinned.record[key])}</td>
                          <td><strong>{String(form[key])}</strong></td>
                        </tr>
                      ))}
                    {Object.keys(form).every(
                      (key) => String(pinned.record[key]) === String(form[key]),
                    ) && (
                      <tr>
                        <td colSpan={3} className="muted">
                          The records are identical — change a field to see its effect.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </Card>
            )}

            <Card title="Tier probabilities" note="How certain the classifier is">
              {TIER_ORDER.map((tier) => {
                const probability = result.tier_probabilities[tier] ?? 0
                return (
                  <div className="shap-row" key={tier}>
                    <span className="shap-label">{tier}</span>
                    <div className="shap-track">
                      <span
                        className="shap-bar"
                        style={{
                          left: 0,
                          width: `${Math.max(probability * 100, probability > 0 ? 1 : 0)}%`,
                          background: TIER_COLORS[tier],
                          opacity: tier === result.risk_tier ? 1 : 0.42,
                        }}
                      />
                    </div>
                    <span className="shap-value">{(probability * 100).toFixed(1)}%</span>
                  </div>
                )
              })}
            </Card>

            <Card
              title="Why this prediction"
              note="SHAP contributions to the length-of-stay estimate"
            >
              <p className="narrative" style={{ marginBottom: 14 }}>
                {result.shap_values.narrative}
              </p>
              <ShapBars features={result.shap_values.top_features} unit="days" />
              <p className="xs muted" style={{ marginTop: 12 }}>
                <Icon name="alert" size={12} style={{ verticalAlign: '-2px' }} /> Baseline
                for an average patient is {result.shap_values.base_value.toFixed(2)} days;
                the factors above adjust that figure to {result.los_days} days.
              </p>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
