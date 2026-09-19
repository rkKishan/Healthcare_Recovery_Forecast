"""
SHAP explainability for both the regressor and the classifier.

Exposes two views:
  * global  - mean absolute SHAP value per feature across a background sample,
              answering "what drives length of stay in general?"
  * local   - signed per-feature contributions for one patient, answering
              "why this prediction, for this person?"

TreeSHAP is used for the tree ensembles that normally win model selection; a
linear fallback keeps the module working if a linear model is ever selected.
"""

from __future__ import annotations

import numpy as np

from .preprocess import describe_feature
from .schema import CATEGORICAL_FEATURES, RISK_TIER_LABELS

# Contributions below this magnitude are noise, not explanation.
MIN_CONTRIBUTION = 1e-6


def _contextual_label(name: str, readable: str, value: float) -> str:
    """
    Phrase a one-hot feature according to whether it is set for this patient.

    A zero-valued `admission_type_Elective` still carries SHAP weight -- the
    model is reacting to the patient *not* being elective -- so the label has
    to say so, otherwise the explanation contradicts the patient's record.
    """
    is_one_hot = any(name.startswith(f"{col}_") for col in CATEGORICAL_FEATURES)
    if is_one_hot and value < 0.5 and " is " in readable:
        return readable.replace(" is ", " is not ", 1)
    return readable


class ModelExplainer:
    """Wraps SHAP explainers for the LOS regressor and the risk classifier."""

    def __init__(self, regressor, classifier, background: np.ndarray,
                 feature_names: list[str]):
        import shap

        self.feature_names = feature_names
        self.readable = [describe_feature(n) for n in feature_names]
        self._background = background

        self._reg_explainer = self._build(shap, regressor, background)
        self._clf_explainer = self._build(shap, classifier, background)

        self._global_cache: dict[str, list[dict]] = {}

    @staticmethod
    def _build(shap, model, background):
        """TreeSHAP where possible, linear/kernel SHAP otherwise."""
        try:
            return shap.TreeExplainer(model)
        except Exception:  # noqa: BLE001 - non-tree model selected
            try:
                return shap.LinearExplainer(model, background)
            except Exception:  # noqa: BLE001
                return shap.Explainer(model, background)

    # ------------------------------------------------------------------
    # Local explanations
    # ------------------------------------------------------------------

    def explain_regression(self, row: np.ndarray, top_k: int = 8) -> dict:
        """Signed contributions, in days, for a single patient's LOS."""
        values, base = self._shap_for(self._reg_explainer, row)
        return self._package(values, base, row, top_k, unit="days")

    def explain_classification(self, row: np.ndarray, tier_index: int,
                               top_k: int = 8) -> dict:
        """Contributions toward the predicted risk tier, in log-odds."""
        values, base = self._shap_for(
            self._clf_explainer, row, class_index=tier_index
        )
        result = self._package(values, base, row, top_k, unit="log-odds")
        result["tier"] = RISK_TIER_LABELS[tier_index]
        return result

    def _shap_for(self, explainer, row: np.ndarray,
                  class_index: int | None = None):
        matrix = row.reshape(1, -1)
        raw = explainer.shap_values(matrix)
        base = explainer.expected_value

        raw = np.asarray(raw)
        base = np.asarray(base)

        # SHAP returns (1, n_features) for regression and either
        # (1, n_features, n_classes) or a per-class list for classification.
        if raw.ndim == 3:
            idx = class_index or 0
            values = raw[0, :, idx]
            base_value = float(base.ravel()[idx]) if base.size > 1 else float(base)
        elif raw.ndim == 2 and class_index is not None and raw.shape[0] > 1:
            values = raw[class_index]
            base_value = float(base.ravel()[class_index]) if base.size > 1 else float(base)
        else:
            values = raw[0] if raw.ndim == 2 else raw
            base_value = float(base.ravel()[0]) if base.size else 0.0

        return np.asarray(values, dtype=float).ravel(), base_value

    def _package(self, values: np.ndarray, base: float, row: np.ndarray,
                 top_k: int, unit: str) -> dict:
        contributions = [
            {
                "feature": name,
                "label": _contextual_label(name, readable, raw_value),
                "value": round(float(raw_value), 4),
                "shap_value": round(float(shap_value), 4),
                "direction": "increases" if shap_value > 0 else "decreases",
            }
            for name, readable, shap_value, raw_value in zip(
                self.feature_names, self.readable, values, row, strict=False
            )
            if abs(shap_value) > MIN_CONTRIBUTION
        ]
        contributions.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
        top = contributions[:top_k]

        other = sum(c["shap_value"] for c in contributions[top_k:])

        return {
            "base_value": round(float(base), 4),
            "unit": unit,
            "top_features": top,
            "other_features_total": round(float(other), 4),
            "narrative": self._narrate(top, unit),
        }

    @staticmethod
    def _narrate(top: list[dict], unit: str) -> str:
        """A plain-language sentence a clinician can read at a glance."""
        if not top:
            return "No single factor stands out for this patient."

        suffix = " days" if unit == "days" else ""
        up = [c for c in top if c["shap_value"] > 0][:2]
        down = [c for c in top if c["shap_value"] < 0][:2]

        parts: list[str] = []
        if up:
            listed = " and ".join(
                f"{c['label'].lower()} (+{c['shap_value']:.1f}{suffix})" for c in up
            )
            parts.append(f"pushed up by {listed}")
        if down:
            listed = " and ".join(
                f"{c['label'].lower()} ({c['shap_value']:.1f}{suffix})" for c in down
            )
            parts.append(f"pulled down by {listed}")

        return "This estimate is " + ", ".join(parts) + "."

    # ------------------------------------------------------------------
    # Global importance
    # ------------------------------------------------------------------

    def global_importance(self, task: str = "regression",
                          top_k: int = 12) -> list[dict]:
        """Mean |SHAP| per feature across the stored background sample."""
        if task in self._global_cache:
            return self._global_cache[task][:top_k]

        explainer = (self._reg_explainer if task == "regression"
                     else self._clf_explainer)
        raw = np.asarray(explainer.shap_values(self._background))

        # Average over the class axis too, for the multi-class model.
        magnitude = (
            np.abs(raw).mean(axis=(0, 2)) if raw.ndim == 3 else np.abs(raw).mean(axis=0)
        )

        ranked = sorted(
            (
                {
                    "feature": name,
                    "label": describe_feature(name),
                    "importance": round(float(score), 4),
                }
                for name, score in zip(self.feature_names, magnitude, strict=False)
            ),
            key=lambda d: d["importance"],
            reverse=True,
        )
        self._global_cache[task] = ranked
        return ranked[:top_k]
