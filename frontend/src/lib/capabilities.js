/**
 * Capability names, mirroring backend/roles.py.
 *
 * The server sends the signed-in user's capability list on every auth
 * response, so nothing here decides what someone is allowed to do -- these
 * constants only let the UI ask "should I render this?" using the same
 * vocabulary the API enforces with. Hiding a control is a courtesy; the 403
 * behind it is the actual rule.
 */

export const PATIENT_PREDICT = 'patient.predict'
export const PATIENT_REPORT = 'patient.report'
export const CASELOAD_VIEW = 'caseload.view'
export const CASELOAD_REPORT = 'caseload.report'
export const DATASET_UPLOAD = 'dataset.upload'
export const COHORT_VIEW = 'cohort.view'
export const COHORT_REPORT = 'cohort.report'
export const MODEL_INSPECT = 'model.inspect'

export function can(user, capability) {
  return Boolean(user?.capabilities?.includes(capability))
}
