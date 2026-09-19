"""
Training pipeline.

Trains five algorithms for length-of-stay regression and the same five
families for discharge-risk classification, reports comparable metrics for
each, and persists the winners as a versioned artifact set under /models.

    python -m ml.train --rows 8000

The preprocessor is fitted once, on the training split only, and saved
alongside the models so inference never re-fits.
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from xgboost import XGBClassifier, XGBRegressor

from .data_generator import generate_dataset
from .preprocess import build_preprocessor, feature_names, prepare_features
from .schema import (
    RISK_TIER_LABELS,
    TARGET_COLUMN,
    los_to_risk_tier,
    risk_tier_index,
)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
RANDOM_STATE = 42


# --------------------------------------------------------------------------
# Model definitions
# --------------------------------------------------------------------------

def regressors() -> dict[str, Any]:
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(
            max_depth=12, min_samples_leaf=8, random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=400, max_depth=None, min_samples_leaf=2,
            n_jobs=-1, random_state=RANDOM_STATE
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=400, learning_rate=0.05, max_depth=4,
            subsample=0.9, random_state=RANDOM_STATE
        ),
        "XGBoost": XGBRegressor(
            n_estimators=600, learning_rate=0.05, max_depth=6,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
            objective="reg:squarederror", n_jobs=-1,
            random_state=RANDOM_STATE, verbosity=0
        ),
    }


def classifiers() -> dict[str, Any]:
    # Logistic Regression stands in for Linear Regression on the
    # classification task -- the same linear family, appropriate link function.
    return {
        # Multinomial is the default and only mode as of scikit-learn 1.9.
        "Logistic Regression": LogisticRegression(
            max_iter=2000, random_state=RANDOM_STATE
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=12, min_samples_leaf=8, random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=2, n_jobs=-1,
            random_state=RANDOM_STATE
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=250, learning_rate=0.08, max_depth=4,
            subsample=0.9, random_state=RANDOM_STATE
        ),
        "XGBoost": XGBClassifier(
            n_estimators=500, learning_rate=0.06, max_depth=6,
            subsample=0.9, colsample_bytree=0.9,
            objective="multi:softprob", num_class=len(RISK_TIER_LABELS),
            n_jobs=-1, random_state=RANDOM_STATE, verbosity=0
        ),
    }


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------

def train(frame: pd.DataFrame, test_size: float = 0.2,
          verbose: bool = True) -> dict[str, Any]:
    """Train both tasks on `frame` and return artifacts plus a metrics report."""
    if TARGET_COLUMN not in frame.columns:
        raise ValueError(
            f"Training data must contain the '{TARGET_COLUMN}' column."
        )

    frame = frame.dropna(subset=[TARGET_COLUMN]).reset_index(drop=True)

    X_raw = prepare_features(frame)
    y_los = frame[TARGET_COLUMN].astype(float).to_numpy()
    y_tier = np.array([risk_tier_index(los_to_risk_tier(v)) for v in y_los])

    X_train_raw, X_test_raw, y_los_train, y_los_test, y_tier_train, y_tier_test = (
        train_test_split(
            X_raw, y_los, y_tier,
            test_size=test_size, random_state=RANDOM_STATE, stratify=y_tier,
        )
    )

    # Fit the preprocessor once, on training data only.
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    names = feature_names(preprocessor)

    if verbose:
        _banner("Data")
        print(f"  Records           {len(frame):,}")
        print(f"  Train / test      {len(X_train):,} / {len(X_test):,}")
        print(f"  Encoded features  {len(names)}")
        print(f"  Mean LOS          {y_los.mean():.2f} days "
              f"(sd {y_los.std():.2f})")

    reg_results, best_reg_name, best_reg = _train_regressors(
        X_train, y_los_train, X_test, y_los_test, verbose
    )
    clf_results, best_clf_name, best_clf, clf_detail = _train_classifiers(
        X_train, y_tier_train, X_test, y_tier_test, verbose
    )

    return {
        "preprocessor": preprocessor,
        "regressor": best_reg,
        "classifier": best_clf,
        "feature_names": names,
        "metrics": {
            "regression": reg_results,
            "classification": clf_results,
            "best_regressor": best_reg_name,
            "best_classifier": best_clf_name,
            "classification_detail": clf_detail,
        },
        "training_rows": int(len(frame)),
        "test_rows": int(len(X_test)),
        # Background sample for the SHAP explainer, kept small so that
        # explanations stay inside the 2s latency budget.
        "background": X_train[
            np.random.default_rng(RANDOM_STATE).choice(
                len(X_train), size=min(200, len(X_train)), replace=False
            )
        ],
    }


def _train_regressors(X_train, y_train, X_test, y_test, verbose):
    results = {}
    fitted = {}

    if verbose:
        _banner("Length-of-stay regression")
        print(f"  {'Model':<22}{'RMSE':>9}{'MAE':>9}{'R2':>9}")
        print("  " + "-" * 49)

    for name, model in regressors().items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        results[name] = {
            "rmse": round(rmse, 4),
            "mae": round(float(mean_absolute_error(y_test, pred)), 4),
            "r2": round(float(r2_score(y_test, pred)), 4),
        }
        fitted[name] = model
        if verbose:
            r = results[name]
            print(f"  {name:<22}{r['rmse']:>9.3f}{r['mae']:>9.3f}{r['r2']:>9.4f}")

    best = min(results, key=lambda n: results[n]["rmse"])
    if verbose:
        print(f"\n  Selected: {best} (RMSE {results[best]['rmse']:.3f} days)")
    return results, best, fitted[best]


def _train_classifiers(X_train, y_train, X_test, y_test, verbose):
    results = {}
    fitted = {}
    detail = {}

    if verbose:
        _banner("Discharge-risk tier classification")
        print(f"  {'Model':<22}{'Accuracy':>10}{'Macro F1':>10}"
              f"{'Weighted F1':>13}")
        print("  " + "-" * 55)

    present = sorted(set(y_train) | set(y_test))
    target_names = [RISK_TIER_LABELS[i] for i in present]

    for name, model in classifiers().items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        report = classification_report(
            y_test, pred, labels=present, target_names=target_names,
            output_dict=True, zero_division=0,
        )
        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
            "weighted_f1": round(float(report["weighted avg"]["f1-score"]), 4),
        }
        detail[name] = {
            "per_tier": {
                tier: {
                    "precision": round(report[tier]["precision"], 4),
                    "recall": round(report[tier]["recall"], 4),
                    "f1": round(report[tier]["f1-score"], 4),
                    "support": int(report[tier]["support"]),
                }
                for tier in target_names
            },
            "confusion_matrix": confusion_matrix(
                y_test, pred, labels=present
            ).tolist(),
            "labels": target_names,
        }
        fitted[name] = model
        if verbose:
            r = results[name]
            print(f"  {name:<22}{r['accuracy']:>10.4f}{r['macro_f1']:>10.4f}"
                  f"{r['weighted_f1']:>13.4f}")

    best = min(
        results,
        key=lambda n: (-results[n]["accuracy"], -results[n]["macro_f1"]),
    )
    if verbose:
        print(f"\n  Selected: {best} (accuracy {results[best]['accuracy']:.2%})")
        _print_confusion(detail[best])
    return results, best, fitted[best], detail


def _print_confusion(detail: dict) -> None:
    labels = detail["labels"]
    matrix = detail["confusion_matrix"]
    width = max(len(x) for x in labels) + 2

    print("\n  Confusion matrix (rows = actual, columns = predicted)")
    header = " " * (width + 2) + "".join(f"{name[:9]:>11}" for name in labels)
    print(header)
    for label, row in zip(labels, matrix, strict=False):
        cells = "".join(f"{v:>11,}" for v in row)
        print(f"  {label:<{width}}{cells}")

    print(f"\n  {'Tier':<{width}}{'Precision':>11}{'Recall':>9}{'F1':>9}{'Support':>10}")
    for tier, stats in detail["per_tier"].items():
        print(f"  {tier:<{width}}{stats['precision']:>11.3f}"
              f"{stats['recall']:>9.3f}{stats['f1']:>9.3f}{stats['support']:>10,}")


def _banner(title: str) -> None:
    print(f"\n{title}")
    print("=" * 60)


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def save_artifacts(artifacts: dict[str, Any], models_dir: Path = MODELS_DIR,
                   source: str = "synthetic") -> str:
    """
    Write a versioned artifact set and mark it as current.

    Layout:
        models/latest.json                     -> {"version": "..."}
        models/<version>/preprocessor.pkl
        models/<version>/regressor.pkl
        models/<version>/classifier.pkl
        models/<version>/background.pkl
        models/<version>/metadata.json
    """
    version = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = models_dir / version
    target.mkdir(parents=True, exist_ok=True)

    joblib.dump(artifacts["preprocessor"], target / "preprocessor.pkl")
    joblib.dump(artifacts["regressor"], target / "regressor.pkl")
    joblib.dump(artifacts["classifier"], target / "classifier.pkl")
    joblib.dump(artifacts["background"], target / "background.pkl")

    metadata = {
        "version": version,
        "trained_at": datetime.now(UTC).isoformat(),
        "data_source": source,
        "training_rows": artifacts["training_rows"],
        "test_rows": artifacts["test_rows"],
        "feature_names": artifacts["feature_names"],
        "risk_tiers": RISK_TIER_LABELS,
        "metrics": artifacts["metrics"],
        "environment": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    (target / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (models_dir / "latest.json").write_text(json.dumps({"version": version}, indent=2))

    return version


def main() -> None:
    parser = argparse.ArgumentParser(description="Train LOS and risk-tier models.")
    parser.add_argument("--rows", type=int, default=8000,
                        help="Synthetic rows to generate when no --data is given.")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to a CSV/Excel training file.")
    parser.add_argument("--seed", type=int, default=RANDOM_STATE)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    if args.data:
        path = Path(args.data)
        frame = (pd.read_excel(path) if path.suffix in {".xlsx", ".xls"}
                 else pd.read_csv(path))
        frame.columns = [str(c).strip().lower().replace(" ", "_")
                         for c in frame.columns]
        source = str(path)
        print(f"Training on {path} ({len(frame):,} rows)")
    else:
        frame = generate_dataset(args.rows, args.seed)
        source = f"synthetic (rows={args.rows}, seed={args.seed})"
        print(f"Training on {args.rows:,} synthetic admissions")

    artifacts = train(frame, test_size=args.test_size)
    version = save_artifacts(artifacts, source=source)

    metrics = artifacts["metrics"]
    best_reg = metrics["regression"][metrics["best_regressor"]]
    best_clf = metrics["classification"][metrics["best_classifier"]]

    _banner("Saved")
    print(f"  Version           {version}")
    print(f"  Location          models/{version}/")
    print(f"  LOS model         {metrics['best_regressor']} "
          f"(RMSE {best_reg['rmse']:.3f} d, R2 {best_reg['r2']:.4f})")
    print(f"  Risk model        {metrics['best_classifier']} "
          f"(accuracy {best_clf['accuracy']:.2%})")
    print()


if __name__ == "__main__":
    main()
