"""
Flask application factory.

    python -m backend.app          # development server on :2800
    gunicorn "backend.app:create_app()"
"""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate

# Make the repository root importable so `ml` resolves when the backend is
# launched from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .config import Config, verify_production_config  # noqa: E402
from .errors import register_error_handlers  # noqa: E402
from .models import User, db  # noqa: E402
from .ratelimit import limiter, rate_limited  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("backend")

migrate = Migrate()

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    # Before anything is wired up: refuse to boot a production server that is
    # still signing tokens with a placeholder key.
    verify_production_config(config)

    _ensure_directories(app)

    db.init_app(app)
    migrate.init_app(app, db, directory=str(MIGRATIONS_DIR))
    limiter.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})

    from .routes.auth_routes import bp as auth_bp
    from .routes.chat_routes import bp as chat_bp
    from .routes.dashboard_routes import bp as dashboard_bp
    from .routes.dataset_routes import bp as dataset_bp
    from .routes.predict_routes import bp as predict_bp
    from .routes.report_routes import bp as report_bp

    for blueprint in (
        auth_bp, dataset_bp, predict_bp, dashboard_bp, report_bp, chat_bp,
    ):
        app.register_blueprint(blueprint)

    register_error_handlers(app)
    app.register_error_handler(429, rate_limited)

    with app.app_context():
        _initialise_schema(app)
        _seed_demo_user(app)

    if app.config["WARM_EXPLAINER"]:
        _warm_models_async()

    # Everything the API serves lives under /api so that the single-page app
    # can own every other path -- /dashboard is a page, /api/dashboard is data.
    @app.get("/api/health")
    def health():
        from ml.predictor import is_ready

        return jsonify({
            "status": "ok",
            "model_trained": is_ready(),
            "database": app.config["SQLALCHEMY_DATABASE_URI"].split("://")[0],
        })

    _register_spa(app)

    return app


def _register_spa(app: Flask) -> None:
    """
    Serve the built single-page app when `frontend/dist` is present.

    In development the Vite server owns the browser and proxies /api here, so
    this does nothing. In the Docker image the build output is present and
    Flask serves both halves from one origin.
    """
    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

    if not dist.is_dir():
        @app.get("/")
        def index():
            return jsonify({
                "service": "Healthcare Recovery Forecast API",
                "endpoints": [
                    "GET  /api/auth/config",
                    "POST /api/auth/login",
                    "POST /api/auth/register",
                    "POST /api/auth/google",
                    "GET  /api/auth/me",
                    "POST /api/dataset/upload",
                    "GET  /api/dataset",
                    "GET  /api/dataset/<id>/preview",
                    "POST /api/predict",
                    "GET  /api/predict/model",
                    "GET  /api/predict/schema",
                    "GET  /api/predict/explain/global",
                    "GET  /api/dashboard/kpis",
                    "GET  /api/dashboard/clinical",
                    "GET  /api/reports/caseload.pdf",
                    "GET  /api/reports/cohort.pdf",
                    "POST /api/reports/patient.pdf",
                    "GET  /api/dashboard/predictions",
                    "GET  /api/health",
                ],
            })
        return

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path: str):
        # A real asset is served as-is; every other path is a client-side
        # route and gets index.html so deep links survive a hard refresh.
        if path and (dist / path).is_file():
            return send_from_directory(dist, path)
        return send_from_directory(dist, "index.html")


def _initialise_schema(app: Flask) -> None:
    """
    Bring the database up to the current schema, where that is unambiguously
    safe, and otherwise say what to run.

    Alembic is the source of truth: it is what carries an added column to an
    existing deployment instead of letting the database drift from the models.
    Applying it automatically is only safe in two states, so this checks which
    one it is in rather than assuming.

    An unstamped database that already has tables is left strictly alone --
    running the initial migration against it would try to re-create those
    tables and fail, including during the very `flask db stamp` that fixes it.
    """
    from alembic.migration import MigrationContext
    from sqlalchemy import inspect

    if app.config.get("TESTING"):
        # Throwaway in-memory database; replaying history buys nothing.
        db.create_all()
        return

    if not (MIGRATIONS_DIR / "env.py").is_file():
        logger.warning(
            "No migrations found at %s; creating tables directly.", MIGRATIONS_DIR
        )
        db.create_all()
        return

    inspector = inspect(db.engine)
    existing = set(inspector.get_table_names()) - {"alembic_version"}

    with db.engine.connect() as connection:
        stamped = MigrationContext.configure(connection).get_current_revision()

    if existing and stamped is None:
        logger.warning(
            "Database has tables but no Alembic revision, so it is not under "
            "migration control. Adopt it with:  flask db stamp head"
        )
        return

    from flask_migrate import upgrade

    # Safe here: either the database is empty, or it is already stamped and
    # Alembic knows exactly which revisions remain.
    upgrade(directory=str(MIGRATIONS_DIR))


def _ensure_directories(app: Flask) -> None:
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_path = Path(app.config["SQLALCHEMY_DATABASE_URI"].removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)


def _seed_demo_user(app: Flask) -> None:
    """
    Create one demo login per role on first run, so both dashboards can be
    opened on a fresh checkout without registering first.

    These accounts share one published password, so the administrator among
    them is only created as an administrator on a deployment that has not
    named its real ones. See `accounts` below.
    """
    from sqlalchemy import inspect

    from .auth import hash_password
    from .roles import ADMIN, ANALYST, DEFAULT_ROLE, DOCTOR

    if not app.config.get("SEED_DEMO_USERS", True):
        return

    # The app object is also constructed by `flask db` commands, which run
    # before any table exists. Seeding is a convenience, never a reason for a
    # migration command to fail.
    if not inspect(db.engine).has_table(User.__tablename__):
        logger.info("Users table not present yet; skipping demo seed.")
        return

    # Once ADMIN_EMAILS names real administrators, that list is the only thing
    # that grants admin -- so the demo account drops to the default clinical
    # role. Without this, a deployment that had carefully locked admin down to
    # three addresses would still boot with a fourth administrator whose
    # password is published in the README, recreated on every restart because
    # seeding runs on boot and only skips accounts that already exist.
    demo_admin_role = DEFAULT_ROLE if app.config.get("ADMIN_EMAILS") else ADMIN

    accounts = (
        (app.config["DEMO_EMAIL"], app.config["DEMO_NAME"], demo_admin_role),
        (app.config["DEMO_DOCTOR_EMAIL"], app.config["DEMO_DOCTOR_NAME"], DOCTOR),
        (app.config["DEMO_ANALYST_EMAIL"], app.config["DEMO_ANALYST_NAME"], ANALYST),
    )

    # One hash for all three: bcrypt is deliberately slow, and doing it per
    # account adds a third of a second to every boot for no benefit.
    password_hash = hash_password(app.config["DEMO_PASSWORD"])

    seeded = []
    for raw_email, full_name, role in accounts:
        email = raw_email.lower()
        if User.query.filter_by(email=email).first():
            continue
        db.session.add(
            User(
                email=email,
                full_name=full_name,
                role=role,
                password_hash=password_hash,
                auth_provider="password",
            )
        )
        seeded.append(f"{email} ({role})")

    if seeded:
        db.session.commit()
        logger.info("Seeded demo accounts: %s", ", ".join(seeded))


def _warm_models_async() -> None:
    """
    Build the SHAP explainer in the background at startup.

    Constructing TreeExplainer takes about a second; doing it here keeps the
    first real /predict call inside the 2s latency budget.
    """

    def warm():
        try:
            from ml.predictor import get_predictor

            predictor = get_predictor()
            _ = predictor.explainer
            logger.info("Model %s loaded and explainer warmed.", predictor.version)
        except Exception as exc:  # noqa: BLE001 - startup must not fail here
            logger.warning("Model not preloaded: %s", exc)

    threading.Thread(target=warm, daemon=True).start()


if __name__ == "__main__":
    import os

    create_app().run(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "2800")),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
    )
