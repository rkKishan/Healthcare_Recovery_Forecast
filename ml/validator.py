"""
Schema validation for uploaded datasets.

The goal is that a clinician uploading the wrong spreadsheet gets a sentence
telling them exactly what to fix, never a stack trace. Every failure path here
produces a `DatasetValidationError` carrying structured, human-readable detail.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pandas as pd

from .schema import (
    CATEGORICAL_FEATURES,
    COLUMN_SPECS,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)

MAX_ROWS = 500_000


class DatasetValidationError(Exception):
    """Raised when an uploaded file cannot be used. Carries API-ready detail."""

    def __init__(self, message: str, errors: list[str] | None = None,
                 hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
        self.hint = hint

    def to_dict(self) -> dict:
        payload = {"error": self.message, "details": self.errors}
        if self.hint:
            payload["hint"] = self.hint
        return payload


@dataclass
class ValidationReport:
    """Data-quality summary returned alongside a successful upload."""

    row_count: int
    column_count: int
    detected_columns: list[str]
    missing_values: dict[str, int]
    has_target: bool
    extra_columns: list[str] = field(default_factory=list)
    coerced_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    numeric_summary: dict[str, dict] = field(default_factory=dict)
    category_counts: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "detected_columns": self.detected_columns,
            "missing_values": self.missing_values,
            "total_missing_values": int(sum(self.missing_values.values())),
            "has_target": self.has_target,
            "usable_for_training": self.has_target,
            "extra_columns": self.extra_columns,
            "coerced_columns": self.coerced_columns,
            "warnings": self.warnings,
            "numeric_summary": self.numeric_summary,
            "category_counts": self.category_counts,
        }


def read_tabular(raw: bytes, filename: str) -> pd.DataFrame:
    """Parse an uploaded CSV/Excel byte payload into a DataFrame."""
    name = (filename or "").lower()

    try:
        if name.endswith((".xlsx", ".xls")):
            frame = pd.read_excel(io.BytesIO(raw))
        elif name.endswith(".csv"):
            frame = pd.read_csv(io.BytesIO(raw))
        else:
            raise DatasetValidationError(
                "Unsupported file type.",
                [f"'{filename}' is not a recognised format."],
                hint="Upload a .csv, .xlsx, or .xls file.",
            )
    except DatasetValidationError:
        raise
    except UnicodeDecodeError:
        raise DatasetValidationError(
            "The file could not be decoded as text.",
            ["The CSV is not valid UTF-8 — it may be a corrupted or binary file."],
            hint="Re-export the file from Excel using 'CSV UTF-8'.",
        ) from None
    except pd.errors.EmptyDataError:
        raise DatasetValidationError(
            "The file is empty.",
            ["No rows or columns were found."],
        ) from None
    except pd.errors.ParserError as exc:
        raise DatasetValidationError(
            "The file could not be parsed as a table.",
            [f"Parser stopped at: {exc}".strip()],
            hint="Check for inconsistent column counts or stray delimiters.",
        ) from None
    except Exception as exc:  # noqa: BLE001 - surfaced as a clean message
        raise DatasetValidationError(
            "The file could not be read.",
            [str(exc)],
        ) from None

    frame.columns = [str(c).strip().lower().replace(" ", "_") for c in frame.columns]
    return frame


def validate(frame: pd.DataFrame, *, require_target: bool = False) -> tuple[pd.DataFrame, ValidationReport]:
    """
    Check a parsed frame against the canonical schema.

    Returns the cleaned frame plus a data-quality report. Raises
    `DatasetValidationError` with specific, actionable messages on failure.
    """
    if frame.empty:
        raise DatasetValidationError(
            "The file contains no data rows.",
            ["The header was read successfully but there are zero records beneath it."],
        )

    if len(frame) > MAX_ROWS:
        raise DatasetValidationError(
            f"The file has too many rows ({len(frame):,}).",
            [f"The maximum supported size is {MAX_ROWS:,} rows."],
            hint="Split the export into smaller batches.",
        )

    present = set(frame.columns)

    # ---- missing columns ------------------------------------------------
    required = list(FEATURE_COLUMNS)
    if require_target:
        required.append(TARGET_COLUMN)

    missing = [c for c in required if c not in present]
    if missing:
        details = []
        for col in missing:
            spec = COLUMN_SPECS[col]
            near = _closest_match(col, present)
            line = f"Missing required column '{col}' — {spec.description}."
            if near:
                line += f" Did you mean '{near}'?"
            elif spec.examples:
                line += f" Expected values like {', '.join(spec.examples[:3])}."
            details.append(line)
        raise DatasetValidationError(
            f"{len(missing)} required column{'s' if len(missing) > 1 else ''} "
            f"{'are' if len(missing) > 1 else 'is'} missing: {', '.join(missing)}.",
            details,
            hint=f"A valid file needs these columns: {', '.join(required)}.",
        )

    frame = frame.copy()
    coerced: list[str] = []
    warnings: list[str] = []

    # ---- type checks ----------------------------------------------------
    numeric_targets = list(NUMERIC_FEATURES)
    if TARGET_COLUMN in frame.columns:
        numeric_targets.append(TARGET_COLUMN)

    type_errors: list[str] = []
    for col in numeric_targets:
        original = frame[col]
        converted = pd.to_numeric(original, errors="coerce")

        # Values that were non-null before conversion but null after were junk.
        broke = original.notna() & converted.isna()
        if broke.any():
            bad_rows = frame.index[broke][:3]
            samples = ", ".join(f"'{original.loc[i]}'" for i in bad_rows)
            type_errors.append(
                f"Column '{col}' must be numeric but {int(broke.sum())} value(s) "
                f"could not be read as numbers (e.g. {samples} on row "
                f"{int(bad_rows[0]) + 2})."
            )
            continue

        if not pd.api.types.is_numeric_dtype(original):
            coerced.append(col)
        frame[col] = converted

    if type_errors:
        raise DatasetValidationError(
            "Some columns have the wrong data type.",
            type_errors,
            hint="Remove text, units, or thousands separators from numeric columns.",
        )

    # ---- target sanity --------------------------------------------------
    has_target = TARGET_COLUMN in frame.columns
    if has_target:
        target = frame[TARGET_COLUMN]
        if target.notna().sum() == 0:
            raise DatasetValidationError(
                f"Column '{TARGET_COLUMN}' is present but entirely empty.",
                ["Training requires an observed length of stay for each record."],
            )
        if (target.dropna() < 0).any():
            raise DatasetValidationError(
                f"Column '{TARGET_COLUMN}' contains negative values.",
                [f"{int((target.dropna() < 0).sum())} record(s) have a length of "
                 f"stay below zero, which is not a valid duration."],
            )

    # ---- range warnings (non-fatal) -------------------------------------
    for col in numeric_targets:
        spec = COLUMN_SPECS[col]
        if spec.minimum is None:
            continue
        series = frame[col].dropna()
        out_of_range = ((series < spec.minimum) | (series > spec.maximum)).sum()
        if out_of_range:
            warnings.append(
                f"{int(out_of_range)} value(s) in '{col}' fall outside the expected "
                f"range {spec.range_text}."
            )

    for col in CATEGORICAL_FEATURES:
        frame[col] = frame[col].astype("string").str.strip()
        blank = frame[col].isna().sum()
        if blank:
            warnings.append(
                f"{int(blank)} record(s) have no value for '{col}'; they will be "
                f"treated as 'Unknown'."
            )

    all_missing = [c for c in required if frame[c].isna().all()]
    if all_missing:
        raise DatasetValidationError(
            f"Column(s) {', '.join(all_missing)} contain no usable values.",
            [f"Every row in '{c}' is blank." for c in all_missing],
        )

    report = ValidationReport(
        row_count=int(len(frame)),
        column_count=int(len(frame.columns)),
        detected_columns=[str(c) for c in frame.columns],
        missing_values={str(c): int(n) for c, n in frame.isna().sum().items() if n},
        has_target=has_target,
        extra_columns=sorted(present - set(required) - {"patient_id"}),
        coerced_columns=coerced,
        warnings=warnings,
        numeric_summary=_numeric_summary(frame, numeric_targets),
        category_counts=_category_counts(frame),
    )
    return frame, report


def _numeric_summary(frame: pd.DataFrame, columns: list[str]) -> dict[str, dict]:
    summary = {}
    for col in columns:
        series = frame[col].dropna()
        if series.empty:
            continue
        summary[col] = {
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
            "mean": round(float(series.mean()), 2),
            "median": round(float(series.median()), 2),
        }
    return summary


def _category_counts(frame: pd.DataFrame) -> dict[str, dict]:
    counts = {}
    for col in CATEGORICAL_FEATURES:
        if col not in frame.columns:
            continue
        top = frame[col].value_counts().head(8)
        counts[col] = {str(k): int(v) for k, v in top.items()}
    return counts


def _closest_match(target: str, candidates: set[str]) -> str | None:
    """Suggest a likely typo fix for a missing column name."""
    import difflib

    matches = difflib.get_close_matches(target, list(candidates), n=1, cutoff=0.7)
    return matches[0] if matches else None
