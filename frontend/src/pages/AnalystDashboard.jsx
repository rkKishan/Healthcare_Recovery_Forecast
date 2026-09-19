import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import {
  BedForecastChart,
  DepartmentBars,
  GlobalImportanceBars,
  LosHistogram,
  RiskDonut,
} from '../components/charts'
import {
  Card,
  CardSkeleton,
  EmptyState,
  ErrorBlock,
  Icon,
  KpiCard,
  KpiSkeleton,
  LiveRegion,
  Spinner,
} from '../components/ui'

const HORIZONS = [7, 14, 30]

/**
 * The analyst's dashboard: the whole cohort, not one patient.
 *
 * Every panel here answers a capacity or data-quality question -- how many
 * beds will be occupied on day 9, which departments carry the long stays,
 * whether the selected model still holds up on held-out data. The
 * per-admission view lives on the doctor's dashboard instead.
 */
export default function AnalystDashboard() {
  const [params, setParams] = useSearchParams()
  const datasetId = params.get('dataset')
  const days = Number(params.get('days') || 14)

  const [data, setData] = useState(null)
  const [importance, setImportance] = useState([])
  const [model, setModel] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState(null)

  async function downloadReport() {
    setDownloadError(null)
    setDownloading(true)
    try {
      await api.downloadCohortReport({ datasetId, days })
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
      .kpis({ datasetId, days })
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [datasetId, days])

  useEffect(load, [load])

  useEffect(() => {
    api.globalExplanation('regression').then((d) => setImportance(d.features)).catch(() => {})
    api.modelInfo().then(setModel).catch(() => {})
  }, [])

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

  const isEmpty = data?.source?.type === 'empty'
  if (isEmpty) {
    return (
      <Card>
        <EmptyState icon="chart" title="Nothing to chart yet">
          Upload an admission dataset and the KPIs, risk mix, and bed forecast
          will populate from it.
          <div style={{ marginTop: 14 }}>
            <Link className="btn btn-primary btn-sm" to="/upload">
              Upload a dataset
            </Link>
          </div>
        </EmptyState>
      </Card>
    )
  }

  const { kpis, risk_distribution: risk, bed_forecast: forecast } = data
  const peak = forecast?.length
    ? forecast.reduce((a, b) => (b.occupancy_rate > a.occupancy_rate ? b : a))
    : null

  return (
    <div className="stack">
      <LiveRegion
        message={`Cohort loaded. ${kpis.total_patients} patients, ${
          kpis.high_risk_patients
        } at high risk${peak ? `, occupancy peaking at ${(peak.occupancy_rate * 100).toFixed(0)} percent on day ${peak.day}` : ''}.`}
      />

      <div className="row-between">
        <div className="row" style={{ gap: 8 }}>
          <span className="pill">
            {data.source.type === 'dataset'
              ? data.source.filename
              : `${data.source.count} logged predictions`}
          </span>
          {model && <span className="pill">model {model.version}</span>}
        </div>
        <div className="row" style={{ gap: 4 }}>
          <span className="xs muted" style={{ marginRight: 4 }}>
            Forecast horizon
          </span>
          {HORIZONS.map((option) => (
            <button
              key={option}
              className={`btn btn-sm${option === days ? ' btn-primary' : ' btn-ghost'}`}
              onClick={() => {
                const next = new URLSearchParams(params)
                next.set('days', String(option))
                setParams(next, { replace: true })
              }}
            >
              {option}d
            </button>
          ))}

          <button
            className="btn btn-sm"
            style={{ marginLeft: 8 }}
            onClick={downloadReport}
            disabled={downloading}
            title={`Download a PDF summary of this cohort over ${days} days`}
          >
            {downloading ? <Spinner /> : <Icon name="download" size={14} />}
            {downloading ? 'Preparing…' : 'PDF report'}
          </button>
        </div>
      </div>

      {downloadError && <ErrorBlock error={downloadError} />}

      <div className="grid grid-kpi">
        <KpiCard
          label="Patients"
          value={kpis.total_patients.toLocaleString()}
          foot="In the current cohort"
        />
        <KpiCard
          label="Average LOS"
          value={kpis.avg_los_days}
          unit="days"
          foot={`Median ${kpis.median_los_days} days`}
        />
        <KpiCard
          lead
          label="High-risk patients"
          value={kpis.high_risk_patients.toLocaleString()}
          foot={`${((kpis.high_risk_patients / kpis.total_patients) * 100).toFixed(1)}% at High or Very High`}
        />
        <KpiCard
          lead
          label="Projected bed-days"
          value={kpis.total_bed_days.toLocaleString()}
          foot={`Model confidence ${(kpis.avg_confidence * 100).toFixed(1)}%`}
        />
      </div>

      <div className="grid grid-2">
        <Card
          title="Bed occupancy forecast"
          note={
            peak
              ? `Peaks at ${(peak.occupancy_rate * 100).toFixed(0)}% on day ${peak.day}${
                  forecast[0].capacity_derived ? ' · capacity auto-sized to cohort' : ''
                }`
              : undefined
          }
        >
          {forecast?.length ? (
            <BedForecastChart data={forecast} />
          ) : (
            <EmptyState icon="chart" title="No forecast available" />
          )}
        </Card>

        <Card title="Discharge-risk mix" note="Share of patients in each tier">
          <RiskDonut data={risk} total={kpis.total_patients} />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="Predicted length of stay" note="Distribution across the cohort">
          <LosHistogram data={data.los_histogram} />
        </Card>

        {data.department_breakdown?.length > 0 ? (
          <Card title="Average stay by department" note="Days, longest first">
            <DepartmentBars data={data.department_breakdown} />
          </Card>
        ) : (
          <Card title="What drives length of stay" note="Mean absolute SHAP value">
            <GlobalImportanceBars features={importance.slice(0, 8)} />
          </Card>
        )}
      </div>

      {data.department_breakdown?.length > 0 && (
        <Card
          title="What drives length of stay"
          note="Mean absolute SHAP value across the training sample"
        >
          <GlobalImportanceBars features={importance.slice(0, 10)} />
        </Card>
      )}

      {model && (
        <Card title="Model performance" note="Held-out test split">
          <div className="table-scroll">
            <table>
              <caption className="sr-only">
                Model performance on the held-out test split, by algorithm. The
                selected model is marked in the first column.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Algorithm</th>
                  <th scope="col" className="num">LOS RMSE</th>
                  <th scope="col" className="num">LOS R²</th>
                  <th scope="col" className="num">Tier accuracy</th>
                  <th scope="col" className="num">Macro F1</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(model.comparison.regression).map((name) => {
                  const reg = model.comparison.regression[name]
                  const clfName =
                    name === 'Linear Regression' ? 'Logistic Regression' : name
                  const clf = model.comparison.classification[clfName]
                  const best = name === model.regressor.algorithm
                  return (
                    <tr key={name} style={best ? { fontWeight: 600 } : undefined}>
                      <th scope="row" className="row-header">
                        {/* The linear family uses least squares for LOS and a
                            logistic link for the tier, so name both. */}
                        {name === 'Linear Regression' ? 'Linear / Logistic Regression' : name}
                        {best && (
                          <span className="pill" style={{ marginLeft: 8 }}>
                            selected
                          </span>
                        )}
                      </th>
                      <td className="num tnum">{reg.rmse.toFixed(3)}</td>
                      <td className="num tnum">{reg.r2.toFixed(4)}</td>
                      <td className="num tnum">
                        {clf ? `${(clf.accuracy * 100).toFixed(2)}%` : '—'}
                      </td>
                      <td className="num tnum">{clf ? clf.macro_f1.toFixed(3) : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
