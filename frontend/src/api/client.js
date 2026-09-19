/**
 * Thin fetch wrapper.
 *
 * The backend returns one error shape everywhere
 * ({ error, details?, hint? }), so a single ApiError carries it to whichever
 * component is rendering, and <ErrorBlock> knows how to display it.
 */

const TOKEN_KEY = 'hrf.token'
const USER_KEY = 'hrf.user'

export class ApiError extends Error {
  constructor(message, { status, details = [], hint } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
    this.hint = hint
  }
}

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  getUser: () => {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },
  set: (token, user) => {
    try {
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } catch {
      /* private browsing — the session still works, it just won't persist */
    }
  },
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    } catch {
      /* ignore */
    }
  },
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  if (!isForm && body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(path, {
      method,
      headers,
      body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Could not reach the API server.', {
      status: 0,
      hint: 'Confirm the Flask backend is running on port 2800.',
    })
  }

  if (response.status === 204) return null

  let payload
  try {
    payload = await response.json()
  } catch {
    payload = {}
  }

  if (!response.ok) {
    if (response.status === 401 && token) {
      tokenStore.clear()
      window.dispatchEvent(new Event('hrf:unauthorized'))
    }
    throw new ApiError(payload.error || `Request failed (${response.status}).`, {
      status: response.status,
      details: payload.details || [],
      hint: payload.hint,
    })
  }

  return payload
}


/**
 * Download a generated file.
 *
 * The endpoint needs the Authorization header, so a plain <a href> cannot
 * fetch it -- the bytes come back through fetch and are handed to the browser
 * as an object URL. The server's Content-Disposition filename is honoured
 * when present so the PDF is named the same way however it was requested.
 */
async function download(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Could not reach the API server.', {
      status: 0,
      hint: 'Confirm the Flask backend is running on port 2800.',
    })
  }

  if (!response.ok) {
    // A failed download still returns the standard JSON error envelope.
    let payload = {}
    try {
      payload = await response.json()
    } catch {
      /* a non-JSON failure keeps the generic message below */
    }
    if (response.status === 401 && token) {
      tokenStore.clear()
      window.dispatchEvent(new Event('hrf:unauthorized'))
    }
    throw new ApiError(payload.error || `Could not generate the report (${response.status}).`, {
      status: response.status,
      details: payload.details || [],
      hint: payload.hint,
    })
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filenameFrom(response.headers.get('Content-Disposition')) || 'report.pdf'
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Revoking immediately can cancel the download in some browsers.
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}

function filenameFrom(disposition) {
  if (!disposition) return null
  const match = /filename="?([^";]+)"?/i.exec(disposition)
  return match ? match[1].trim() : null
}

export const api = {
  /**
   * Everything the sign-in page needs before anyone has a token: whether
   * Google is configured on this server, and which roles may be self-selected.
   * Served rather than bundled so one build works against either deployment.
   */
  authConfig: () => request('/api/auth/config'),

  login: (email, password) =>
    request('/api/auth/login', { method: 'POST', body: { email, password } }),

  register: ({ email, password, fullName, role }) =>
    request('/api/auth/register', {
      method: 'POST',
      body: { email, password, full_name: fullName, role },
    }),

  /**
   * Exchange a Google ID token for a session.
   *
   * `role` is only honoured the first time an account is seen; a returning
   * user keeps whatever role they already have, so this cannot be used to
   * change one's own permissions.
   */
  googleLogin: ({ credential, role }) =>
    request('/api/auth/google', { method: 'POST', body: { credential, role } }),

  me: () => request('/api/auth/me'),

  uploadDataset: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/api/dataset/upload', { method: 'POST', body: form, isForm: true })
  },

  listDatasets: () => request('/api/dataset'),

  predict: (patient) => request('/api/predict', { method: 'POST', body: patient }),

  predictDataset: (datasetId) =>
    request('/api/predict', { method: 'POST', body: { dataset_id: datasetId } }),

  kpis: ({ datasetId, days = 14 } = {}) => {
    const params = new URLSearchParams({ days: String(days) })
    if (datasetId) params.set('dataset_id', String(datasetId))
    return request(`/api/dashboard/kpis?${params}`)
  },

  /** The doctor's own caseload — their scored admissions, not the cohort. */
  clinicalSummary: () => request('/api/dashboard/clinical'),

  recentPredictions: (limit = 25) =>
    request(`/api/dashboard/predictions?limit=${limit}`),

  modelInfo: () => request('/api/predict/model'),

  globalExplanation: (task = 'regression') =>
    request(`/api/predict/explain/global?task=${task}`),

  schema: () => request('/api/predict/schema'),

  chatConfig: () => request('/api/chat/config'),

  /** One assistant turn. `history` is prior {role, content} pairs. */
  chat: (message, history = []) =>
    request('/api/chat', { method: 'POST', body: { message, history } }),

  /** The doctor's ward-round handover across their whole caseload. Takes no
   *  arguments: the server builds it from the caller's own prediction log. */
  downloadCaseloadReport: () => download('/api/reports/caseload.pdf'),

  downloadCohortReport: ({ datasetId, days = 14 } = {}) => {
    const params = new URLSearchParams({ days: String(days) })
    if (datasetId) params.set('dataset_id', String(datasetId))
    return download(`/api/reports/cohort.pdf?${params}`)
  },

  downloadPatientReport: (patient) =>
    download('/api/reports/patient.pdf', { method: 'POST', body: patient }),
}
