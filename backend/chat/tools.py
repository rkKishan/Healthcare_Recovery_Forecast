"""
The tools the assistant may call, and who is allowed to call them.

Each entry pairs a JSON-schema declaration (sent to the model) with the
function that answers it (run here, in process). The functions are the same
`build_kpis` / `build_clinical_summary` / predictor calls the REST routes and
the PDF reports use, so the assistant cannot disagree with the dashboard: it
is reading the identical payload.

Authorisation is structural rather than instructed. `tools_for` filters by the
caller's capabilities, so a doctor's request never carries a cohort tool in
the first place -- the model cannot call what it was not offered. `dispatch`
then re-checks the capability before running anything, because a model that
invents a tool name it was never given must not be able to reach a function
through it.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from ..errors import ApiError
from ..roles import (
    CASELOAD_VIEW,
    COHORT_VIEW,
    DATASET_UPLOAD,
    MODEL_INSPECT,
    PATIENT_PREDICT,
    has_capability,
)

logger = logging.getLogger(__name__)

# How many rows of a list the assistant is handed. The model does not need the
# whole worklist to answer a question about it, and a large tool result is
# both slower and more expensive than the answer is worth.
WORKLIST_SLICE = 12
SCHEDULE_SLICE = 14
DATASET_SLICE = 10
DRIVER_SLICE = 6


# --------------------------------------------------------------------------
# Tool implementations
#
# Each returns a plain dict, which is JSON-encoded straight into the
# conversation as a tool result.
# --------------------------------------------------------------------------


def _score_admission(**record: Any) -> dict:
    """Score one admission through the real model, with its SHAP drivers."""
    from ..routes.predict_routes import _predict_single

    result = _predict_single(record, explain=True)
    return {
        "predicted_los_days": result["los_days"],
        "risk_tier": result["risk_tier"],
        "confidence": result["confidence"],
        "estimated_discharge": result["estimated_discharge"],
        "guidance": result["guidance"],
        "model_version": result["model_version"],
        # The drivers are the point. A predicted stay with no explanation is
        # exactly the output this application exists not to produce.
        #
        # `shap_values` is the explainer's dict -- base value, unit, ranked
        # features and a plain-language narrative -- not a bare list. The
        # narrative is handed over as-is because it is already the sentence
        # the assistant is being asked to produce.
        "explanation": _drivers(result.get("shap_values")),
        "input": result["input"],
    }


def _drivers(shap: dict | None) -> dict:
    """The explanation, trimmed to what the assistant needs to say."""
    if not isinstance(shap, dict):
        return {}
    return {
        "narrative": shap.get("narrative"),
        "unit": shap.get("unit"),
        "baseline": shap.get("base_value"),
        "top_features": [
            {
                "feature": f.get("label") or f.get("feature"),
                "effect_days": f.get("shap_value"),
                "direction": f.get("direction"),
            }
            for f in (shap.get("top_features") or [])[:DRIVER_SLICE]
        ],
    }


def _my_caseload() -> dict:
    """The signed-in clinician's own scored admissions."""
    from ..routes.dashboard_routes import build_clinical_summary

    payload = build_clinical_summary()
    return {
        "summary": payload["caseload"],
        "risk_distribution": payload["risk_distribution"],
        "discharge_schedule": payload.get("discharge_schedule", [])[:SCHEDULE_SLICE],
        "worklist": payload.get("worklist", [])[:WORKLIST_SLICE],
        "model_version": payload.get("model_version"),
    }


def _cohort_overview(dataset_id: str | None = None, forecast_days: int = 14) -> dict:
    """Cohort KPIs and the bed-occupancy forecast."""
    from ..routes.dashboard_routes import build_kpis

    payload = build_kpis(dataset_id, max(1, min(int(forecast_days), 60)))
    return payload


def _model_metrics() -> dict:
    """Held-out performance of the model currently loaded."""
    from ..routes.predict_routes import _predictor

    return _predictor().model_info()


def _global_drivers(task: str = "regression") -> dict:
    """Which features move the model's output across the whole population."""
    from ..routes.predict_routes import _predictor

    if task not in {"regression", "classification"}:
        task = "regression"
    predictor = _predictor()
    return {
        "task": task,
        "model_version": predictor.version,
        "features": predictor.global_importance(task),
    }


def _list_datasets() -> dict:
    """The caller's uploaded extracts, newest first."""
    from flask import g

    from ..models import Dataset

    rows = (
        Dataset.query.filter_by(user_id=g.current_user.id)
        .order_by(Dataset.uploaded_at.desc())
        .limit(DATASET_SLICE)
        .all()
    )
    return {"datasets": [d.to_dict() for d in rows]}


# --------------------------------------------------------------------------
# Declarations
# --------------------------------------------------------------------------


class Tool:
    __slots__ = ("name", "capability", "description", "parameters", "run")

    def __init__(
        self,
        name: str,
        capability: str,
        description: str,
        parameters: dict,
        run: Callable[..., dict],
    ):
        self.name = name
        self.capability = capability
        self.description = description
        self.parameters = parameters
        self.run = run

    def declaration(self) -> dict:
        """The OpenAI-shaped declaration the provider's `tools` param expects."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_NO_ARGS: dict = {"type": "object", "properties": {}, "required": []}

# The seven admission fields, mirrored from ml/schema.py. Spelled out here
# rather than generated so the model gets the ranges and the vocabulary in the
# same breath as the field names -- it has to fill these in from a sentence a
# doctor typed, and a bare column list produces far more re-asking.
_ADMISSION_PARAMS: dict = {
    "type": "object",
    "properties": {
        "age": {"type": "integer", "description": "Patient age in years, 0-120."},
        "gender": {"type": "string", "enum": ["M", "F", "U"]},
        "admission_type": {
            "type": "string",
            "enum": ["Emergency", "Elective", "Urgent", "Newborn", "Trauma"],
        },
        "diagnosis_code": {
            "type": "string",
            "description": (
                "Primary diagnosis group: CIRC circulatory, RESP respiratory, "
                "INFX infection, MUSC musculoskeletal, DIGE digestive, "
                "NEUR neurological, ONCO oncology, TRMA trauma, "
                "PSYC psychiatric, OBST obstetric."
            ),
        },
        "department": {
            "type": "string",
            "description": "Admitting department, e.g. Cardiology, Pulmonology.",
        },
        "comorbidity_count": {"type": "integer", "description": "0-20."},
        "prior_admissions": {
            "type": "integer",
            "description": "Admissions in the previous 12 months, 0-50.",
        },
    },
    "required": [
        "age",
        "gender",
        "admission_type",
        "diagnosis_code",
        "department",
        "comorbidity_count",
        "prior_admissions",
    ],
}


TOOLS: tuple[Tool, ...] = (
    Tool(
        "score_admission",
        PATIENT_PREDICT,
        "Predict length of stay and discharge-risk tier for one admission, "
        "with the SHAP factors driving the prediction. Requires all seven "
        "admission fields; ask the user for any you do not have rather than "
        "guessing. This also records the prediction in the audit log.",
        _ADMISSION_PARAMS,
        _score_admission,
    ),
    Tool(
        "my_caseload",
        CASELOAD_VIEW,
        "The signed-in clinician's own caseload: how many admissions they "
        "have scored, the risk mix, expected discharges per day, and the "
        "ward-round worklist ordered sickest-first. Use this for questions "
        "about 'my patients', who is overdue, or who is due out soon.",
        _NO_ARGS,
        _my_caseload,
    ),
    Tool(
        "cohort_overview",
        COHORT_VIEW,
        "Cohort-wide KPIs and the bed-occupancy forecast for an uploaded "
        "extract: average stay, risk distribution, projected occupancy and "
        "discharges per day. Use for capacity and whole-ward questions.",
        {
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "Which upload to read. Omit for the most recent.",
                },
                "forecast_days": {
                    "type": "integer",
                    "description": "Forecast horizon, 1-60. Defaults to 14.",
                },
            },
            "required": [],
        },
        _cohort_overview,
    ),
    Tool(
        "model_metrics",
        MODEL_INSPECT,
        "Held-out test metrics for the model currently loaded: RMSE, MAE and "
        "R2 for length of stay, accuracy and F1 for the risk tier, plus the "
        "model version and when it was trained. Use this to answer whether "
        "the model is still trustworthy.",
        _NO_ARGS,
        _model_metrics,
    ),
    Tool(
        "global_drivers",
        MODEL_INSPECT,
        "Which input features move the model's output across the whole "
        "population, ranked. Ask for task='regression' for length of stay or "
        "task='classification' for the risk tier. This is population-level "
        "importance, not the drivers for one patient.",
        {
            "type": "object",
            "properties": {
                "task": {"type": "string", "enum": ["regression", "classification"]}
            },
            "required": [],
        },
        _global_drivers,
    ),
    Tool(
        "list_datasets",
        DATASET_UPLOAD,
        "The extracts this user has uploaded, newest first, with row counts "
        "and whether each carries a length_of_stay column (and so can be used "
        "for training rather than only scoring).",
        _NO_ARGS,
        _list_datasets,
    ),
)

_BY_NAME: dict[str, Tool] = {tool.name: tool for tool in TOOLS}


def tools_for(role: str) -> list[dict]:
    """The tool declarations a given role is allowed to be offered."""
    return [
        tool.declaration()
        for tool in TOOLS
        if has_capability(role, tool.capability)
    ]


def tool_names_for(role: str) -> list[str]:
    return [tool.name for tool in TOOLS if has_capability(role, tool.capability)]


def dispatch(role: str, name: str, arguments: dict) -> dict:
    """
    Run one tool call on behalf of `role`.

    Both failure modes return a dict rather than raising: a tool result is the
    model's feedback channel, and an error it can read ("that field is out of
    range") lets it correct itself or ask the user, where an exception would
    end the turn.
    """
    tool = _BY_NAME.get(name)
    if tool is None:
        return {"error": f"No such tool: {name}."}

    # The model was never handed this tool, so it has hallucinated the name.
    # Refuse by capability rather than trusting the offer list alone.
    if not has_capability(role, tool.capability):
        return {"error": f"Your role is not permitted to use {name}."}

    args = arguments or {}

    # Bind the arguments separately from running the tool. A TypeError raised
    # *inside* a tool is a bug here, not a malformed call, and reporting the
    # two identically told the model to retry a call that could never succeed
    # -- it burned every round doing so.
    try:
        bound = inspect.signature(tool.run).bind(**args)
    except TypeError as exc:
        return {"error": f"Wrong arguments for {name}: {exc}"}

    try:
        return tool.run(*bound.args, **bound.kwargs)
    except ApiError as exc:
        return {"error": exc.message, "hint": getattr(exc, "hint", None)}
    except Exception as exc:  # noqa: BLE001 - surfaced to the model, not raised
        logger.exception("Tool %s failed", name)
        return {"error": f"{name} failed: {exc}"}
