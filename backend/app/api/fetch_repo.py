from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.github_client import (
    GitHubAPIError,
    GitHubRateLimitError,
    InvalidRepoUrlError,
    RepoNotFoundError,
    fetch_repo,
)

router = APIRouter(prefix="/api", tags=["api"])


class FetchRepoRequest(BaseModel):
    url: str


@router.post("/fetch-repo")
def post_fetch_repo(body: FetchRepoRequest):
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    try:
        result = fetch_repo(url)
    except InvalidRepoUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RepoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GitHubRateLimitError as e:
        headers = {}
        if e.retry_after is not None:
            headers["Retry-After"] = str(e.retry_after)
        raise HTTPException(status_code=429, detail=str(e), headers=headers)
    except GitHubAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return result
