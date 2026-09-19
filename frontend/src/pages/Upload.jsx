import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import {
  Card,
  EmptyState,
  ErrorBlock,
  Icon,
  LiveRegion,
  Spinner,
} from '../components/ui'

const ACCEPTED = '.csv,.xlsx,.xls'

export default function Upload() {
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [datasets, setDatasets] = useState([])

  const loadDatasets = useCallback(() => {
    api
      .listDatasets()
      .then((data) => setDatasets(data.datasets))
      .catch(() => setDatasets([]))
  }, [])

  useEffect(loadDatasets, [loadDatasets])

  async function handleFile(file) {
    if (!file) return
    setError(null)
    setResult(null)
    setBusy(true)
    try {
      const data = await api.uploadDataset(file)
      setResult(data)
      loadDatasets()
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    handleFile(event.dataTransfer.files?.[0])
  }

  const report = result?.quality_report

  return (
    <div className="stack">
      {/* The success banner below is mounted at the same moment as its text,
          which assistive technology announces unreliably. This region is
          always present, so the sentence lands. */}
      <LiveRegion
        message={
          result
            ? `Upload accepted. ${result.filename}, ${
                report?.row_count?.toLocaleString() ?? 'unknown'
              } rows, stored as dataset ${result.dataset_id}.`
            : ''
        }
      />

      <Card
        title="Upload admission data"
        note="CSV or Excel, shaped like a SPARCS discharge extract. Validated before anything is stored."
      >
        <div
          className={`dropzone${dragging ? ' dragging' : ''}`}
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              inputRef.current?.click()
            }
          }}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <span className="dropzone-icon">
            {busy ? <Spinner /> : <Icon name="upload" size={26} />}
          </span>
          <span className="dropzone-title">
            {busy ? 'Validating…' : 'Drop a file here, or click to browse'}
          </span>
          <span className="xs muted">
            Required columns: age, gender, admission_type, diagnosis_code,
            comorbidity_count, prior_admissions, department
          </span>
          <span className="xs muted">
            Include <code>length_of_stay</code> to make the file usable for training.
          </span>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            hidden
            onChange={(e) => {
              handleFile(e.target.files?.[0])
              e.target.value = ''
            }}
          />
        </div>

        {error && (
          <div style={{ marginTop: 14 }}>
            <ErrorBlock error={error} />
          </div>
        )}
      </Card>

      {result && (
        <>
          <div className="alert alert-ok" role="status">
            <Icon name="check" size={16} style={{ marginTop: 2, flexShrink: 0 }} />
            <div className="alert-body grow">
              <div className="alert-title">{result.message}</div>
              <p className="xs" style={{ marginTop: 3 }}>
                Stored as dataset #{result.dataset_id} — {result.filename}
              </p>
            </div>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => navigate(`/cohort?dataset=${result.dataset_id}`)}
            >
              View dashboard
            </button>
          </div>

          <div className="grid grid-2">
            <Card title="Data quality">
              <dl style={{ margin: 0, display: 'grid', gap: 10 }}>
                <QualityRow label="Rows" value={report.row_count.toLocaleString()} />
                <QualityRow label="Columns detected" value={report.column_count} />
                <QualityRow
                  label="Missing values"
                  value={
                    report.total_missing_values
                      ? report.total_missing_values.toLocaleString()
                      : 'None'
                  }
                />
                <QualityRow
                  label="Usable for training"
                  value={report.usable_for_training ? 'Yes' : 'No — no target column'}
                />
              </dl>

              {report.warnings?.length > 0 && (
                <div className="alert alert-warn" style={{ marginTop: 14 }}>
                  <Icon name="alert" size={15} style={{ marginTop: 2, flexShrink: 0 }} />
                  <div className="alert-body">
                    <div className="alert-title small">Worth a look</div>
                    <ul className="xs">
                      {report.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </Card>

            <Card title="Detected columns">
              <div className="row" style={{ gap: 6 }}>
                {report.detected_columns.map((column) => (
                  <span className="pill" key={column}>
                    {column}
                  </span>
                ))}
              </div>
              {report.extra_columns?.length > 0 && (
                <p className="xs muted" style={{ marginTop: 12 }}>
                  Ignored by the model: {report.extra_columns.join(', ')}
                </p>
              )}
            </Card>
          </div>

          <Card
            title="Preview"
            note={`First ${result.preview.rows.length} of ${result.preview.total_rows.toLocaleString()} rows`}
            bodyStyle={{ padding: '4px 0 0' }}
          >
            <div className="table-scroll">
              <table>
                <caption className="sr-only">
                  First {result.preview.rows.length} rows of the uploaded file.
                </caption>
                <thead>
                  <tr>
                    {result.preview.columns.map((column) => (
                      <th scope="col" key={column}>
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.preview.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td
                          key={j}
                          className={typeof cell === 'number' ? 'num tnum' : undefined}
                        >
                          {cell === null ? <span className="muted">—</span> : String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      <Card title="Your datasets" note={`${datasets.length} uploaded`}>
        {datasets.length === 0 ? (
          <EmptyState icon="file" title="No datasets yet">
            Upload a CSV or Excel file above to get started. A ready-made sample
            lives at <code>data/sample_admissions.csv</code> in the project.
          </EmptyState>
        ) : (
          <div className="table-scroll">
            <table>
              <caption className="sr-only">
                Datasets you have uploaded, newest first.
              </caption>
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col" className="num">Rows</th>
                  <th scope="col">Target</th>
                  <th scope="col">Uploaded</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.dataset_id}>
                    <td>{dataset.filename}</td>
                    <td className="num tnum">{dataset.row_count.toLocaleString()}</td>
                    <td>
                      {dataset.has_target ? (
                        <span className="pill">length_of_stay</span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td className="secondary">
                      {new Date(dataset.uploaded_at).toLocaleString()}
                    </td>
                    <td className="num">
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => navigate(`/cohort?dataset=${dataset.dataset_id}`)}
                      >
                        Analyse
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

function QualityRow({ label, value }) {
  return (
    <div className="row-between">
      <dt className="secondary small">{label}</dt>
      <dd style={{ margin: 0, fontWeight: 600 }} className="tnum">
        {value}
      </dd>
    </div>
  )
}
