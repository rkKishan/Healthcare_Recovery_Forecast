import { Navigate, useLocation } from 'react-router-dom'
import { Card, EmptyState } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { CASELOAD_VIEW, COHORT_VIEW } from '../lib/capabilities'

/**
 * `/dashboard` is not a page — it is the door to whichever dashboard this
 * account actually has.
 *
 * The two roles get genuinely different products at their own URLs
 * (`/caseload` and `/cohort`), so a bookmark or a shared link always means
 * one specific view. This keeps the historical `/dashboard` path working,
 * and gives sign-in somewhere role-neutral to land.
 *
 * The choice is made on capability rather than role name, so it stays correct
 * if another role is added later. An admin holds both and lands on the
 * clinical side; the cohort view is one click away in the sidebar.
 */
export default function Dashboard() {
  const { can } = useAuth()
  const { search } = useLocation()

  // The search string is carried across so `/dashboard?dataset=7` — which is
  // what the upload page used to link to — still opens that dataset.
  if (can(CASELOAD_VIEW)) return <Navigate to={`/caseload${search}`} replace />
  if (can(COHORT_VIEW)) return <Navigate to={`/cohort${search}`} replace />

  return (
    <Card>
      <EmptyState icon="alert" title="No dashboard for this account">
        This account has no dashboard assigned. Ask an administrator to set its
        role to doctor or analyst.
      </EmptyState>
    </Card>
  )
}
