"""Prediction endpoints: single record, batch by dataset, and model metadata."""

from __future__ import annotations

from flask import Blueprint, g, request

from ml.predictor import ModelNotTrainedError, get_predictor
from ml.schema import CATEGORICAL_FEATURES, COLUMN_SPECS, FEATURE_COLUMNS, NUMERIC_FEATURES

from ..auth import require_capability, requires_auth, requires_capability
from ..errors import ApiError
from ..models import Dataset, PredictionLog, db
from ..roles import COHORT_VIEW, MODEL_INSPECT, PATIENT_PREDICT
from .dataset_routes import load_dataset_frame

bp = Blueprint("predict", __name__, url_prefix="/api/predict")

BATCH_LOG_LIMIT = 500


def _predictor():
    try:
        return get_predictor()
    except ModelNotTrainedError as exc:
        raise ApiError(
            str(exc), 503,
            hint="Run `python -m ml.train` to produce the model artifacts.",
        ) from exc


@bp.post("")
@requires_auth
def predict():
    """
    Score a single patient record, or a whole dataset via `dataset_id`.

    Single:  {"age": 74, "gender": "F", ...}
    Batch:   {"dataset_id": 3}
    """
    payload = request.get_json(silent=True) or {}

    if "dataset_id" in payload:
        return _predict_dataset(payload)

    record = payload.get("patient", payload)
    return _predict_single(record, payload.get("explain", True))


def _predict_single(record: dict, explain: bool = True):
    require_capability(PATIENT_PREDICT)

    if not isinstance(record, dict) or not record:
        raise ApiError(
            "A patient record is required.", 400,
            hint=f"Send an object with these fields: {', '.join(FEATURE_COLUMNS)}.",
        )

    cleaned = validate_record(record)
    predictor = _predictor()
    result = predictor.predict_one(cleaned, explain=explain)

    db.session.add(
        PredictionLog(
            user_id=g.current_user.id,
            dataset_id=None,
            patient_ref=str(record.get("patient_id") or "")[:64] or None,
            input_payload=cleaned,
            los_days=result["los_days"],
            risk_tier=result["risk_tier"],
            confidence=result["confidence"],
            model_version=result["model_version"],
            latency_ms=result["latency_ms"],
        )
    )
    db.session.commit()

    result["input"] = cleaned
    return result


def _predict_dataset(payload: dict):
    dataset_id = payload["dataset_id"]
    dataset = Dataset.query.filter_by(
        id=dataset_id, user_id=g.current_user.id
    ).first()
    if dataset is None:
        raise ApiError(f"Dataset {dataset_id} was not found.", 404)

    # After the ownership check, not before: someone probing for another
    # user's dataset id must get the same 404 whichever role they hold, or the
    # 403/404 difference confirms which ids exist.
    require_capability(COHORT_VIEW)

    frame = load_dataset_frame(dataset)
    predictor = _predictor()
    predictions = predictor.predict_batch(frame)

    # Log a bounded sample; writing a row per record would swamp the table
    # on a large upload while adding nothing to the audit trail.
    for row in predictions.head(BATCH_LOG_LIMIT).itertuples(index=False):
        db.session.add(
            PredictionLog(
                user_id=g.current_user.id,
                dataset_id=dataset.id,
                patient_ref=str(row.patient_id)[:64],
                input_payload={},
                los_days=float(row.los_days),
                risk_tier=str(row.risk_tier),
                confidence=float(row.confidence),
                model_version=predictor.version,
            )
        )
    db.session.commit()

    tier_counts = predictions["risk_tier"].value_counts().to_dict()
    return {
        "dataset_id": dataset.id,
        "count": int(len(predictions)),
        "logged": int(min(len(predictions), BATCH_LOG_LIMIT)),
        "model_version": predictor.version,
        "summary": {
            "avg_los_days": round(float(predictions["los_days"].mean()), 2),
            "median_los_days": round(float(predictions["los_days"].median()), 2),
            "risk_distribution": {k: int(v) for k, v in tier_counts.items()},
        },
        "predictions": predictions.head(200).to_dict(orient="records"),
    }


@bp.get("/explain/global")
@requires_auth
@requires_capability(MODEL_INSPECT)
def global_explanation():
    task = request.args.get("task", "regression")
    if task not in {"regression", "classification"}:
        raise ApiError(
            f"Unknown task '{task}'.", 400,
            hint="Use task=regression or task=classification.",
        )
    predictor = _predictor()
    return {
        "task": task,
        "model_version": predictor.version,
        "features": predictor.global_importance(task),
    }


@bp.get("/model")
@requires_auth
@requires_capability(MODEL_INSPECT)
def model_info():
    return _predictor().model_info()


@bp.get("/schema")
def schema():
    """The input contract, so the frontend can build its form from one source."""
    vocabulary = _trained_categories()
    return {
        "feature_columns": FEATURE_COLUMNS,
        "numeric": [
            {
                "name": c,
                "description": COLUMN_SPECS[c].description,
                "min": COLUMN_SPECS[c].minimum,
                "max": COLUMN_SPECS[c].maximum,
            }
            for c in NUMERIC_FEATURES
        ],
        "categorical": [
            {
                "name": c,
                "description": COLUMN_SPECS[c].description,
                "examples": list(COLUMN_SPECS[c].examples),
                # The categories the model was actually fitted on, when a model
                # is loaded. The encoder uses handle_unknown="ignore", so a
                # value outside this list is silently encoded as all-zeros and
                # scores as if the field were blank -- the UI needs the real
                # vocabulary to keep a user from doing that unknowingly.
                "categories": vocabulary.get(c, []),
            }
            for c in CATEGORICAL_FEATURES
        ],
    }


def _trained_categories() -> dict[str, list[str]]:
    """Read the fitted OneHotEncoder's categories, or {} if no model is loaded."""
    try:
        predictor = get_predictor()
    except ModelNotTrainedError:
        return {}

    try:
        for name, transformer, columns in predictor.preprocessor.transformers_:
            if name != "categorical":
                continue
            encoder = getattr(transformer, "named_steps", {}).get("encode", transformer)
            return {
                column: [str(v) for v in categories]
                for column, categories in zip(
                    columns, encoder.categories_, strict=False
                )
            }
    except (AttributeError, TypeError):
        # An older artifact with a different pipeline shape: fall back to the
        # documented examples rather than failing the whole schema call.
        return {}
    return {}


def validate_record(record: dict) -> dict:
    """Check a single-patient payload before it reaches the model."""
    cleaned: dict = {}
    errors: list[str] = []

    for column in NUMERIC_FEATURES:
        if column not in record or record[column] in (None, ""):
            spec = COLUMN_SPECS[column]
            errors.append(f"Missing '{column}' — {spec.description}.")
            continue
        try:
            value = float(record[column])
        except (TypeError, ValueError):
            errors.append(
                f"'{column}' must be a number but received "
                f"'{record[column]}'."
            )
            continue

        spec = COLUMN_SPECS[column]
        if spec.minimum is not None and not (spec.minimum <= value <= spec.maximum):
            errors.append(
                f"'{column}' is {value:g}, outside the valid range "
                f"{spec.range_text}."
            )
            continue
        cleaned[column] = value

    for column in CATEGORICAL_FEATURES:
        value = record.get(column)
        if value in (None, ""):
            errors.append(f"Missing '{column}' — {COLUMN_SPECS[column].description}.")
            continue
        cleaned[column] = str(value).strip()

    if errors:
        raise ApiError(
            f"The patient record is incomplete or invalid "
            f"({len(errors)} problem{'s' if len(errors) > 1 else ''}).",
            422,
            details=errors,
            hint=f"Required fields: {', '.join(FEATURE_COLUMNS)}.",
        )

    return cleaned
