"""Upload validation: what the API accepts, and what it must refuse."""

from __future__ import annotations

import io

import pytest


def post_file(client, headers, content: bytes, filename: str):
    return client.post(
        "/api/dataset/upload",
        headers=headers,
        data={"file": (io.BytesIO(content), filename)},
        content_type="multipart/form-data",
    )


class TestAccepted:
    def test_valid_csv_is_stored_and_summarised(self, client, auth_headers, sample_csv):
        response = post_file(client, auth_headers, sample_csv, "admissions.csv")
        body = response.get_json()

        assert response.status_code == 201
        assert body["dataset_id"]
        assert body["quality_report"]["row_count"] > 0
        assert body["preview"]["columns"]

    def test_stored_file_is_renamed_not_kept_as_supplied(
        self, app, client, auth_headers, sample_csv
    ):
        """
        The upload is written under a generated UUID name. Keeping the caller's
        filename on disk is how path-traversal and overwrite bugs happen.
        """
        response = post_file(client, auth_headers, sample_csv, "admissions.csv")
        dataset_id = response.get_json()["dataset_id"]

        with app.app_context():
            from backend.models import Dataset, db

            stored = db.session.get(Dataset, dataset_id)
            assert "admissions.csv" not in stored.stored_path
            assert stored.filename == "admissions.csv"  # original kept as a label


class TestRejected:
    def test_request_without_a_file_is_400(self, client, auth_headers):
        response = client.post("/api/dataset/upload", headers=auth_headers, data={})
        assert response.status_code == 400

    def test_empty_file_is_400(self, client, auth_headers):
        response = post_file(client, auth_headers, b"", "empty.csv")
        assert response.status_code == 400

    @pytest.mark.parametrize("filename", ["payload.exe", "script.sh", "notes.txt", "a.pdf"])
    def test_disallowed_extensions_are_415(self, client, auth_headers, filename):
        response = post_file(client, auth_headers, b"anything", filename)
        assert response.status_code == 415

    def test_csv_missing_required_columns_is_422(self, client, auth_headers):
        """Parses fine as CSV, but does not meet the schema."""
        response = post_file(
            client, auth_headers, b"colour,shape\nred,round\nblue,square\n", "wrong.csv"
        )
        assert response.status_code == 422

    def test_upload_requires_authentication(self, client, sample_csv):
        response = post_file(client, {}, sample_csv, "admissions.csv")
        assert response.status_code == 401

    def test_path_traversal_in_the_filename_is_neutralised(
        self, app, client, auth_headers, sample_csv
    ):
        """A crafted name must not escape the upload directory."""
        response = post_file(client, auth_headers, sample_csv, "../../../../etc/passwd.csv")
        assert response.status_code == 201

        with app.app_context():
            from backend.models import Dataset, db

            stored = db.session.get(Dataset, response.get_json()["dataset_id"])
            upload_dir = app.config["UPLOAD_DIR"].resolve()
            # The written path stays inside the configured upload directory.
            assert str(upload_dir) in str(__import__("pathlib").Path(stored.stored_path).resolve())
