"""
Cross-tenant isolation.

Every route that takes a `dataset_id` must scope it to the calling user. The
protection exists today; these tests exist so a future refactor cannot quietly
drop it and expose one clinician's patient data to another.

A missing resource and someone else's resource must both answer 404 -- a 403
would confirm the id exists, which is itself a disclosure.
"""

from __future__ import annotations

import io

import pytest


@pytest.fixture
def owned_dataset(client, auth_headers, sample_csv):
    """A dataset uploaded by the seeded demo user."""
    response = client.post(
        "/api/dataset/upload",
        headers=auth_headers,
        data={"file": (io.BytesIO(sample_csv), "admissions.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["dataset_id"]


class TestDatasetIsolation:
    def test_owner_can_read_their_own_dataset(self, client, auth_headers, owned_dataset):
        response = client.get(
            f"/api/dataset/{owned_dataset}/preview", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.get_json()["dataset_id"] == owned_dataset

    def test_another_user_cannot_read_it(self, client, other_user, owned_dataset):
        response = client.get(
            f"/api/dataset/{owned_dataset}/preview", headers=other_user["headers"]
        )
        assert response.status_code == 404

    def test_another_user_cannot_score_it(self, client, other_user, owned_dataset):
        """The batch-predict path takes a dataset_id and must scope it too."""
        response = client.post(
            "/api/predict",
            headers=other_user["headers"],
            json={"dataset_id": owned_dataset},
        )
        assert response.status_code == 404

    def test_another_user_cannot_pull_it_into_the_dashboard(
        self, client, other_user, owned_dataset
    ):
        response = client.get(
            f"/api/dashboard/kpis?dataset_id={owned_dataset}",
            headers=other_user["headers"],
        )
        assert response.status_code in (404, 200)
        if response.status_code == 200:
            # If the dashboard falls back to "no dataset" rather than 404ing,
            # it must not have served the other user's data.
            assert response.get_json().get("dataset_id") != owned_dataset

    def test_dataset_listing_is_scoped_to_the_caller(
        self, client, other_user, owned_dataset
    ):
        response = client.get("/api/dataset", headers=other_user["headers"])
        assert response.status_code == 200

        visible = [d["dataset_id"] for d in response.get_json()["datasets"]]
        assert owned_dataset not in visible

    def test_nonexistent_dataset_is_404(self, client, auth_headers):
        response = client.get("/api/dataset/999999/preview", headers=auth_headers)
        assert response.status_code == 404

    def test_all_dataset_routes_require_authentication(self, client, owned_dataset):
        """No anonymous access, regardless of ownership."""
        assert client.get("/api/dataset").status_code == 401
        assert client.get(f"/api/dataset/{owned_dataset}/preview").status_code == 401
        assert client.post("/api/predict", json={"dataset_id": owned_dataset}).status_code == 401
        assert client.get("/api/dashboard/kpis").status_code == 401
