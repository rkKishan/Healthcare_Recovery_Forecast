"""
PDF report endpoints — one per job.

  * `cohort.pdf`   -- the analyst's capacity summary, plus the held-out model
                      metrics they are the ones expected to keep an eye on.
  * `caseload.pdf` -- the doctor's ward-round handover across their own
                      admissions, led by what has run past its discharge date.
  * `patient.pdf`  -- one admission, printable for a patient file.

Every report is generated from the same data the UI renders, so a downloaded
PDF and the screen it came from can never disagree. Nothing is written to
disk: the bytes go straight to the response, which keeps patient data out of
temp files.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from flask import Blueprint, Response, g, request

from ..auth import require_capability, requires_auth, requires_capability
from ..errors import ApiError
from ..roles import (
    CASELOAD_REPORT,
    COHORT_REPORT,
    MODEL_INSPECT,
    PATIENT_REPORT,
    has_capability,
)
from .dashboard_routes import build_clinical_summary, build_kpis
from .predict_routes import validate_record

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _pdf_response(payload: bytes, filename: str) -> Response:
    response = Response(payload, mimetype="application/pdf")
    # `filename` is built from a slug below, never straight from user input --
    # a quote or newline here would let a caller forge extra headers.
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"] = str(len(payload))
    # A report is a snapshot of mutable data; a cached copy would go stale.
    response.headers["Cache-Control"] = "no-store"
    return response


def _slug(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip()).strip("-")
    return (cleaned or fallback)[:64]


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M")


@bp.get("/cohort.pdf")
@requires_auth
def cohort_pdf():
    """Dataset-wide capacity summary, matching the dashboard."""
    from ml.report import cohort_report

    requested = request.args.get("dataset_id")
    try:
        days = int(request.args.get("days", 14))
    except (TypeError, ValueError):
        raise ApiError("'days' must be a whole number.", 400) from None
    if not 1 <= days <= 60:
        raise ApiError("'days' must be between 1 and 60.", 400)

    # build_kpis resolves the dataset first (404 on an id the caller does not
    # own) and then enforces cohort access, so a role that cannot read cohorts
    # still cannot tell a foreign dataset id from a nonexistent one. The
    # report capability is checked afterwards, on the same principle.
    payload = build_kpis(requested, days)
    require_capability(COHORT_REPORT)

    source = payload.get("source") or {}
    name = _slug(str(source.get("filename", "")).rsplit(".", 1)[0], "cohort")

    # Held-out metrics are part of the analyst's job, so they belong in the
    # analyst's PDF -- but only for a caller who is allowed to see model
    # internals, and only if a trained model is actually loadable. Neither
    # condition failing is a reason to withhold the capacity report.
    model = None
    if has_capability(g.current_user.role, MODEL_INSPECT):
        from ml.predictor import ModelNotTrainedError, get_predictor

        try:
            model = get_predictor().model_info()
        except ModelNotTrainedError:
            model = None

    pdf = cohort_report(payload, generated_by=g.current_user.full_name, model=model)
    return _pdf_response(pdf, f"recovery-forecast-{name}-{_stamp()}.pdf")


@bp.get("/caseload.pdf")
@requires_auth
@requires_capability(CASELOAD_REPORT)
def caseload_pdf():
    """
    The signed-in clinician's own caseload, as a ward-round handover sheet.

    Unlike the cohort report there is no id to resolve and nothing to scope:
    the payload is built from this user's own prediction log, so one clinician
    cannot request another's round however the request is shaped.
    """
    from ml.report import caseload_report

    clinician = g.current_user.full_name
    payload = build_clinical_summary()

    pdf = caseload_report(payload, generated_by=clinician, clinician=clinician)
    name = _slug(clinician, "caseload")
    return _pdf_response(pdf, f"recovery-forecast-caseload-{name}-{_stamp()}.pdf")


@bp.post("/patient.pdf")
@requires_auth
@requires_capability(PATIENT_REPORT)
def patient_pdf():
    """
    Single-admission report.

    POST rather than GET: the patient record is the input, and putting a
    patient's details in a URL would leak them into logs and browser history.
    """
    from ml.predictor import ModelNotTrainedError, get_predictor
    from ml.report import patient_report

    payload = request.get_json(silent=True) or {}
    record = payload.get("patient", payload)
    if not isinstance(record, dict) or not record:
        raise ApiError(
            "A patient record is required.", 400,
            hint="POST the same record you would send to /api/predict.",
        )

    patient_ref = str(record.get("patient_id") or "").strip()[:64] or None
    cleaned = validate_record({k: v for k, v in record.items() if k != "patient_id"})

    try:
        predictor = get_predictor()
    except ModelNotTrainedError as exc:
        raise ApiError(
            str(exc), 503,
            hint="Run `python -m ml.train` to produce the model artifacts.",
        ) from exc

    prediction = predictor.predict_one(cleaned, explain=True)

    pdf = patient_report(
        cleaned, prediction,
        generated_by=g.current_user.full_name,
        patient_ref=patient_ref,
    )
    name = _slug(patient_ref or "", "patient")
    return _pdf_response(pdf, f"recovery-forecast-{name}-{_stamp()}.pdf")
