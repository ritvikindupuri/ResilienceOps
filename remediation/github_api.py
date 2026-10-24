"""Minimal GitHub API helper. Never logs tokens."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote


class GitHubError(RuntimeError):
    pass


def github_token() -> str:
    token = (os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or "").strip()
    if not token:
        raise GitHubError("GITHUB_TOKEN (or GH_TOKEN) is not set")
    return token


def github_repository() -> str:
    repo = (os.getenv("GITHUB_REPOSITORY") or "").strip()
    if not repo or "/" not in repo or repo.count("/") != 1:
        raise GitHubError("GITHUB_REPOSITORY must be owner/name")
    owner, name = repo.split("/", 1)
    if not owner or not name:
        raise GitHubError("GITHUB_REPOSITORY must be owner/name")
    return repo


def _request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> Any:
    tok = token if token is not None else github_token()
    url = f"https://api.github.com{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {tok}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "resilienceops-remediation",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # Do not include headers (Authorization) or the token.
        raise GitHubError(f"GitHub API {method} {path} -> HTTP {exc.code}") from None


def collaborator_permission(repo: str, login: str, token: str | None = None) -> str:
    owner, name = repo.split("/", 1)
    path = (
        f"/repos/{quote(owner)}/{quote(name)}"
        f"/collaborators/{quote(login)}/permission"
    )
    try:
        payload = _request("GET", path, token=token)
    except GitHubError:
        return ""
    return str(payload.get("permission") or "")


def list_issue_comments(repo: str, issue_number: int, token: str | None = None) -> list[dict[str, Any]]:
    owner, name = repo.split("/", 1)
    path = f"/repos/{quote(owner)}/{quote(name)}/issues/{int(issue_number)}/comments?per_page=100"
    payload = _request("GET", path, token=token)
    if not isinstance(payload, list):
        raise GitHubError("expected a comment list")
    return payload


def add_issue_comment(repo: str, issue_number: int, body: str, token: str | None = None) -> dict[str, Any]:
    owner, name = repo.split("/", 1)
    path = f"/repos/{quote(owner)}/{quote(name)}/issues/{int(issue_number)}/comments"
    payload = _request("POST", path, body={"body": body}, token=token)
    if not isinstance(payload, dict):
        raise GitHubError("expected a comment object")
    return payload


def add_issue_labels(repo: str, issue_number: int, labels: list[str], token: str | None = None) -> None:
    owner, name = repo.split("/", 1)
    path = f"/repos/{quote(owner)}/{quote(name)}/issues/{int(issue_number)}/labels"
    _request("POST", path, body={"labels": labels}, token=token)


def list_labeled_issues(repo: str, labels: list[str], token: str | None = None) -> list[dict[str, Any]]:
    owner, name = repo.split("/", 1)
    joined = ",".join(labels)
    path = (
        f"/repos/{quote(owner)}/{quote(name)}/issues"
        f"?state=open&labels={quote(joined)}&per_page=50"
    )
    payload = _request("GET", path, token=token)
    if not isinstance(payload, list):
        raise GitHubError("expected an issue list")
    return [i for i in payload if not i.get("pull_request")]


def repo_owner_login(repo: str, token: str | None = None) -> str:
    owner, name = repo.split("/", 1)
    payload = _request("GET", f"/repos/{quote(owner)}/{quote(name)}", token=token)
    owner_obj = payload.get("owner") or {}
    return str(owner_obj.get("login") or owner)
