import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { DischargeSchedule, RiskDonut } from '../components/charts'
import {
  Card,
  CardSkeleton,
  EmptyState,
  ErrorBlock,
  Icon,
  KpiCard,
  KpiSkeleton,
  LiveRegion,
  RiskBadge,
  SortHeader,
  Spinner,
} from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { CASELOAD_REPORT } from '../lib/capabilities'
import { TIER_ORDER } from '../theme'

/**
 * The doctor's dashboard: their own caseload, one admission at a time.
 *
 * Everything here is built from the admissions this clinician has scored, so
 * it answers ward-round questions — who is overdue, who is not going anywhere,
 * what did I look at today. Ward occupancy and model metrics belong to the
 * analyst view and are deliberately absent.
 */

function dueLabel(days) {
  if (days < 0) return `${Math.abs(days)}d overdue`
  if (days === 0) return 'Due today'
  if (days === 1) return 'Tomorrow'
  return `In ${days} days`
}

function dueClass(days) {
  if (days <= 0) return 'due-now'
  if (days <= 2) return 'due-soon'
  return ''
}

/**
 * Sort keys for the worklist.
 *
 * Risk sorts by tier severity, not alphabetically — "Very High" belongs above
 * "Low", and a string comparison would file it under V. Everything else is a
 * plain field read.
 */
const SORT_KEYS = {
  patient: (entry) => entry.patient_ref ?? '',
  department: (entry) => entry.department ?? '',
  risk: (entry) => TIER_ORDER.indexOf(entry.risk_tier),
  los: (entry) => entry.los_days,
  due: (entry) => entry.days_remaining,
  confidence: (entry) => entry.confidence,
}

const DEFAULT_SORT = { field: 'risk', direction: 'desc' }

export default function DoctorDashboard() {
  const { user, can } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [sort, setSort] = useState(DEFAULT_SORT)
  const [department, setDepartment] = useState('all')
  const [query, setQuery] = useState('')

  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState(null)

  /**
   * The handover sheet covers the whole caseload as the server sees it, not
   * the filtered view on screen: someone who typed a patient reference into
   * the search box is looking for one row, not redefining what their ward
   * round consists of.
   */
  async function downloadReport() {
    setDownloadError(null)
    setDownloading(true)
    try {
      await api.downloadCaseloadReport()
    } catch (err) {
      setDownloadError(err)
    } finally {
      setDownloading(false)
    }
  }

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .clinicalSummary()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const worklist = data?.worklist

  const departments = useMemo(() => {
    if (!worklist) return []
    return [...new Set(worklist.map((entry) => entry.department).filter(Boolean))].sort()
  }, [worklist])

  const rows = useMemo(() => {
    if (!worklist) return []
    const needle = query.trim().toLowerCase()

    const filtered = worklist.filter((entry) => {
      if (department !== 'all' && entry.department !== department) return false
      if (!needle) return true
      return String(entry.patient_ref ?? '').toLowerCase().includes(needle)
    })

    const read = SORT_KEYS[sort.field] ?? SORT_KEYS.risk
    const sign = sort.direction === 'asc' ? 1 : -1

    // Copy first: the fetched array is state, and sort mutates in place.
    return [...filtered].sort((a, b) => {
      const left = read(a)
      const right = read(b)
      if (left === right) return 0
      if (typeof left === 'string' || typeof right === 'string') {
        return String(left).localeCompare(String(right)) * sign
      }
      return (left < right ? -1 : 1) * sign
    })
  }, [worklist, department, query, sort])

  if (loading && !data) {
    return (
      <div className="stack">
        <KpiSkeleton />
        <div className="grid grid-2">
          <CardSkeleton height={300} />
          <CardSkeleton height={300} />
        </div>
      </div>
    )
  }

  if (error) return <ErrorBlock error={error} onRetry={load} />

  const { caseload, discharge_schedule: schedule } = data
  const firstName = (user?.full_name || '').split(' ').slice(-1)[0]

  if (!caseload.patients) {
    return (
      <Card>
        <EmptyState icon="patient" title="No patients scored yet">
          Score an admission and it joins your caseload here, with an expected
          discharge date and a place in the worklist.
          <div style={{ marginTop: 14 }}>
            <Link className="btn btn-primary btn-sm" to="/patient">
              Score an admission
            </Link>
          </div>
        </EmptyState>
      </Card>
    )
  }

  const filtered = department !== 'all' || query.trim() !== ''
  // The note below used to promise "highest risk first" unconditionally, which
  // stops being true the moment anyone touches a column header.
  const resorted =
    sort.field !== DEFAULT_SORT.field || sort.direction !== DEFAULT_SORT.direction

  return (
    <div className="stack">
      <LiveRegion
        message={`Caseload loaded. ${caseload.patients} admission${
          caseload.patients === 1 ? '' : 's'
        }, ${caseload.due_within_48h} due within 48 hours.`}
      />

      <div className="row-between">
        <div className="row" style={{ gap: 8 }}>
          <span className="pill">
            {caseload.patients} admission{caseload.patients === 1 ? '' : 's'} in your caseload
          </span>
          {data.model_version && <span className="pill">model {data.model_version}</span>}
        </div>
        <div className="row" style={{ gap: 6 }}>
          {can(CASELOAD_REPORT) && (
            <button
              className="btn btn-sm"
              onClick={downloadReport}
              disabled={downloading}
              title="Download this caseload as a ward-round handover PDF"
            >
              {downloading ? <Spinner /> : <Icon name="download" size={14} />}
              {downloading ? 'Preparing…' : 'PDF report'}
            </button>
          )}
          <Link className="btn btn-sm btn-primary" to="/patient">
            <Icon name="patient" size={14} /> Score an admission
          </Link>
        </div>
      </div>

      {downloadError && <ErrorBlock error={downloadError} />}

      {/*
        The first two tiles are the ward-round numbers — who needs paperwork
        started today, and who is not going anywhere — so they lead. The tone
        is conditional on purpose: a red tile that is red every single morning
        stops being read within a week.
      */}
      <div className="grid grid-kpi">
        <KpiCard
          lead
          tone={caseload.due_within_48h > 0 ? 'critical' : undefined}
          label="Due within 48 hours"
          value={caseload.due_within_48h.toLocaleString()}
          foot="Plan the discharge paperwork"
        />
        <KpiCard
          lead
          tone={caseload.high_risk > 0 ? 'warn' : undefined}
          label="High-risk patients"
          value={caseload.high_risk.toLocaleString()}
          foot={`${((caseload.high_risk / caseload.patients) * 100).toFixed(0)}% of your caseload`}
        />
        <KpiCard
          label="Average stay"
          value={caseload.avg_los_days}
          unit="days"
          foot={`Longest ${caseload.longest_los_days} days`}
        />
        <KpiCard
          label="Scored today"
          value={caseload.scored_today.toLocaleString()}
          foot={`Model confidence ${(caseload.avg_confidence * 100).toFixed(1)}%`}
        />
      </div>

      <div className="grid grid-2">
        <Card
          title="Expected discharges"
          note="Next 14 days, from each patient's predicted stay"
        >
          {schedule?.length ? (
            <DischargeSchedule data={schedule} />
          ) : (
            <EmptyState icon="chart" title="Nothing scheduled" />
          )}
        </Card>

        <Card title="Your caseload by risk" note="Share of patients in each tier">
          <RiskDonut data={data.risk_distribution} total={caseload.patients} />
        </Card>
      </div>

      <Card
        title="Discharge worklist"
        note={
          filtered
            ? `${rows.length} of ${worklist.length} shown`
            : resorted
              ? `${rows.length} admission${rows.length === 1 ? '' : 's'}`
              : `Highest risk first${firstName ? `, for Dr. ${firstName}'s round` : ''}`
        }
        action={
          <div className="table-controls">
            <div className="search-field">
              <Icon name="search" size={14} className="search-icon" />
              <input
                className="input"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Find patient"
                aria-label="Filter the worklist by patient reference"
              />
            </div>

            {departments.length > 1 && (
              <select
                className="select"
                value={department}
                onChange={(event) => setDepartment(event.target.value)}
                aria-label="Filter the worklist by department"
              >
                <option value="all">All departments</option>
                {departments.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            )}

            {filtered && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  setQuery('')
                  setDepartment('all')
                }}
              >
                <Icon name="reset" size={14} /> Clear
              </button>
            )}
          </div>
        }
      >
        {rows.length === 0 ? (
          <EmptyState icon="search" title="No admissions match those filters">
            {department === 'all'
              ? `Nothing in your caseload matches “${query.trim()}”.`
              : `Nothing in ${department} matches the current filters.`}
            <div style={{ marginTop: 14 }}>
              <button
                className="btn btn-sm"
                onClick={() => {
                  setQuery('')
                  setDepartment('all')
                }}
              >
                Clear filters
              </button>
            </div>
          </EmptyState>
        ) : (
          <div className="table-scroll">
            <table>
              <caption className="sr-only">
                Discharge worklist: {rows.length} admission
                {rows.length === 1 ? '' : 's'}. Use the column headers to sort.
              </caption>
              <thead>
                <tr>
                  <SortHeader label="Patient" field="patient" sort={sort} onSort={setSort} />
                  <SortHeader label="Department" field="department" sort={sort} onSort={setSort} />
                  <SortHeader label="Risk" field="risk" sort={sort} onSort={setSort} />
                  <SortHeader
                    label="Predicted stay"
                    field="los"
                    sort={sort}
                    onSort={setSort}
                    align="right"
                  />
                  <SortHeader
                    label="Expected discharge"
                    field="due"
                    sort={sort}
                    onSort={setSort}
                  />
                  <SortHeader
                    label="Confidence"
                    field="confidence"
                    sort={sort}
                    onSort={setSort}
                    align="right"
                  />
                </tr>
              </thead>
              <tbody>
                {rows.map((entry) => (
                  <tr
                    key={entry.id}
                    /* The urgency stripe repeats what the discharge column
                       already says in words, so the row still reads correctly
                       with the colour removed. */
                    className={
                      entry.days_remaining <= 0
                        ? 'row-overdue'
                        : entry.days_remaining <= 2
                          ? 'row-due-soon'
                          : undefined
                    }
                  >
                    <td>
                      <strong>{entry.patient_ref}</strong>
                      {entry.age != null && (
                        <span className="xs muted"> · {entry.age}y</span>
                      )}
                    </td>
                    <td className="secondary">{entry.department ?? '—'}</td>
                    <td>
                      <RiskBadge tier={entry.risk_tier} />
                    </td>
                    <td className="num tnum">{entry.los_days} d</td>
                    <td>
                      <span className={`due ${dueClass(entry.days_remaining)}`}>
                        {entry.days_remaining <= 0 && (
                          <Icon name="clock" size={12} style={{ verticalAlign: '-2px' }} />
                        )}{' '}
                        {dueLabel(entry.days_remaining)}
                      </span>
                      <span className="xs muted" style={{ display: 'block' }}>
                        {entry.expected_discharge}
                      </span>
                    </td>
                    <td className="num tnum">{(entry.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="xs muted" style={{ marginTop: 12 }}>
          <Icon name="alert" size={12} style={{ verticalAlign: '-2px' }} /> Expected
          discharge is the predicted stay counted from when the admission was
          scored. It is a planning aid, not a clinical decision.
        </p>
      </Card>
    </div>
  )
}
