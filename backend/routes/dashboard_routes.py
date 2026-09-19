"""Aggregate dashboard statistics and the bed-occupancy forecast."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np
from flask import Blueprint, current_app, g, request

from ml.predictor import ModelNotTrainedError, get_predictor
from ml.schema import RISK_TIER_LABELS

from ..auth import require_capability, requires_auth, requires_capability
from ..errors import ApiError
from ..models import Dataset, PredictionLog
from ..roles import CASELOAD_VIEW, COHORT_VIEW
from .dataset_routes import load_dataset_frame

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

DEFAULT_FORECAST_DAYS = 14
MAX_FORECAST_DAYS = 60

# How far ahead the doctor's discharge planner looks, and how many admissions
# it will put on screen at once.
CASELOAD_HORIZON_DAYS = 14
WORKLIST_LIMIT = 25
CASELOAD_SAMPLE = 500


@bp.get("/kpis")
@requires_auth
def kpis():
    """
    Aggregate KPIs for the analytics dashboard.

    Scoped to one upload with `?dataset_id=`, otherwise the caller's most
    recent dataset. Falls back to the logged prediction history when no
    dataset is available, so the dashboard is never blank after a
    single-patient prediction.
    """
    return build_kpis(request.args.get("dataset_id"), _forecast_days())


def build_kpis(requested_dataset_id: str | None, forecast_days: int) -> dict:
    """
    Compute the dashboard payload.

    Shared with the PDF report so a downloaded summary and the dashboard it
    came from can never disagree about the same numbers.
    """
    dataset = _select_dataset(requested_dataset_id)

    # Checked here rather than on the view so that the dataset lookup above --
    # which 404s on an id the caller does not own -- happens first. A role that
    # cannot read cohorts must not be able to tell, from a 403 instead of a
    # 404, that someone else's dataset id exists.
    require_capability(COHORT_VIEW)

    if dataset is None:
        return _kpis_from_logs(forecast_days)

    try:
        predictor = get_predictor()
    except ModelNotTrainedError as exc:
        raise ApiError(
            str(exc), 503,
            hint="Run `python -m ml.train` to produce the model artifacts.",
        ) from exc

    frame = load_dataset_frame(dataset)
    predictions = predictor.predict_batch(frame)
    los = predictions["los_days"].to_numpy(dtype=float)

    tier_counts = predictions["risk_tier"].value_counts().to_dict()
    distribution = [
        {
            "tier": tier,
            "count": int(tier_counts.get(tier, 0)),
            "percentage": round(100 * tier_counts.get(tier, 0) / len(predictions), 1),
        }
        for tier in RISK_TIER_LABELS
    ]

    return {
        "source": {
            "type": "dataset",
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "uploaded_at": dataset.uploaded_at.isoformat(),
        },
        "model_version": predictor.version,
        "kpis": {
            "total_patients": int(len(predictions)),
            "avg_los_days": round(float(los.mean()), 2),
            "median_los_days": round(float(np.median(los)), 2),
            "high_risk_patients": int(
                predictions["risk_tier"].isin(["High", "Very High"]).sum()
            ),
            "avg_confidence": round(
                float(predictions["confidence"].mean()), 4
            ),
            "total_bed_days": int(round(float(los.sum()))),
        },
        "risk_distribution": distribution,
        "los_histogram": _histogram(los),
        "bed_forecast": _bed_forecast(los, forecast_days),
        "department_breakdown": _department_breakdown(frame, predictions),
    }


@bp.get("/predictions")
@requires_auth
def recent_predictions():
    """The audit log, newest first — powers the dashboard activity table."""
    limit = min(int(request.args.get("limit", 25)), 200)
    logs = (
        PredictionLog.query.filter_by(user_id=g.current_user.id)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"predictions": [log.to_dict() for log in logs]}


@bp.get("/clinical")
@requires_auth
@requires_capability(CASELOAD_VIEW)
def clinical_summary():
    """
    The doctor's view: their own caseload, not the hospital's cohort.

    Everything here is derived from the admissions this clinician has actually
    scored, so it answers ward-round questions -- who is due out, who is not
    going anywhere, what did I look at today -- rather than the capacity
    questions the analyst dashboard answers.
    """
    return build_clinical_summary()


def build_clinical_summary() -> dict:
    """
    Compute the caseload payload for the signed-in clinician.

    Shared with the caseload PDF for the same reason `build_kpis` is shared
    with the cohort one: a handover sheet that disagreed with the screen it
    was printed from would be worse than no handover sheet at all.
    """
    logs = (
        PredictionLog.query.filter_by(user_id=g.current_user.id)
        .order_by(PredictionLog.created_at.desc())
        .limit(CASELOAD_SAMPLE)
        .all()
    )

    if not logs:
        return {
            "caseload": {
                "patients": 0,
                "high_risk": 0,
                "avg_los_days": 0,
                "longest_los_days": 0,
                "scored_today": 0,
                "avg_confidence": 0,
                "due_within_48h": 0,
            },
            "risk_distribution": [
                {"tier": t, "count": 0, "percentage": 0.0} for t in RISK_TIER_LABELS
            ],
            "discharge_schedule": [],
            "worklist": [],
            "recent": [],
        }

    los = np.array([log.los_days for log in logs], dtype=float)

    # `created_at` is stored as UTC, so "today" has to be UTC too or a stay
    # scored late in the evening reads as a day out. Resolved once and passed
    # down, so every date on the page agrees even across a midnight boundary.
    today = datetime.now(UTC).date()

    counts = {tier: 0 for tier in RISK_TIER_LABELS}
    for log in logs:
        if log.risk_tier in counts:
            counts[log.risk_tier] += 1

    entries = [_caseload_entry(log, today) for log in logs]
    due_within_48h = sum(1 for e in entries if 0 <= e["days_remaining"] <= 2)

    return {
        "caseload": {
            "patients": len(logs),
            "high_risk": sum(counts[t] for t in ("High", "Very High")),
            "avg_los_days": round(float(los.mean()), 2),
            "longest_los_days": round(float(los.max()), 2),
            "scored_today": sum(1 for log in logs if log.created_at.date() == today),
            "avg_confidence": round(
                float(np.mean([log.confidence for log in logs])), 4
            ),
            "due_within_48h": due_within_48h,
        },
        "model_version": logs[0].model_version,
        "risk_distribution": [
            {
                "tier": tier,
                "count": counts[tier],
                "percentage": round(100 * counts[tier] / len(logs), 1),
            }
            for tier in RISK_TIER_LABELS
        ],
        "discharge_schedule": _discharge_schedule(entries, today),
        # Sickest first, then soonest out: the order a ward round works in.
        "worklist": sorted(
            entries,
            key=lambda e: (-e["risk_rank"], e["expected_discharge"]),
        )[:WORKLIST_LIMIT],
        "recent": [log.to_dict() for log in logs[:10]],
    }


def _caseload_entry(log: PredictionLog, today: date) -> dict:
    """One admission as the ward round needs to see it."""
    admitted = log.created_at.date()
    stay = max(int(round(log.los_days)), 0)
    expected = admitted + timedelta(days=stay)

    payload = log.input_payload or {}
    return {
        "id": log.id,
        # A batch-scored row carries its patient_id; a single prediction may
        # not have been given one, so fall back to something referable.
        "patient_ref": log.patient_ref or f"#{log.id}",
        "los_days": round(float(log.los_days), 2),
        "risk_tier": log.risk_tier,
        "risk_rank": _risk_rank(log.risk_tier),
        "confidence": round(float(log.confidence), 4),
        "department": payload.get("department"),
        "age": payload.get("age"),
        "admission_type": payload.get("admission_type"),
        "scored_at": log.created_at.isoformat(),
        "expected_discharge": expected.isoformat(),
        "days_remaining": (expected - today).days,
    }


def _risk_rank(tier: str) -> int:
    try:
        return RISK_TIER_LABELS.index(tier)
    except ValueError:
        return 0


def _discharge_schedule(entries: list[dict], today: date) -> list[dict]:
    """
    Expected discharges per day over the planning horizon.

    Stays that have already run past their predicted date collapse onto day 0
    rather than being dropped -- an overdue discharge is the one a clinician
    most needs to see.
    """
    buckets = {day: 0 for day in range(CASELOAD_HORIZON_DAYS + 1)}
    for entry in entries:
        offset = min(max(entry["days_remaining"], 0), CASELOAD_HORIZON_DAYS)
        buckets[offset] += 1

    return [
        {
            "day": day,
            "date": (today + timedelta(days=day)).isoformat(),
            "patients": count,
            "label": "Overdue / today" if day == 0 else f"Day +{day}",
        }
        for day, count in sorted(buckets.items())
    ]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _forecast_days() -> int:
    try:
        days = int(request.args.get("days", DEFAULT_FORECAST_DAYS))
    except ValueError:
        raise ApiError("'days' must be a whole number.", 400) from None
    if not 1 <= days <= MAX_FORECAST_DAYS:
        raise ApiError(
            f"'days' must be between 1 and {MAX_FORECAST_DAYS}.", 400
        )
    return days


def _select_dataset(requested: str | None = None) -> Dataset | None:
    """Scoped to the caller: another user's dataset id must read as absent."""
    query = Dataset.query.filter_by(user_id=g.current_user.id)

    if requested:
        try:
            dataset = query.filter_by(id=int(requested)).first()
        except ValueError:
            raise ApiError("'dataset_id' must be a whole number.", 400) from None
        if dataset is None:
            raise ApiError(f"Dataset {requested} was not found.", 404)
        return dataset

    return query.order_by(Dataset.uploaded_at.desc()).first()


# When capacity is auto-sized, place the busiest forecast day at this level.
PEAK_OCCUPANCY = 0.95


def _configured_capacity() -> int | None:
    """Explicit `?total_beds=`, then TOTAL_BEDS; None means auto-size."""
    requested = request.args.get("total_beds")
    if requested:
        try:
            beds = int(requested)
        except ValueError:
            raise ApiError("'total_beds' must be a whole number.", 400) from None
        if beds < 1:
            raise ApiError("'total_beds' must be at least 1.", 400)
        return beds

    configured = current_app.config["TOTAL_BEDS"]
    return configured if configured > 0 else None


def _bed_forecast(los: np.ndarray, days: int) -> list[dict]:
    """
    Project bed occupancy forward from the current cohort.

    Occupancy has two components:

      * the patients in beds today, draining as each reaches their predicted
        length of stay;
      * new admissions, arriving at the rate implied by Little's Law
        (arrivals = census / average stay) and draining according to the same
        empirical length-of-stay distribution.

    Using the cohort's own survival curve for arrivals -- rather than assuming
    every arrival stays exactly the mean -- is what makes the projection settle
    at the true steady state instead of overshooting it.
    """
    census = len(los)
    if census == 0:
        return []

    mean_los = float(los.mean())
    arrivals_per_day = census / mean_los if mean_los > 0 else 0.0

    # survival[a] = P(a patient is still in a bed `a` days after admission)
    survival = np.array([float((los > a).mean()) for a in range(days + 1)])

    # Occupancy first, capacity second: an auto-sized ward has to be able to
    # absorb the busiest projected day, not just today's census.
    occupancy = [
        float((los > day).sum()) + arrivals_per_day * survival[:day].sum()
        for day in range(1, days + 1)
    ]

    configured = _configured_capacity()
    derived = configured is None
    total_beds = (
        configured if configured is not None
        else max(int(np.ceil(max(occupancy) / PEAK_OCCUPANCY)), 1)
    )

    today = date.today()
    return [
        {
            "day": day,
            "date": (today + timedelta(days=day)).isoformat(),
            "occupied_beds": int(round(occupied)),
            "available_beds": int(round(max(total_beds - occupied, 0))),
            "projected_discharges": int(((los > day - 1) & (los <= day)).sum()),
            "projected_admissions": int(round(arrivals_per_day)),
            "occupancy_rate": round(occupied / total_beds, 4),
            "capacity": total_beds,
            "capacity_derived": derived,
        }
        for day, occupied in enumerate(occupancy, start=1)
    ]


def _histogram(los: np.ndarray, bins: int = 12) -> list[dict]:
    counts, edges = np.histogram(los, bins=bins)
    return [
        {
            "range": f"{edges[i]:.0f}-{edges[i + 1]:.0f}",
            "midpoint": round(float((edges[i] + edges[i + 1]) / 2), 1),
            "count": int(counts[i]),
        }
        for i in range(len(counts))
    ]


def _department_breakdown(frame, predictions) -> list[dict]:
    if "department" not in frame.columns:
        return []

    joined = predictions.copy()
    joined["department"] = frame["department"].astype(str).to_numpy()

    grouped = (
        joined.groupby("department")
        .agg(patients=("los_days", "size"), avg_los=("los_days", "mean"))
        .reset_index()
        .sort_values("patients", ascending=False)
        .head(10)
    )
    return [
        {
            "department": str(row.department),
            "patients": int(row.patients),
            "avg_los_days": round(float(row.avg_los), 2),
        }
        for row in grouped.itertuples(index=False)
    ]


def _kpis_from_logs(forecast_days: int) -> dict:
    """Dashboard payload assembled from the prediction log alone."""
    logs = (
        PredictionLog.query.filter_by(user_id=g.current_user.id)
        .order_by(PredictionLog.created_at.desc())
        .limit(1000)
        .all()
    )

    if not logs:
        return {
            "source": {"type": "empty"},
            "kpis": {
                "total_patients": 0,
                "avg_los_days": 0,
                "median_los_days": 0,
                "high_risk_patients": 0,
                "avg_confidence": 0,
                "total_bed_days": 0,
            },
            "risk_distribution": [
                {"tier": t, "count": 0, "percentage": 0.0} for t in RISK_TIER_LABELS
            ],
            "los_histogram": [],
            "bed_forecast": [],
            "department_breakdown": [],
        }

    los = np.array([log.los_days for log in logs], dtype=float)
    tiers = [log.risk_tier for log in logs]
    counts = {tier: tiers.count(tier) for tier in RISK_TIER_LABELS}

    return {
        "source": {"type": "prediction_log", "count": len(logs)},
        "model_version": logs[0].model_version,
        "kpis": {
            "total_patients": len(logs),
            "avg_los_days": round(float(los.mean()), 2),
            "median_los_days": round(float(np.median(los)), 2),
            "high_risk_patients": sum(
                counts[t] for t in ("High", "Very High")
            ),
            "avg_confidence": round(
                float(np.mean([log.confidence for log in logs])), 4
            ),
            "total_bed_days": int(round(float(los.sum()))),
        },
        "risk_distribution": [
            {
                "tier": tier,
                "count": counts[tier],
                "percentage": round(100 * counts[tier] / len(logs), 1),
            }
            for tier in RISK_TIER_LABELS
        ],
        "los_histogram": _histogram(los),
        "bed_forecast": _bed_forecast(los, forecast_days),
        "department_breakdown": [],
    }
