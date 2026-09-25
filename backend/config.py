"""Application configuration, sourced from environment variables."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _resolve(path_like: str | Path) -> Path:
    """Interpret a configured path relative to the project root, not the CWD."""
    path = Path(path_like)
    return path if path.is_absolute() else BASE_DIR / path


def _database_uri() -> str:
    """
    Build the SQLAlchemy URI, normalising the two forms that bite in practice.

    A relative SQLite path -- `sqlite:///data/app.db` -- is relative to the
    working directory, which breaks whenever the server starts from anywhere
    but the project root, so it is anchored here instead.

    A Postgres URL without a driver is worse, because it fails only in
    deployment. Every managed provider hands out `postgresql://...` (or the
    older `postgres://`), and SQLAlchemy reads a driverless Postgres URL as
    psycopg2. This project ships psycopg 3, so that URL imports a module that
    is not installed and the app dies at `db.init_app`, after a build that
    looked entirely healthy. Naming the driver here means a connection string
    can be pasted from Neon or Render exactly as given.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        return f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"

    # postgres:// is the legacy spelling several providers still emit.
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return f"postgresql+psycopg://{url[len(prefix):]}"

    prefix = "sqlite:///"
    if url.startswith(prefix):
        target = url[len(prefix):]
        if target and not target.startswith("/"):
            return f"{prefix}{_resolve(target)}"
    return url


# Placeholder secrets that have ever shipped in this repo's templates. A
# deployment still using one of these is signing JWTs with a value published
# on the internet, so anyone can forge a token for any account.
INSECURE_SECRETS = frozenset({
    "dev-secret-change-me",
    "change-me-in-production",
    "your-secret-key-here",
    "",
})


class Config:
    # --- security ------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "12"))

    # Debug is the switch that decides whether a placeholder secret is a
    # convenience (development) or a fatal misconfiguration (production).
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # --- auth rate limiting --------------------------------------------
    # Login is the one unauthenticated endpoint worth brute-forcing.
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5 per minute")
    REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "3 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    # --- database ------------------------------------------------------
    # Defaults to SQLite so the project runs with no external services.
    # Point DATABASE_URL at MySQL to switch, e.g.
    #   mysql+pymysql://user:password@localhost:3306/healthcare_forecast
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- uploads -------------------------------------------------------
    UPLOAD_DIR = _resolve(os.getenv("UPLOAD_DIR", BASE_DIR / "data" / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "64")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    # --- ml ------------------------------------------------------------
    MODELS_DIR = _resolve(os.getenv("MODELS_DIR", BASE_DIR / "models"))
    WARM_EXPLAINER = os.getenv("WARM_EXPLAINER", "true").lower() == "true"

    # --- hospital capacity, used by the bed forecast -------------------
    TOTAL_BEDS = int(os.getenv("TOTAL_BEDS", "0"))

    # --- google sign-in ------------------------------------------------
    # The OAuth *client id* only -- it is public by design and is sent to the
    # browser by /api/auth/config. No client secret is involved: the browser
    # runs Google Identity Services and posts back an ID token, which the API
    # verifies against Google's public keys.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    # Optional workspace lock. Empty means any verified Google account may
    # sign in; set it to keep the app to hospital-issued addresses.
    GOOGLE_ALLOWED_DOMAINS = [
        d.strip().lower()
        for d in os.getenv("GOOGLE_ALLOWED_DOMAINS", "").split(",")
        if d.strip()
    ]

    # --- assistant -----------------------------------------------------
    # The chat assistant is optional: with no key the endpoint reports itself
    # disabled and the UI omits the panel, rather than the app failing to boot.
    #
    # Groq rather than Mistral: its free tier issues real API quota without a
    # payment method, where Mistral's free plan reports a hard
    # x-ratelimit-limit-req-minute of 0 until pay-as-you-go is enabled.
    ASSISTANT_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

    # Pinned rather than an alias, so a provider-side model refresh cannot
    # silently change how the assistant behaves in a clinical setting.
    ASSISTANT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # --- cors ----------------------------------------------------------
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:9000").split(",")
        if o.strip()
    ]

    # --- administrators -------------------------------------------------
    # Admin is granted by this list and nothing else. It is server-side
    # configuration, so it cannot be influenced by anything a registrant
    # sends -- which is the whole reason `admin` is absent from the role
    # picker. An address here becomes an administrator when it registers, and
    # an existing account is promoted the next time it signs in, so the list
    # can be edited without touching the database.
    ADMIN_EMAILS = [
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    ]

    # --- demo seed accounts -------------------------------------------
    # One per role, so both dashboards can be opened on a fresh checkout
    # without anyone having to register first.
    DEMO_EMAIL = os.getenv("DEMO_EMAIL", "admin@hospital.org")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")
    DEMO_NAME = os.getenv("DEMO_NAME", "Dr. Alex Morgan")

    DEMO_DOCTOR_EMAIL = os.getenv("DEMO_DOCTOR_EMAIL", "doctor@hospital.org")
    DEMO_DOCTOR_NAME = os.getenv("DEMO_DOCTOR_NAME", "Dr. Priya Nair")
    DEMO_ANALYST_EMAIL = os.getenv("DEMO_ANALYST_EMAIL", "analyst@hospital.org")
    DEMO_ANALYST_NAME = os.getenv("DEMO_ANALYST_NAME", "Jordan Mehta")

    # These accounts share one published password, which is fine for a demo
    # and not fine anywhere real, so a deployment that has named its real
    # administrators in ADMIN_EMAILS does not seed them -- see
    # `resolve_demo_seeding`, which applies that at app creation because a
    # subclass may override either setting after this body has run.
    #
    # Tracking whether the variable was set at all keeps that default from
    # overruling someone who asked for seeding on purpose.
    SEED_DEMO_USERS = os.getenv("SEED_DEMO_USERS", "true").lower() == "true"
    SEED_DEMO_USERS_EXPLICIT = "SEED_DEMO_USERS" in os.environ


def resolve_demo_seeding(config: type[Config]) -> tuple[bool, str | None]:
    """
    Whether to seed the demo logins, and a line to log if the answer changed.

    Seeding runs on every boot and only skips accounts that already exist, so
    on a real deployment it is not merely untidy -- it puts the published
    password back after anyone deletes it. Naming real administrators is the
    clearest possible signal that a deployment is real, so that turns seeding
    off, and deleting the demo accounts then sticks.

    A deliberate SEED_DEMO_USERS still wins either way: the zero-setup Docker
    demo runs with debug off and no ADMIN_EMAILS, and keeps its logins.
    """
    if not config.SEED_DEMO_USERS or config.SEED_DEMO_USERS_EXPLICIT:
        return config.SEED_DEMO_USERS, None
    if config.DEBUG or not config.ADMIN_EMAILS:
        return True, None
    return False, (
        "Not seeding the demo accounts: ADMIN_EMAILS names this deployment's "
        "administrators, and the demo logins share a published password. Set "
        "SEED_DEMO_USERS=true to keep them anyway."
    )


def sqlite_in_use() -> bool:
    return Config.SQLALCHEMY_DATABASE_URI.startswith("sqlite")


def verify_production_config(config: type[Config]) -> None:
    """
    Refuse to start a non-debug server that is misconfigured in a way which
    silently weakens security.

    Failing loudly at boot is the point: a placeholder signing key produces a
    server that works perfectly and trusts forged tokens, which is far worse
    than one that will not start.
    """
    if config.DEBUG:
        return

    # SQLite is only a warning: it stays the documented zero-setup default for
    # the Docker demo, which runs with FLASK_DEBUG=false.
    if config.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        logging.getLogger(__name__).warning(
            "Running in production mode on SQLite. Point DATABASE_URL at "
            "MySQL/Postgres before serving concurrent writers."
        )

    problems = []
    if config.SECRET_KEY in INSECURE_SECRETS:
        problems.append(
            "SECRET_KEY is unset or still a placeholder. Generate one with: "
            'python -c "import secrets; print(secrets.token_hex(32))"'
        )

    if problems:
        raise RuntimeError(
            "Refusing to start with an insecure production configuration:\n"
            + "\n".join(f"  - {p}" for p in problems)
        )
