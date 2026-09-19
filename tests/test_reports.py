"""
PDF report endpoints.

The assertions deliberately check the response envelope and a handful of
structural facts about the bytes rather than the visual layout: what must not
regress is that a report is a real PDF, is scoped to its owner, carries a safe
filename, and refuses to render an invalid record.
"""

from __future__ import annotations

import io

import pytest

from ml.predictor import is_ready

requires_model = pytest.mark.skipif(
    not is_ready(), reason="no trained model artifacts; run `python -m ml.train`"
)

PATIENT = {
    "age": 74,
    "gender": "F",
    "admission_type": "Emergency",
    "diagnosis_code": "CIRC",
    "comorbidity_count": 3,
    "prior_admissions": 1,
    "department": "Cardiology",
}


def page_count(payload: bytes) -> int:
    import pypdf

    return len(pypdf.PdfReader(io.BytesIO(payload)).pages)


@pytest.fixture
def dataset_id(client, auth_headers, sample_csv):
    response = client.post(
        "/api/dataset/upload",
        headers=auth_headers,
        data={"file": (io.BytesIO(sample_csv), "admissions.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["dataset_id"]


@requires_model
class TestCohortReport:
    def test_returns_a_pdf(self, client, auth_headers, dataset_id):
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert response.data.startswith(b"%PDF-")
        assert page_count(response.data) >= 1

    def test_is_sent_as_an_attachment_with_a_safe_filename(
        self, client, auth_headers, dataset_id
    ):
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}", headers=auth_headers
        )
        disposition = response.headers["Content-Disposition"]

        assert disposition.startswith("attachment;")
        assert disposition.endswith('.pdf"')
        # A quote or newline reaching this header would allow header injection.
        assert "\n" not in disposition and "\r" not in disposition

    def test_is_not_cached(self, client, auth_headers, dataset_id):
        """A report is a snapshot of mutable data; a cached copy goes stale."""
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}", headers=auth_headers
        )
        assert "no-store" in response.headers.get("Cache-Control", "")

    @pytest.mark.parametrize("days", [0, 61, 999, -1])
    def test_out_of_range_days_is_rejected(self, client, auth_headers, dataset_id, days):
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}&days={days}",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_non_numeric_days_is_rejected(self, client, auth_headers, dataset_id):
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}&days=lots",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_another_user_cannot_download_it(self, client, other_user, dataset_id):
        """Same scoping as every other dataset route -- a PDF is not a loophole."""
        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}",
            headers=other_user["headers"],
        )
        assert response.status_code == 404

    def test_requires_authentication(self, client, dataset_id):
        assert client.get(f"/api/reports/cohort.pdf?dataset_id={dataset_id}").status_code == 401

    def test_carries_the_held_out_model_metrics(self, client, auth_headers, dataset_id):
        """
        "Is this model still trustworthy" is half the analyst's job, so the
        candidate algorithms and the mark against the selected one have to
        survive the trip to paper, not just live on the dashboard.
        """
        import pypdf

        response = client.get(
            f"/api/reports/cohort.pdf?dataset_id={dataset_id}", headers=auth_headers
        )
        assert response.status_code == 200

        text = "".join(
            page.extract_text()
            for page in pypdf.PdfReader(io.BytesIO(response.data)).pages
        )
        assert "Model performance" in text
        assert "LOS RMSE" in text
        assert "(selected)" in text


@requires_model
class TestCaseloadReport:
    """
    The doctor's handover sheet.

    It takes no parameters at all -- the caseload is whoever is holding the
    token -- so the interesting assertions are about scoping and about the
    empty case, which a clinician hits on their first day.
    """

    @pytest.fixture
    def scored(self, client, doctor_headers):
        """One admission on the doctor's own caseload."""
        response = client.post("/api/predict", headers=doctor_headers, json=PATIENT)
        assert response.status_code == 200, response.get_json()
        return response.get_json()

    def test_returns_a_pdf(self, client, doctor_headers, scored):
        response = client.get("/api/reports/caseload.pdf", headers=doctor_headers)

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert response.data.startswith(b"%PDF-")
        assert page_count(response.data) >= 1

    def test_is_sent_as_an_attachment_with_a_safe_filename(
        self, client, doctor_headers, scored
    ):
        disposition = client.get(
            "/api/reports/caseload.pdf", headers=doctor_headers
        ).headers["Content-Disposition"]

        assert disposition.startswith("attachment;")
        assert disposition.endswith('.pdf"')
        assert "\r" not in disposition and "\n" not in disposition

    def test_is_not_cached(self, client, doctor_headers, scored):
        response = client.get("/api/reports/caseload.pdf", headers=doctor_headers)
        assert response.headers["Cache-Control"] == "no-store"

    def test_renders_for_a_clinician_with_no_admissions_yet(self, client, doctor_headers):
        """An empty caseload is a first day, not an error."""
        response = client.get("/api/reports/caseload.pdf", headers=doctor_headers)

        assert response.status_code == 200
        assert response.data.startswith(b"%PDF-")

    def test_an_analyst_cannot_download_it(self, client, analyst_headers):
        """The cohort side of the product has no caseload to report on."""
        assert client.get(
            "/api/reports/caseload.pdf", headers=analyst_headers
        ).status_code == 403

    def test_requires_authentication(self, client):
        assert client.get("/api/reports/caseload.pdf").status_code == 401

    def test_covers_only_the_callers_own_admissions(
        self, client, doctor_headers, other_user, scored
    ):
        """
        Two clinicians, one shared model: the sheet must not leak a colleague's
        round. The second account scores a patient with a reference the first
        never used, and it must not appear in the first account's report.
        """
        import pypdf

        response = client.post(
            "/api/predict",
            headers=other_user["headers"],
            json={**PATIENT, "patient_id": "NOTMINE01"},
        )
        assert response.status_code == 200, response.get_json()

        pdf = client.get("/api/reports/caseload.pdf", headers=doctor_headers).data
        text = "".join(
            page.extract_text() for page in pypdf.PdfReader(io.BytesIO(pdf)).pages
        )
        assert "NOTMINE01" not in text


@requires_model
class TestPatientReport:
    def test_returns_a_pdf(self, client, auth_headers):
        response = client.post(
            "/api/reports/patient.pdf", headers=auth_headers, json=PATIENT
        )

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert response.data.startswith(b"%PDF-")
        assert page_count(response.data) >= 1

    def test_patient_reference_reaches_the_filename(self, client, auth_headers):
        response = client.post(
            "/api/reports/patient.pdf",
            headers=auth_headers,
            json={**PATIENT, "patient_id": "PT000042"},
        )
        assert "PT000042" in response.headers["Content-Disposition"]

    def test_a_hostile_patient_reference_cannot_forge_headers(self, client, auth_headers):
        """The filename is built from a slug, never straight from user input."""
        response = client.post(
            "/api/reports/patient.pdf",
            headers=auth_headers,
            json={**PATIENT, "patient_id": 'x"\r\nX-Injected: yes'},
        )

        assert response.status_code == 200
        disposition = response.headers["Content-Disposition"]
        assert "X-Injected" not in response.headers
        assert "\r" not in disposition and "\n" not in disposition
        assert disposition.count('"') == 2

    def test_empty_body_is_rejected(self, client, auth_headers):
        response = client.post("/api/reports/patient.pdf", headers=auth_headers, json={})
        assert response.status_code == 400

    def test_invalid_record_is_rejected_before_rendering(self, client, auth_headers):
        response = client.post(
            "/api/reports/patient.pdf", headers=auth_headers, json={**PATIENT, "age": -5}
        )
        assert response.status_code == 422

    def test_missing_field_is_rejected(self, client, auth_headers):
        incomplete = {k: v for k, v in PATIENT.items() if k != "department"}
        response = client.post(
            "/api/reports/patient.pdf", headers=auth_headers, json=incomplete
        )
        assert response.status_code == 422

    def test_requires_authentication(self, client):
        assert client.post("/api/reports/patient.pdf", json=PATIENT).status_code == 401


@requires_model
class TestReportContent:
    """The generator is called directly here -- no HTTP, no database."""

    def test_patient_report_states_the_predicted_tier(self):
        import pypdf

        from ml.predictor import get_predictor
        from ml.report import patient_report

        prediction = get_predictor().predict_one(dict(PATIENT), explain=True)
        pdf = patient_report(dict(PATIENT), prediction, patient_ref="PT000042")

        text = "".join(
            page.extract_text() for page in pypdf.PdfReader(io.BytesIO(pdf)).pages
        )
        assert prediction["risk_tier"].upper() in text.upper()
        assert "PT000042" in text
        # The disclaimer is a product requirement, not decoration.
        assert "clinical judgement" in text.lower()

    def test_caseload_report_leads_with_the_overdue_admissions(self):
        """
        The whole point of this report is the "priority actions" block. An
        admission whose predicted discharge has already passed must be named
        there, and the sheet must carry the planning-aid disclaimer.
        """
        import pypdf

        from ml.report import caseload_report

        pdf = caseload_report(
            {
                "caseload": {
                    "patients": 2,
                    "high_risk": 1,
                    "avg_los_days": 6.4,
                    "longest_los_days": 9.0,
                    "scored_today": 1,
                    "avg_confidence": 0.88,
                    "due_within_48h": 1,
                },
                "model_version": "test-1",
                "risk_distribution": [
                    {"tier": "High", "count": 1, "percentage": 50.0},
                    {"tier": "Low", "count": 1, "percentage": 50.0},
                ],
                "discharge_schedule": [
                    {"day": 0, "date": "2026-01-01", "patients": 1,
                     "label": "Overdue / today"},
                    {"day": 1, "date": "2026-01-02", "patients": 1, "label": "Day +1"},
                ],
                "worklist": [
                    {
                        "id": 1, "patient_ref": "LATE0001", "department": "Cardiology",
                        "risk_tier": "High", "los_days": 9.0, "confidence": 0.9,
                        "expected_discharge": "2025-12-30", "days_remaining": -2,
                    },
                    {
                        "id": 2, "patient_ref": "SOON0002", "department": "Neurology",
                        "risk_tier": "Low", "los_days": 3.8, "confidence": 0.86,
                        "expected_discharge": "2026-01-02", "days_remaining": 1,
                    },
                ],
            },
            clinician="Dr Ada Reed",
        )

        assert pdf.startswith(b"%PDF-")
        text = "".join(
            page.extract_text() for page in pypdf.PdfReader(io.BytesIO(pdf)).pages
        )
        assert "Priority actions" in text
        assert "LATE0001" in text
        assert "2d overdue" in text
        assert "Dr Ada Reed" in text
        assert "not a clinical recommendation" in text

    def test_caseload_report_survives_an_empty_caseload(self):
        """No admissions scored yet must render a page, not raise."""
        from ml.report import caseload_report

        pdf = caseload_report({"caseload": {"patients": 0}, "worklist": []})
        assert pdf.startswith(b"%PDF-")

    def test_cohort_report_survives_an_empty_distribution(self):
        """No predictions yet must render a page, not raise."""
        from ml.report import cohort_report

        pdf = cohort_report({
            "kpis": {},
            "risk_distribution": [],
            "bed_forecast": [],
            "los_histogram": [],
            "department_breakdown": [],
            "source": {},
        })
        assert pdf.startswith(b"%PDF-")
