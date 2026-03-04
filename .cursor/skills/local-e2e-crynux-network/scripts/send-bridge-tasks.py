#!/usr/bin/env python3

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


BRIDGE_BASE_URL = os.getenv("BRIDGE_BASE_URL", "http://localhost:8080")
TASK_TIMEOUT_SECONDS = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

# TODO: Replace with the actual Bridge API paths and payload schema.
LLM_SUBMIT_PATH = os.getenv("LLM_SUBMIT_PATH", "/api/v1/tasks/llm")
VLM_SUBMIT_PATH = os.getenv("VLM_SUBMIT_PATH", "/api/v1/tasks/vlm")
TASK_STATUS_PATH_TEMPLATE = os.getenv("TASK_STATUS_PATH_TEMPLATE", "/api/v1/tasks/%s")


def log(message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {message}")


def _request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {method} {url}. Response: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {method} {url}: {exc}") from exc

    try:
        return json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {method} {url}: {body}") from exc


def submit_task(path: str, payload: dict) -> dict:
    return _request_json(f"{BRIDGE_BASE_URL}{path}", method="POST", payload=payload)


def extract_task_id(response: dict) -> str:
    task_id = response.get("task_id") or response.get("id") or ""
    if not isinstance(task_id, str):
        return ""
    return task_id


def poll_task_until_done(task_id: str) -> None:
    start_ts = time.time()
    while True:
        status_path = TASK_STATUS_PATH_TEMPLATE % task_id
        response = _request_json(f"{BRIDGE_BASE_URL}{status_path}", method="GET")
        status = str(response.get("status", "")).lower()

        if status in {"succeeded", "success", "completed"}:
            log(f"Task {task_id} completed with status: {status}")
            return
        if status in {"failed", "error"}:
            raise RuntimeError(f"Task {task_id} failed. Response: {json.dumps(response)}")

        elapsed = time.time() - start_ts
        if elapsed >= TASK_TIMEOUT_SECONDS:
            raise RuntimeError(
                f"Task {task_id} timed out after {TASK_TIMEOUT_SECONDS}s. "
                f"Last response: {json.dumps(response)}"
            )
        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> int:
    # TODO: Replace these payloads with real Bridge task payloads.
    llm_payload = {"type": "llm", "input": "e2e smoke test"}
    vlm_payload = {
        "type": "vlm",
        "input": {"text": "describe image", "image_url": "https://example.com/image.png"},
    }

    log("Submitting LLM task...")
    llm_response = submit_task(LLM_SUBMIT_PATH, llm_payload)
    llm_task_id = extract_task_id(llm_response)
    if not llm_task_id:
        raise RuntimeError(f"Failed to extract LLM task id. Response: {json.dumps(llm_response)}")
    log(f"LLM task id: {llm_task_id}")

    log("Submitting VLM task...")
    vlm_response = submit_task(VLM_SUBMIT_PATH, vlm_payload)
    vlm_task_id = extract_task_id(vlm_response)
    if not vlm_task_id:
        raise RuntimeError(f"Failed to extract VLM task id. Response: {json.dumps(vlm_response)}")
    log(f"VLM task id: {vlm_task_id}")

    log("Polling LLM task...")
    poll_task_until_done(llm_task_id)

    log("Polling VLM task...")
    poll_task_until_done(vlm_task_id)

    log("All Bridge e2e tasks succeeded.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
