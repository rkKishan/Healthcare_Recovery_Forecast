"""SQLAlchemy models: users, uploaded datasets, and the prediction audit log."""

from __future__ import annotations

from datetime import UTC, datetime

from flask_sqlalchemy import SQLAlchemy

from .roles import DEFAULT_ROLE, capabilities_for
from .roles import label as role_label

db = SQLAlchemy()


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=DEFAULT_ROLE)

    # Nullable because a Google account has no password to hash. `auth_provider`
    # is what distinguishes "no password yet" from "password login is not how
    # this account signs in", which the login route needs in order to fail
    # with the right message.
    password_hash = db.Column(db.String(255), nullable=True)
    auth_provider = db.Column(db.String(32), nullable=False, default="password")

    # Google's `sub` claim, not the email: an address can be reassigned inside
    # a workspace, the subject identifier cannot.
    google_sub = db.Column(db.String(64), unique=True, nullable=True, index=True)
    avatar_url = db.Column(db.String(512), nullable=True)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    datasets = db.relationship("Dataset", back_populates="user",
                               cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        # `capabilities` ships with the user so the frontend renders its
        # navigation from the same mapping the API enforces, rather than
        # keeping a second copy of the rules that can drift out of step.
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "role_label": role_label(self.role),
            "capabilities": capabilities_for(self.role),
            "auth_provider": self.auth_provider,
            "avatar_url": self.avatar_url,
        }


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(512), nullable=False)
    row_count = db.Column(db.Integer, nullable=False)
    column_count = db.Column(db.Integer, nullable=False)
    has_target = db.Column(db.Boolean, default=False, nullable=False)
    # Full ValidationReport, kept so the upload summary survives a page reload.
    quality_report = db.Column(db.JSON, nullable=False, default=dict)
    uploaded_at = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="datasets")
    predictions = db.relationship("PredictionLog", back_populates="dataset",
                                  cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "dataset_id": self.id,
            "filename": self.filename,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "has_target": self.has_target,
            "uploaded_at": self.uploaded_at.isoformat(),
            "quality_report": self.quality_report,
        }


class PredictionLog(db.Model):
    """One row per served prediction, for auditability."""

    __tablename__ = "prediction_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=True,
                           index=True)
    patient_ref = db.Column(db.String(64), nullable=True)

    input_payload = db.Column(db.JSON, nullable=False, default=dict)
    los_days = db.Column(db.Float, nullable=False)
    risk_tier = db.Column(db.String(32), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(64), nullable=False)
    latency_ms = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)

    dataset = db.relationship("Dataset", back_populates="predictions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "patient_ref": self.patient_ref,
            "los_days": self.los_days,
            "risk_tier": self.risk_tier,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat(),
        }
