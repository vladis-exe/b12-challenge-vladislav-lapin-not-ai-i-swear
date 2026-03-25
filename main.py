#!/usr/bin/env python3

import argparse
import json
import sys
from typing import Any

import requests


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def fetch(url: str, timeout_s: float, max_body_chars: int, print_headers: bool) -> int:
    try:
        resp = requests.get(url, timeout=timeout_s)
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    content_type = resp.headers.get("Content-Type", "")
    print(f"Status: {resp.status_code}")
    if print_headers:
        print("Response headers:")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")

    body_text = resp.text
    print(f"Content-Type: {content_type or 'unknown'}")

    is_jsonish = "application/json" in content_type.lower() or body_text.lstrip().startswith("{")
    if is_jsonish:
        try:
            data: Any = resp.json()
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
            print(_truncate(pretty, max_body_chars))
        except json.JSONDecodeError:
            print(_truncate(body_text, max_body_chars))
    else:
        print(_truncate(body_text, max_body_chars))

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple HTTP GET example using requests.")
    parser.add_argument("--url", default="https://httpbin.org/get", help="URL to fetch")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout seconds")
    parser.add_argument(
        "--max-body-chars",
        type=int,
        default=2000,
        help="Max number of response body characters to print",
    )
    parser.add_argument("--print-headers", action="store_true", help="Print response headers")
    args = parser.parse_args()

    return fetch(
        url=args.url,
        timeout_s=args.timeout,
        max_body_chars=args.max_body_chars,
        print_headers=args.print_headers,
    )


if __name__ == "__main__":
    raise SystemExit(main())
