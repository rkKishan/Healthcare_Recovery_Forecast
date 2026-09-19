"""Dataset upload, listing, and preview."""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
from flask import Blueprint, current_app, g, request
from werkzeug.utils import secure_filename

from ml.validator import DatasetValidationError, read_tabular, validate

from ..auth import requires_auth, requires_capability
from ..errors import ApiError
from ..models import Dataset, db
from ..roles import DATASET_UPLOAD

bp = Blueprint("dataset", __name__, url_prefix="/api/dataset")

PREVIEW_ROWS = 10


@bp.post("/upload")
@requires_auth
@requires_capability(DATASET_UPLOAD)
def upload():
    if "file" not in request.files:
        raise ApiError(
            "No file was included in the request.", 400,
            hint="Send the file as multipart/form-data under the key 'file'.",
        )

    upload_file = request.files["file"]
    if not upload_file.filename:
        raise ApiError("No file was selected.", 400)

    filename = secure_filename(upload_file.filename)
    suffix = Path(filename).suffix.lower()
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    if suffix not in allowed:
        raise ApiError(
            f"'{suffix or 'unknown'}' files are not supported.", 415,
            details=[f"Received '{filename}'."],
            hint=f"Upload one of: {', '.join(sorted(allowed))}.",
        )

    raw = upload_file.read()
    if not raw:
        raise ApiError("The uploaded file is empty.", 400)

    # read_tabular and validate raise DatasetValidationError, which the
    # global handler renders as a 422 with specific guidance.
    frame = read_tabular(raw, filename)
    frame, report = validate(frame)

    upload_dir: Path = current_app.config["UPLOAD_DIR"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    stored_path.write_bytes(raw)

    dataset = Dataset(
        user_id=g.current_user.id,
        filename=filename,
        stored_path=str(stored_path),
        row_count=report.row_count,
        column_count=report.column_count,
        has_target=report.has_target,
        quality_report=report.to_dict(),
    )
    db.session.add(dataset)
    db.session.commit()

    return {
        "dataset_id": dataset.id,
        "filename": filename,
        "quality_report": report.to_dict(),
        "preview": _preview(frame),
        "message": (
            f"{report.row_count:,} records validated successfully."
            if report.has_target
            else f"{report.row_count:,} records validated. No "
                 f"'length_of_stay' column, so this file can be scored but "
                 f"not used for training."
        ),
    }, 201


@bp.get("")
@requires_auth
def list_datasets():
    datasets = (
        Dataset.query.filter_by(user_id=g.current_user.id)
        .order_by(Dataset.uploaded_at.desc())
        .limit(50)
        .all()
    )
    return {"datasets": [d.to_dict() for d in datasets]}


@bp.get("/<int:dataset_id>/preview")
@requires_auth
def preview(dataset_id: int):
    dataset = _owned_dataset(dataset_id)
    frame = load_dataset_frame(dataset)
    return {
        "dataset_id": dataset.id,
        "filename": dataset.filename,
        "preview": _preview(frame),
        "quality_report": dataset.quality_report,
    }


def _owned_dataset(dataset_id: int) -> Dataset:
    dataset = Dataset.query.filter_by(
        id=dataset_id, user_id=g.current_user.id
    ).first()
    if dataset is None:
        raise ApiError(f"Dataset {dataset_id} was not found.", 404)
    return dataset


def load_dataset_frame(dataset: Dataset) -> pd.DataFrame:
    """Re-read a stored upload from disk, re-running validation."""
    path = Path(dataset.stored_path)
    if not path.exists():
        raise ApiError(
            f"The stored file for dataset {dataset.id} is missing from disk.",
            410,
            hint="Upload the file again.",
        )
    frame = read_tabular(path.read_bytes(), dataset.filename)
    try:
        frame, _ = validate(frame)
    except DatasetValidationError as exc:
        raise ApiError(
            f"Stored dataset {dataset.id} no longer passes validation.",
            422, details=exc.errors,
        ) from exc
    return frame


def _preview(frame: pd.DataFrame) -> dict:
    head = frame.head(PREVIEW_ROWS)
    return {
        "columns": [str(c) for c in head.columns],
        "rows": [
            [None if pd.isna(v) else _jsonable(v) for v in row]
            for row in head.itertuples(index=False, name=None)
        ],
        "total_rows": int(len(frame)),
    }


def _jsonable(value):
    if hasattr(value, "item"):
        return value.item()
    return str(value) if not isinstance(value, int | float | bool | str) else value
