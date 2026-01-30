"""API tests: analyze creates report, report endpoint returns it."""

import uuid

from fastapi.testclient import TestClient


def test_analyze_creates_report(client: TestClient):
    resp = client.post(
        "/api/analyze",
        json={"repo_url": "https://github.com/owner/repo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    report_id = data["report_id"]

    get_resp = client.get(f"/api/reports/{report_id}")
    assert get_resp.status_code == 200
    report = get_resp.json()
    assert report["id"] == report_id
    assert report["repo_url"] == "https://github.com/owner/repo"
    assert report["status"] == "done"
    assert "overall_score" in report
    assert "findings_json" in report


def test_get_report_404(client: TestClient):
    resp = client.get(f"/api/reports/{uuid.uuid4()}")
    assert resp.status_code == 404
