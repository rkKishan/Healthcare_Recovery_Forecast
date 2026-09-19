"""
The prediction contract.

These tests guard the shape and sanity of what the model returns, not its
accuracy -- accuracy belongs to the training run's own metrics. What matters
here is that a clinician-facing response can never be malformed, and that a
nonsense input is rejected instead of silently scored.
"""

from __future__ import annotations

import pytest

from ml.predictor import is_ready
from ml.schema import FEATURE_COLUMNS, RISK_TIER_LABELS, los_to_risk_tier

# The suite is useful without trained artifacts (auth, uploads, isolation all
# still run), so the model-dependent tests skip rather than fail.
requires_model = pytest.mark.skipif(
    not is_ready(), reason="no trained model artifacts; run `python -m ml.train`"
)

PATIENT = {
    "age": 46,
    "gender": "M",
    "admission_type": "Emergency",
    "diagnosis_code": "ONCO",
    "comorbidity_count": 0,
    "prior_admissions": 0,
    "department": "Oncology",
}


class TestRiskTiers:
    """Pure functions -- no model artifacts needed."""

    @pytest.mark.parametrize(
        "days,expected",
        [
            (0.0, "Very Low"),
            (5.9, "Very Low"),
            (6.0, "Low"),
            (11.9, "Low"),
            (12.0, "Moderate"),
            (20.0, "High"),
            (30.0, "Very High"),
            (400.0, "Very High"),
        ],
    )
    def test_boundaries_land_in_the_expected_tier(self, days, expected):
        assert los_to_risk_tier(days) == expected

    def test_every_tier_is_reachable(self):
        produced = {los_to_risk_tier(d) for d in (1, 8, 15, 25, 40)}
        assert produced == set(RISK_TIER_LABELS)


@requires_model
class TestSinglePrediction:
    def test_response_carries_the_full_contract(self, client, auth_headers):
        response = client.post("/api/predict", headers=auth_headers, json=PATIENT)
        body = response.get_json()

        assert response.status_code == 200
        for field in ("los_days", "risk_tier", "confidence", "model_version"):
            assert field in body, f"missing '{field}' in {body}"

    def test_predicted_stay_is_physically_plausible(self, client, auth_headers):
        body = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()

        # A negative or year-long stay means the pipeline is broken, whatever
        # the model's error metrics say.
        assert 0 < body["los_days"] < 365

    def test_risk_tier_is_one_of_the_known_labels(self, client, auth_headers):
        body = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()
        assert body["risk_tier"] in RISK_TIER_LABELS

    def test_tier_agrees_with_the_predicted_days(self, client, auth_headers):
        """
        The two heads must not contradict each other in the UI.

        They are separately trained, and the payload carries both
        `risk_tier` (classifier) and `los_derived_tier` (from the regressor)
        precisely because they can differ. Agreement to within one tier is
        the real invariant: regression noise that straddles a tier boundary
        is irreducible label noise for the classifier by design, so an exact
        match is not something either head promises -- and a model trained on
        fewer rows, as CI does, makes that drift visible.

        A two-tier gap would be a genuine contradiction and still fails.
        """
        body = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()

        predicted = RISK_TIER_LABELS.index(body["risk_tier"])
        derived = RISK_TIER_LABELS.index(los_to_risk_tier(body["los_days"]))
        assert abs(predicted - derived) <= 1, (
            f"classifier said {body['risk_tier']}, "
            f"{body['los_days']} days derives {los_to_risk_tier(body['los_days'])}"
        )

    def test_confidence_is_a_probability(self, client, auth_headers):
        body = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()
        assert 0.0 <= body["confidence"] <= 1.0

    def test_identical_input_gives_identical_output(self, client, auth_headers):
        """Predictions are logged for audit, so they must be reproducible."""
        first = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()
        second = client.post("/api/predict", headers=auth_headers, json=PATIENT).get_json()
        assert first["los_days"] == second["los_days"]


@requires_model
class TestPredictionInputValidation:
    def test_empty_body_is_rejected(self, client, auth_headers):
        assert client.post("/api/predict", headers=auth_headers, json={}).status_code == 400

    @pytest.mark.parametrize("missing", FEATURE_COLUMNS)
    def test_each_missing_feature_is_reported_not_guessed(
        self, client, auth_headers, missing
    ):
        """
        422, not 400: the JSON parsed fine, it just does not describe a
        scoreable patient. The response must name the offending field rather
        than quietly imputing a value and returning a prediction anyway.
        """
        incomplete = {k: v for k, v in PATIENT.items() if k != missing}
        response = client.post("/api/predict", headers=auth_headers, json=incomplete)

        assert response.status_code == 422
        assert missing in str(response.get_json()["details"])

    def test_out_of_range_age_is_rejected(self, client, auth_headers):
        response = client.post(
            "/api/predict", headers=auth_headers, json={**PATIENT, "age": -5}
        )
        assert response.status_code == 422
        assert "range" in str(response.get_json()["details"])

    def test_non_numeric_age_is_rejected(self, client, auth_headers):
        response = client.post(
            "/api/predict", headers=auth_headers, json={**PATIENT, "age": "elderly"}
        )
        assert response.status_code == 422

    def test_prediction_requires_authentication(self, client):
        assert client.post("/api/predict", json=PATIENT).status_code == 401


@requires_model
class TestSchema:
    """The form is generated from this endpoint, so its shape is a contract."""

    def test_exposes_the_categories_the_model_was_fitted_on(self, client):
        schema = client.get("/api/predict/schema").get_json()
        by_name = {f["name"]: f for f in schema["categorical"]}

        # `examples` is an illustrative subset; `categories` must be complete,
        # or the UI offers a dropdown that silently omits valid values.
        departments = by_name["department"]["categories"]
        assert "Oncology" in departments
        assert len(departments) >= len(by_name["department"]["examples"])

    def test_every_categorical_field_reports_its_vocabulary(self, client):
        schema = client.get("/api/predict/schema").get_json()
        for field in schema["categorical"]:
            assert field["categories"], f"{field['name']} has no categories"

    def test_a_preset_record_uses_only_known_categories(self, client):
        """The UI presets must not depend on values the model cannot encode."""
        schema = client.get("/api/predict/schema").get_json()
        by_name = {f["name"]: set(f["categories"]) for f in schema["categorical"]}

        presets = [
            {"gender": "M", "admission_type": "Emergency", "diagnosis_code": "CIRC",
             "department": "Cardiology"},
            {"gender": "F", "admission_type": "Elective", "diagnosis_code": "MUSC",
             "department": "Orthopedics"},
            {"gender": "F", "admission_type": "Urgent", "diagnosis_code": "ONCO",
             "department": "Oncology"},
            {"gender": "M", "admission_type": "Emergency", "diagnosis_code": "RESP",
             "department": "Pulmonology"},
        ]
        for preset in presets:
            for field, value in preset.items():
                assert value in by_name[field], f"{value!r} is not a known {field}"


@requires_model
class TestAuditLog:
    def test_a_served_prediction_is_recorded(self, app, client, auth_headers):
        """Auditability is a product requirement, not an incidental detail."""
        from backend.models import PredictionLog

        client.post("/api/predict", headers=auth_headers, json=PATIENT)

        with app.app_context():
            logged = PredictionLog.query.order_by(PredictionLog.id.desc()).first()
            assert logged is not None
            assert logged.risk_tier in RISK_TIER_LABELS
            assert logged.model_version
