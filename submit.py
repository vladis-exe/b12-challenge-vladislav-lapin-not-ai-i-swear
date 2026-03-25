#!/usr/bin/env python3
"""POST application submission to B12 (canonical JSON + HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

SIGNING_SECRET = "hello-there-from-b12"
SUBMIT_URL = "https://b12.io/apply/submission"


def _utc_iso8601_ms_z() -> str:
    dt = datetime.now(timezone.utc)
    ms = dt.microsecond // 1000
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{ms:03d}Z"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _signature_hex(body: str) -> str:
    digest = hmac.new(
        SIGNING_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def _env(name: str, *, required: bool = True) -> str | None:
    v = os.environ.get(name)
    if v is None or v == "":
        if required:
            print(f"Missing required environment variable: {name}", file=sys.stderr)
            sys.exit(1)
        return None
    return v


def _load_payload() -> dict[str, Any]:
    name = _env("B12_NAME")
    email = _env("B12_EMAIL")
    resume_link = _env("B12_RESUME_LINK")

    repo = _env("B12_REPOSITORY_LINK", required=False)
    if repo is None:
        server = _env("GITHUB_SERVER_URL", required=False)
        gh_repo = _env("GITHUB_REPOSITORY", required=False)
        if server and gh_repo:
            repo = f"{server.rstrip('/')}/{gh_repo}"
        else:
            _env("B12_REPOSITORY_LINK")  # triggers missing error

    action = _env("B12_ACTION_RUN_LINK", required=False)
    if action is None:
        server = _env("GITHUB_SERVER_URL", required=False)
        gh_repo = _env("GITHUB_REPOSITORY", required=False)
        run_id = _env("GITHUB_RUN_ID", required=False)
        if server and gh_repo and run_id:
            action = f"{server.rstrip('/')}/{gh_repo}/actions/runs/{run_id}"
        else:
            _env("B12_ACTION_RUN_LINK")  # triggers missing error

    return {
        "action_run_link": action,
        "email": email,
        "name": name,
        "repository_link": repo,
        "resume_link": resume_link,
        "timestamp": _utc_iso8601_ms_z(),
    }


def main() -> int:
    # Loads variables from a local .env file if present (does not override existing env).
    load_dotenv()
    payload = _load_payload()
    body = _canonical_json(payload)
    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": _signature_hex(body),
    }

    try:
        resp = requests.post(SUBMIT_URL, data=body.encode("utf-8"), headers=headers, timeout=60)
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    if resp.status_code != 200:
        print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print(f"Invalid JSON response: {resp.text!r}", file=sys.stderr)
        return 1

    if not data.get("success"):
        print(f"Unexpected response: {data!r}", file=sys.stderr)
        return 1

    receipt = data.get("receipt")
    if not receipt:
        print(f"Missing receipt in response: {data!r}", file=sys.stderr)
        return 1

    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
