"""
Role separation: what a doctor can reach, what an analyst can reach, and the
guarantee that the two sets are actually enforced by the API rather than only
hidden in the UI.
"""

from __future__ import annotations

import io

import pytest

from backend.roles import (
    ADMIN,
    ANALYST,
    CAPABILITIES,
    DEFAULT_ROLE,
    DOCTOR,
    SELF_SELECTABLE,
    capabilities_for,
    coerce_signup_role,
    has_capability,
    normalise,
)

PATIENT = {
    "age": 71,
    "gender": "F",
    "admission_type": "Emergency",
    "diagnosis_code": "CIRC",
    "comorbidity_count": 3,
    "prior_admissions": 1,
    "department": "Cardiology",
}


class TestRoleMapping:
    def test_the_legacy_role_name_still_resolves(self):
        """Accounts created before the split stored a single "clinician" role."""
        assert normalise("clinician") == DOCTOR
        assert capabilities_for("clinician") == capabilities_for(DOCTOR)

    def test_case_and_padding_are_ignored(self):
        assert normalise("  Analyst ") == ANALYST

    def test_an_unknown_role_has_no_capabilities(self):
        assert normalise("wizard") is None
        assert capabilities_for("wizard") == []

    def test_admin_is_the_union_of_both_clinical_roles(self):
        assert set(CAPABILITIES[ADMIN]) == set(CAPABILITIES[DOCTOR]) | set(
            CAPABILITIES[ANALYST]
        )

    def test_the_two_clinical_roles_do_not_overlap(self):
        """If they shared capabilities there would be no separation to enforce."""
        assert not set(CAPABILITIES[DOCTOR]) & set(CAPABILITIES[ANALYST])

    def test_admin_is_not_self_selectable(self):
        assert ADMIN not in SELF_SELECTABLE
        assert coerce_signup_role(ADMIN) == DOCTOR

    @pytest.mark.parametrize("value", [None, "", 42, ["admin"], {"role": "admin"}])
    def test_a_nonsense_role_claim_becomes_the_default(self, value):
        assert coerce_signup_role(value) == DOCTOR

    def test_has_capability_is_false_for_a_role_that_lacks_it(self):
        assert has_capability(DOCTOR, "patient.predict")
        assert not has_capability(DOCTOR, "dataset.upload")


class TestDoctorAccess:
    """A doctor works one admission at a time and nothing wider."""

    def test_can_score_a_single_patient(self, client, doctor_headers):
        response = client.post("/api/predict", headers=doctor_headers, json=PATIENT)
        assert response.status_code == 200, response.get_json()

    def test_can_read_their_own_caseload(self, client, doctor_headers):
        response = client.get("/api/dashboard/clinical", headers=doctor_headers)
        assert response.status_code == 200
        assert "worklist" in response.get_json()

    def test_cannot_upload_a_dataset(self, client, doctor_headers, sample_csv):
        response = client.post(
            "/api/dataset/upload",
            headers=doctor_headers,
            data={"file": (io.BytesIO(sample_csv), "admissions.csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 403
        assert "error" in response.get_json()

    def test_cannot_read_cohort_kpis(self, client, doctor_headers):
        assert client.get("/api/dashboard/kpis", headers=doctor_headers).status_code == 403

    def test_cannot_inspect_the_model(self, client, doctor_headers):
        assert client.get("/api/predict/model", headers=doctor_headers).status_code == 403
        assert (
            client.get(
                "/api/predict/explain/global", headers=doctor_headers
            ).status_code
            == 403
        )

    def test_cannot_download_the_cohort_report(self, client, doctor_headers):
        response = client.get("/api/reports/cohort.pdf", headers=doctor_headers)
        assert response.status_code == 403


class TestAnalystAccess:
    """An analyst works the cohort and does not sign clinical documents."""

    @pytest.fixture
    def dataset_id(self, client, analyst_headers, sample_csv):
        response = client.post(
            "/api/dataset/upload",
            headers=analyst_headers,
            data={"file": (io.BytesIO(sample_csv), "admissions.csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 201, response.get_json()
        return response.get_json()["dataset_id"]

    def test_can_upload_and_read_the_cohort(self, client, analyst_headers, dataset_id):
        response = client.get(
            f"/api/dashboard/kpis?dataset_id={dataset_id}", headers=analyst_headers
        )
        assert response.status_code == 200
        assert response.get_json()["kpis"]["total_patients"] > 0

    def test_can_inspect_the_model(self, client, analyst_headers):
        assert client.get("/api/predict/model", headers=analyst_headers).status_code == 200

    def test_can_score_a_whole_dataset(self, client, analyst_headers, dataset_id):
        response = client.post(
            "/api/predict", headers=analyst_headers, json={"dataset_id": dataset_id}
        )
        assert response.status_code == 200

    def test_cannot_score_a_single_patient(self, client, analyst_headers):
        response = client.post("/api/predict", headers=analyst_headers, json=PATIENT)
        assert response.status_code == 403

    def test_cannot_generate_a_patient_report(self, client, analyst_headers):
        response = client.post(
            "/api/reports/patient.pdf", headers=analyst_headers, json=PATIENT
        )
        assert response.status_code == 403

    def test_cannot_read_a_clinical_caseload(self, client, analyst_headers):
        assert (
            client.get("/api/dashboard/clinical", headers=analyst_headers).status_code
            == 403
        )


class TestAdminAccess:
    def test_admin_reaches_both_sides(self, client, auth_headers):
        assert client.post("/api/predict", headers=auth_headers, json=PATIENT).status_code == 200
        assert client.get("/api/dashboard/kpis", headers=auth_headers).status_code == 200
        assert client.get("/api/dashboard/clinical", headers=auth_headers).status_code == 200


class TestScopingBeatsRole:
    """
    A 403 must never be the thing that reveals a resource exists.

    A doctor cannot read cohorts at all, so probing another user's dataset id
    has to come back 404 -- the same answer they would get for an id that was
    never issued -- rather than a 403 that confirms it is real.
    """

    @pytest.fixture
    def analyst_dataset(self, client, analyst_headers, sample_csv):
        response = client.post(
            "/api/dataset/upload",
            headers=analyst_headers,
            data={"file": (io.BytesIO(sample_csv), "admissions.csv")},
            content_type="multipart/form-data",
        )
        return response.get_json()["dataset_id"]

    def test_kpis_for_someone_elses_dataset_is_404(
        self, client, doctor_headers, analyst_dataset
    ):
        response = client.get(
            f"/api/dashboard/kpis?dataset_id={analyst_dataset}", headers=doctor_headers
        )
        assert response.status_code == 404

    def test_a_real_and_a_fictional_id_are_indistinguishable(
        self, client, doctor_headers, analyst_dataset
    ):
        real = client.get(
            f"/api/dashboard/kpis?dataset_id={analyst_dataset}", headers=doctor_headers
        )
        invented = client.get(
            "/api/dashboard/kpis?dataset_id=999999", headers=doctor_headers
        )
        assert real.status_code == invented.status_code == 404

    def test_cohort_pdf_for_someone_elses_dataset_is_404(
        self, client, doctor_headers, analyst_dataset
    ):
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={analyst_dataset}",
            headers=doctor_headers,
        )
        assert response.status_code == 404


class TestAdminAllowlist:
    """
    Admin is granted by server configuration and nothing else.

    The demo seed put an `admin` account with a published password into a
    live database, so the list replaces seeding as the way anyone becomes an
    administrator -- and being server-side, no request can reach it.
    """

    @staticmethod
    def _app(app, emails):
        app.config["ADMIN_EMAILS"] = [e.lower() for e in emails]
        return app

    def test_a_listed_address_registers_as_admin(self, client, app):
        self._app(app, ["boss@hospital.org"])
        body = client.post(
            "/api/auth/register",
            json={
                "email": "boss@hospital.org",
                "password": "a-good-password",
                "full_name": "The Boss",
                "role": DOCTOR,
            },
        ).get_json()
        assert body["user"]["role"] == ADMIN

    def test_an_unlisted_address_cannot_ask_for_admin(self, client, app):
        self._app(app, ["boss@hospital.org"])
        body = client.post(
            "/api/auth/register",
            json={
                "email": "nobody@hospital.org",
                "password": "a-good-password",
                "full_name": "Nobody",
                "role": "admin",
            },
        ).get_json()
        assert body["user"]["role"] == DEFAULT_ROLE

    def test_the_match_ignores_case_and_padding(self, client, app):
        self._app(app, ["boss@hospital.org"])
        body = client.post(
            "/api/auth/register",
            json={
                "email": "  BOSS@Hospital.ORG ",
                "password": "a-good-password",
                "full_name": "The Boss",
                "role": DOCTOR,
            },
        ).get_json()
        assert body["user"]["role"] == ADMIN

    def test_adding_an_address_promotes_on_next_sign_in(self, client, app):
        """So the list can be edited without touching the database."""
        client.post(
            "/api/auth/register",
            json={
                "email": "later@hospital.org",
                "password": "a-good-password",
                "full_name": "Later Admin",
                "role": DOCTOR,
            },
        )
        self._app(app, ["later@hospital.org"])
        body = client.post(
            "/api/auth/login",
            json={"email": "later@hospital.org", "password": "a-good-password"},
        ).get_json()
        assert body["user"]["role"] == ADMIN

    def test_removing_an_address_demotes_on_next_sign_in(self, client, app):
        self._app(app, ["temp@hospital.org"])
        client.post(
            "/api/auth/register",
            json={
                "email": "temp@hospital.org",
                "password": "a-good-password",
                "full_name": "Temp Admin",
                "role": DOCTOR,
            },
        )
        # Someone leaves the team.
        self._app(app, ["someone.else@hospital.org"])
        body = client.post(
            "/api/auth/login",
            json={"email": "temp@hospital.org", "password": "a-good-password"},
        ).get_json()
        assert body["user"]["role"] == DEFAULT_ROLE

    def test_an_empty_list_changes_nobody(self, client, app):
        """
        Unconfigured means "not in use", not "nobody is an administrator" --
        otherwise shipping this would strip admin from every existing install.
        """
        self._app(app, ["boss@hospital.org"])
        client.post(
            "/api/auth/register",
            json={
                "email": "boss@hospital.org",
                "password": "a-good-password",
                "full_name": "The Boss",
                "role": DOCTOR,
            },
        )
        self._app(app, [])
        body = client.post(
            "/api/auth/login",
            json={"email": "boss@hospital.org", "password": "a-good-password"},
        ).get_json()
        assert body["user"]["role"] == ADMIN

    # --- the seeded demo administrator ---------------------------------
    # Seeding runs on every boot and only skips accounts that already exist,
    # so deleting the demo admin from a live database is not a fix by itself:
    # the next restart puts it back. These two pin the rule that closes that
    # hole -- the allowlist, once configured, is the only source of admin.

    @staticmethod
    def _booted(tmp_path, admin_emails):
        """A freshly created app, since seeding happens inside create_app."""
        from backend.app import create_app
        from backend.models import User, db
        from tests.conftest import TestConfig

        class _Config(TestConfig):
            UPLOAD_DIR = tmp_path / "uploads"
            ADMIN_EMAILS = admin_emails

        application = create_app(_Config)
        with application.app_context():
            demo = User.query.filter_by(
                email=application.config["DEMO_EMAIL"].lower()
            ).first()
            role = demo.role if demo else None
            db.session.remove()
            db.drop_all()
        return role

    def test_the_demo_admin_is_not_seeded_as_admin_once_the_list_is_set(
        self, tmp_path
    ):
        """
        The published demo password must not reach an admin account on a
        deployment that has named its real administrators.
        """
        assert self._booted(tmp_path, ["boss@hospital.org"]) == DEFAULT_ROLE

    def test_the_demo_admin_still_works_on_an_unconfigured_deployment(
        self, tmp_path
    ):
        """A fresh checkout keeps both dashboards openable without setup."""
        assert self._booted(tmp_path, []) == ADMIN
