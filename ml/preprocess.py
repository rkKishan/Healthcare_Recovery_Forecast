"""
Preprocessing built as a single sklearn ColumnTransformer.

The transformer is fitted exactly once during training and persisted next to
the model. Inference loads it and only ever calls `.transform()`, so training
and serving cannot drift apart.

Unseen categorical values at inference are absorbed by
`OneHotEncoder(handle_unknown="ignore")`, which emits an all-zero block for an
unrecognised category rather than raising.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .schema import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES

UNKNOWN_CATEGORY = "Unknown"


def build_preprocessor() -> ColumnTransformer:
    """Construct the (unfitted) feature pipeline."""
    numeric = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )

    categorical = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="constant", fill_value=UNKNOWN_CATEGORY)),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False,
                                     min_frequency=5)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Select and normalise the model's input columns from an arbitrary frame.

    Handles the messy realities of an uploaded file: missing optional columns,
    stray whitespace, numeric columns arriving as text. The result always has
    exactly `FEATURE_COLUMNS`, in order, which is what the fitted
    ColumnTransformer expects.
    """
    prepared = pd.DataFrame(index=frame.index)

    for col in NUMERIC_FEATURES:
        if col in frame.columns:
            prepared[col] = pd.to_numeric(frame[col], errors="coerce")
        else:
            prepared[col] = np.nan

    for col in CATEGORICAL_FEATURES:
        if col in frame.columns:
            series = frame[col].astype("object").where(frame[col].notna(), None)
            series = pd.Series(
                [str(v).strip() if v is not None else None for v in series],
                index=frame.index,
                dtype="object",
            )
            prepared[col] = series.replace({"": None, "nan": None, "None": None})
        else:
            prepared[col] = None

    return prepared[FEATURE_COLUMNS]


def feature_names(preprocessor: ColumnTransformer) -> list[str]:
    """Human-readable names for the transformed matrix columns."""
    return [str(n) for n in preprocessor.get_feature_names_out()]


def describe_feature(name: str) -> str:
    """
    Turn an encoded feature name into plain language for the explanation view.

    `department_Oncology` becomes "Department is Oncology"; `age` stays "Age".
    """
    labels = {
        "age": "Age",
        "comorbidity_count": "Comorbidity count",
        "prior_admissions": "Prior admissions",
    }
    if name in labels:
        return labels[name]

    for col in CATEGORICAL_FEATURES:
        prefix = f"{col}_"
        if name.startswith(prefix):
            value = name[len(prefix):]
            readable = col.replace("_", " ").capitalize()
            if value == "infrequent_sklearn":
                return f"{readable} is an uncommon value"
            return f"{readable} is {value}"

    return name.replace("_", " ").capitalize()
