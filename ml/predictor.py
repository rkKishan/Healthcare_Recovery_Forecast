"""
Inference service.

Loads a versioned artifact set once per process and serves single-record and
batch predictions. The preprocessor is only ever `.transform()`-ed here, never
re-fitted, so serving cannot drift from training.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .explain import ModelExplainer
from .preprocess import prepare_features
from .schema import (
    RISK_TIER_GUIDANCE,
    RISK_TIER_LABELS,
    los_to_risk_tier,
)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


class ModelNotTrainedError(RuntimeError):
    """Raised when no artifact set exists yet."""


class Predictor:
    """Thread-safe, lazily-initialised wrapper around the trained artifacts."""

    def __init__(self, models_dir: Path = MODELS_DIR, version: str | None = None):
        self.models_dir = Path(models_dir)
        self.version = version or self._resolve_version()
        self._dir = self.models_dir / self.version

        self.preprocessor = joblib.load(self._dir / "preprocessor.pkl")
        self.regressor = joblib.load(self._dir / "regressor.pkl")
        self.classifier = joblib.load(self._dir / "classifier.pkl")
        self.background = joblib.load(self._dir / "background.pkl")
        self.metadata = json.loads((self._dir / "metadata.json").read_text())

        self.feature_names = self.metadata["feature_names"]

        # SHAP construction is deferred: it costs ~1s and most requests to the
        # dashboard never need an explanation.
        self._explainer: ModelExplainer | None = None
        self._explainer_lock = threading.Lock()

    def _resolve_version(self) -> str:
        pointer = self.models_dir / "latest.json"
        if not pointer.exists():
            raise ModelNotTrainedError(
                "No trained model found. Run `python -m ml.train` first."
            )
        version = json.loads(pointer.read_text())["version"]
        if not (self.models_dir / version).exists():
            raise ModelNotTrainedError(
                f"Model version '{version}' is referenced by latest.json but "
                f"its directory is missing. Re-run `python -m ml.train`."
            )
        return version

    @property
    def explainer(self) -> ModelExplainer:
        if self._explainer is None:
            with self._explainer_lock:
                if self._explainer is None:
                    self._explainer = ModelExplainer(
                        self.regressor, self.classifier,
                        self.background, self.feature_names,
                    )
        return self._explainer

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_one(self, record: dict, explain: bool = True) -> dict:
        """Predict for a single patient record."""
        started = time.perf_counter()
        frame = pd.DataFrame([record])
        matrix = self._transform(frame)

        los = float(self.regressor.predict(matrix)[0])
        los = max(los, 0.1)

        probabilities = self.classifier.predict_proba(matrix)[0]
        tier_idx = int(np.argmax(probabilities))
        tier = RISK_TIER_LABELS[tier_idx]

        result: dict[str, Any] = {
            "los_days": round(los, 2),
            "risk_tier": tier,
            "risk_tier_index": tier_idx,
            "confidence": round(float(probabilities[tier_idx]), 4),
            "tier_probabilities": {
                label: round(float(p), 4)
                for label, p in zip(RISK_TIER_LABELS, probabilities, strict=False)
            },
            "guidance": RISK_TIER_GUIDANCE[tier],
            "los_derived_tier": los_to_risk_tier(los),
            "estimated_discharge": (
                datetime.now(UTC) + timedelta(days=los)
            ).date().isoformat(),
            "model_version": self.version,
        }

        if explain:
            row = matrix[0]
            result["shap_values"] = self.explainer.explain_regression(row)
            result["risk_shap_values"] = self.explainer.explain_classification(
                row, tier_idx
            )

        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        return result

    def predict_batch(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Predict for a whole dataset. No SHAP - this runs over many rows."""
        matrix = self._transform(frame)

        los = np.maximum(self.regressor.predict(matrix), 0.1)
        probabilities = self.classifier.predict_proba(matrix)
        tier_indices = probabilities.argmax(axis=1)

        out = pd.DataFrame(index=frame.index)
        if "patient_id" in frame.columns:
            out["patient_id"] = frame["patient_id"].astype(str)
        else:
            out["patient_id"] = [f"ROW{i + 1:06d}" for i in range(len(frame))]

        out["los_days"] = np.round(los, 2)
        out["risk_tier"] = [RISK_TIER_LABELS[i] for i in tier_indices]
        out["risk_tier_index"] = tier_indices
        out["confidence"] = np.round(probabilities.max(axis=1), 4)
        return out

    def _transform(self, frame: pd.DataFrame) -> np.ndarray:
        prepared = prepare_features(frame)
        return np.asarray(self.preprocessor.transform(prepared))

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------

    def global_importance(self, task: str = "regression", top_k: int = 12):
        return self.explainer.global_importance(task, top_k)

    def model_info(self) -> dict:
        metrics = self.metadata["metrics"]
        best_reg = metrics["best_regressor"]
        best_clf = metrics["best_classifier"]
        return {
            "version": self.version,
            "trained_at": self.metadata["trained_at"],
            "data_source": self.metadata["data_source"],
            "training_rows": self.metadata["training_rows"],
            "regressor": {
                "algorithm": best_reg,
                **metrics["regression"][best_reg],
            },
            "classifier": {
                "algorithm": best_clf,
                **metrics["classification"][best_clf],
            },
            "comparison": {
                "regression": metrics["regression"],
                "classification": metrics["classification"],
            },
            "confusion_matrix": metrics["classification_detail"][best_clf],
            "risk_tiers": RISK_TIER_LABELS,
        }


# --------------------------------------------------------------------------
# Process-wide singleton
# --------------------------------------------------------------------------

_instance: Predictor | None = None
_lock = threading.Lock()


def get_predictor(refresh: bool = False) -> Predictor:
    """Return the shared Predictor, loading artifacts on first use."""
    global _instance
    if _instance is None or refresh:
        with _lock:
            if _instance is None or refresh:
                _instance = Predictor()
    return _instance


def is_ready() -> bool:
    """True when a trained artifact set is available to load."""
    try:
        get_predictor()
        return True
    except (ModelNotTrainedError, FileNotFoundError):
        return False


if __name__ == "__main__":
    sample = {
        "age": 74,
        "gender": "F",
        "admission_type": "Emergency",
        "diagnosis_code": "ONCO",
        "comorbidity_count": 4,
        "prior_admissions": 3,
        "department": "Oncology",
    }
    predictor = get_predictor()
    result = predictor.predict_one(sample)
    print(f"Model version : {result['model_version']}")
    print(f"Predicted LOS : {result['los_days']} days")
    print(f"Risk tier     : {result['risk_tier']} "
          f"(confidence {result['confidence']:.1%})")
    print(f"Latency       : {result['latency_ms']} ms")
    print(f"\n{result['shap_values']['narrative']}\n")
    for feature in result["shap_values"]["top_features"][:5]:
        print(f"  {feature['label']:<34}{feature['shap_value']:+7.2f} days")
