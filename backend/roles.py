"""
Account roles and what each one is allowed to do.

The two clinical roles look at the same hospital from opposite ends:

  * a **doctor** works one admission at a time -- score this patient, read the
    drivers, hand the ward round a discharge date;
  * an **analyst** works the whole cohort -- load an extract, project bed
    occupancy, check whether the model is still trustworthy.

Keeping the mapping here rather than scattering role checks through the route
modules means the API and the UI cannot disagree about who sees what: the
capability list travels to the browser inside `User.to_dict()`, and the
frontend builds its navigation from it instead of hard-coding a second copy of
these rules.
"""

from __future__ import annotations

DOCTOR = "doctor"
ANALYST = "analyst"
ADMIN = "admin"

ALL_ROLES: tuple[str, ...] = (DOCTOR, ANALYST, ADMIN)

# What a self-registering account is allowed to pick. `admin` is deliberately
# absent: elevating an account stays an administrative act, never a field the
# registrant fills in.
SELF_SELECTABLE: frozenset[str] = frozenset({DOCTOR, ANALYST})

DEFAULT_ROLE = DOCTOR

# Rows written before the split stored the single role "clinician". Mapping it
# here means an existing database keeps working without a data migration being
# the thing that decides whether someone can log in.
ALIASES: dict[str, str] = {"clinician": DOCTOR, "physician": DOCTOR}

ROLE_LABELS: dict[str, str] = {
    DOCTOR: "Doctor",
    ANALYST: "Analyst",
    ADMIN: "Administrator",
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    DOCTOR: "Score individual admissions, read the drivers behind a stay, and "
            "track your own caseload towards discharge.",
    ANALYST: "Load admission extracts, project ward occupancy, and monitor "
             "model performance across the whole cohort.",
    ADMIN: "Everything both clinical roles can do.",
}

# --- capabilities ---------------------------------------------------------
# One string per thing a user can do. Routes ask for these, never for a role,
# so adding a fourth role later is a change to this file alone.

PATIENT_PREDICT = "patient.predict"      # score a single admission
PATIENT_REPORT = "patient.report"        # the per-patient clinical PDF
CASELOAD_VIEW = "caseload.view"          # the doctor's own worklist
CASELOAD_REPORT = "caseload.report"      # the ward-round handover PDF
DATASET_UPLOAD = "dataset.upload"        # ingest an admissions extract
COHORT_VIEW = "cohort.view"              # cohort KPIs and the bed forecast
COHORT_REPORT = "cohort.report"          # the capacity-planning PDF
MODEL_INSPECT = "model.inspect"          # metrics and global feature importance

DOCTOR_CAPABILITIES: tuple[str, ...] = (
    PATIENT_PREDICT,
    PATIENT_REPORT,
    CASELOAD_VIEW,
    CASELOAD_REPORT,
)

ANALYST_CAPABILITIES: tuple[str, ...] = (
    DATASET_UPLOAD,
    COHORT_VIEW,
    COHORT_REPORT,
    MODEL_INSPECT,
)

CAPABILITIES: dict[str, tuple[str, ...]] = {
    DOCTOR: DOCTOR_CAPABILITIES,
    ANALYST: ANALYST_CAPABILITIES,
    ADMIN: DOCTOR_CAPABILITIES + ANALYST_CAPABILITIES,
}


def normalise(value: object) -> str | None:
    """Canonical role name for `value`, or None if it is not a known role."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    cleaned = ALIASES.get(cleaned, cleaned)
    return cleaned if cleaned in ALL_ROLES else None


def coerce_signup_role(value: object) -> str:
    """
    The role a self-registering caller ends up with.

    Anything outside `SELF_SELECTABLE` -- "admin", a typo, or nothing at all --
    quietly becomes the default rather than being honoured or raising. A
    caller who asks for admin must not be able to tell the difference between
    that request being ignored and the field not existing.
    """
    role = normalise(value)
    return role if role in SELF_SELECTABLE else DEFAULT_ROLE


def label(role: str) -> str:
    return ROLE_LABELS.get(normalise(role) or "", "User")


def capabilities_for(role: str) -> list[str]:
    return list(CAPABILITIES.get(normalise(role) or "", ()))


def has_capability(role: str, capability: str) -> bool:
    return capability in CAPABILITIES.get(normalise(role) or "", ())


def public_roles() -> list[dict]:
    """The role picker's options, so the sign-up form has one source of truth."""
    return [
        {
            "value": role,
            "label": ROLE_LABELS[role],
            "description": ROLE_DESCRIPTIONS[role],
            "capabilities": list(CAPABILITIES[role]),
        }
        for role in (DOCTOR, ANALYST)
    ]
