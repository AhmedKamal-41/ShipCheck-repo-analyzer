import copy
import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import GITHUB_TOKEN
from app.core.database import get_db
from app.core.rate_limit import RateLimitExceeded, check_analyze_rate_limit
from app.core.repo_limits import MAX_FILES_FETCH, MAX_TOTAL_BYTES
from app.models import Report
from app.services.analyzer import ReportResult, analyze
from app.services.candidate_selector import select_candidates
from app.services.github_client import (
    GitHubAPIError,
    GitHubRateLimitError,
    InvalidRepoUrlError,
    RepoNotFoundError,
    _parse_repo_url,
    fetch_repo,
)
from app.services.repo_content import batch_fetch_text

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DEMO_FIXTURE_PATH = _BACKEND_ROOT / "tests" / "fixtures" / "sample_repo.json"


def _load_demo_fixture() -> dict:
    with open(_DEMO_FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)

router = APIRouter(prefix="/api", tags=["reports"])


class AnalyzeRequest(BaseModel):
    repo_url: str


class AnalyzeResponse(BaseModel):
    report_id: str


def _serialize_report_result(result: ReportResult) -> tuple[dict, dict]:
    """Produce (legacy_findings_json, structured_findings_v2) from one ReportResult.

    Both have the same overall shape; they differ only in how
    `recommendation` is rendered: legacy is a flat string, v2 is the
    structured what/where/why/how dict.
    """
    structured = asdict(result)  # recursively turns Recommendation into dict
    legacy = copy.deepcopy(structured)
    for section in legacy.get("sections") or []:
        for check in section.get("checks") or []:
            rec = check.get("recommendation")
            if isinstance(rec, dict):
                # Mirror Recommendation.to_legacy_string(): "{what} {how}"
                what = rec.get("what") or ""
                how = rec.get("how") or ""
                check["recommendation"] = f"{what} {how}".strip()
    return legacy, structured


def _v2_to_legacy(findings_v2: Any) -> Any:
    """Convert a structured findings_v2 payload into legacy shape on read.

    Used when a row was written with both columns and a v=1 client requests it,
    or to rebuild a legacy view on the fly when only findings_v2 exists.
    """
    if not isinstance(findings_v2, dict):
        return findings_v2
    out = copy.deepcopy(findings_v2)
    for section in out.get("sections") or []:
        for check in section.get("checks") or []:
            rec = check.get("recommendation")
            if isinstance(rec, dict):
                check["recommendation"] = f"{rec.get('what') or ''} {rec.get('how') or ''}".strip()
    return out


def _report_to_detail(r: Report, version: int = 1) -> dict:
    """Return the report as a JSON-friendly dict.

    version=1 (default): findings_json field has flat-string recommendations.
    version=2: findings_json field has structured recommendation dicts.

    Field name stays `findings_json` either way so old clients see the same
    response shape; only the `recommendation` field within changes.
    """
    if version == 2:
        # Prefer the new column, fall back to the legacy column if missing.
        payload = r.findings_v2 if r.findings_v2 is not None else r.findings_json
    else:
        payload = r.findings_json if r.findings_json is not None else _v2_to_legacy(r.findings_v2)
    return {
        "id": str(r.id),
        "repo_url": r.repo_url,
        "repo_owner": r.repo_owner,
        "repo_name": r.repo_name,
        "commit_sha": r.commit_sha,
        "status": r.status,
        "overall_score": r.overall_score,
        "findings_json": payload,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _report_to_list_item(r: Report) -> dict:
    return {
        "id": str(r.id),
        "repo_url": r.repo_url,
        "score": r.overall_score,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze repository",
    description="Analyze a public GitHub repository. Read-only; no repository code is executed.",
)
def post_analyze(
    body: AnalyzeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    repo_url = (body.repo_url or "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url is required")

    try:
        _parse_repo_url(repo_url)
    except InvalidRepoUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ip = request.client.host if request.client else "unknown"
    try:
        check_analyze_rate_limit(ip)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))

    report = Report(repo_url=repo_url, status="pending")
    db.add(report)
    db.commit()
    db.refresh(report)
    report_id = str(report.id)

    try:
        fetch = fetch_repo(repo_url)
    except GitHubRateLimitError as e:
        if not GITHUB_TOKEN:
            fetch = _load_demo_fixture()
        else:
            report.status = "failed"
            report.findings_json = {"error": str(e)}
            db.commit()
            return AnalyzeResponse(report_id=report_id)
    except (
        InvalidRepoUrlError,
        RepoNotFoundError,
        GitHubAPIError,
        Exception,
    ) as e:
        report.status = "failed"
        report.findings_json = {"error": str(e)}
        db.commit()
        return AnalyzeResponse(report_id=report_id)

    content_by_path = {}
    tree_blobs = fetch.get("tree_blobs") or []
    if tree_blobs:
        try:
            owner = fetch.get("owner") or ""
            repo = fetch.get("name") or ""
            candidate_blobs = select_candidates(tree_blobs)
            content_by_path = batch_fetch_text(
                owner, repo, candidate_blobs,
                max_files=MAX_FILES_FETCH,
                max_total_bytes=MAX_TOTAL_BYTES,
            )
        except Exception:
            pass

    result: ReportResult = analyze(fetch, content_by_path=content_by_path)
    legacy_payload, structured_payload = _serialize_report_result(result)
    report.status = "done"
    report.overall_score = result.overall_score
    report.findings_json = legacy_payload
    report.findings_v2 = structured_payload
    report.repo_owner = fetch.get("owner")
    report.repo_name = fetch.get("name")
    db.commit()

    return AnalyzeResponse(report_id=report_id)


@router.get("/reports/{report_id}")
def get_report(
    report_id: uuid.UUID,
    v: int = Query(1, ge=1, le=2, description="Recommendation shape version: 1=legacy strings, 2=structured what/where/why/how dicts"),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_detail(report, version=v)


@router.get("/reports")
def list_reports(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_report_to_list_item(r) for r in rows]
