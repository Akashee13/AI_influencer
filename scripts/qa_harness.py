#!/usr/bin/env python3
"""Interactive QA harness for gateway-driven workflow testing.

This script is intentionally operator-in-the-loop: it exercises the real
gateway path, downloads the resulting artifact, and guides a human reviewer
through a structured gap-analysis report.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QA_RUNS_DIR = ROOT / "docs" / "gap-finding"
LOCAL_CONFIG_PATH = ROOT / "qa_harness.local.json"
FALLBACK_GATEWAY_URL = "http://127.0.0.1:9000"


class QaHarnessError(RuntimeError):
    pass


def load_local_config() -> dict[str, Any]:
    if not LOCAL_CONFIG_PATH.exists():
        return {}
    try:
        payload = json.loads(LOCAL_CONFIG_PATH.read_text())
    except Exception as exc:
        raise QaHarnessError(f"failed to read local harness config at {LOCAL_CONFIG_PATH}: {exc}") from exc
    if not isinstance(payload, dict):
        raise QaHarnessError(f"local harness config must be a JSON object: {LOCAL_CONFIG_PATH}")
    return payload


def prompt_text(label: str, *, default: str = "", required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            value = default
        if value or not required:
            return value
        print("This field is required.")


def prompt_multiline(label: str, *, required: bool = False) -> str:
    print(f"{label} (finish with an empty line):")
    lines: list[str] = []
    while True:
        line = input()
        if not line.strip():
            if lines or not required:
                return "\n".join(lines).strip()
            print("This field is required. Enter at least one line.")
            continue
        lines.append(line.rstrip())


def prompt_choice(label: str, options: list[str], *, default: str | None = None) -> str:
    if not options:
        raise QaHarnessError(f"No options available for {label}.")
    normalized = {str(index + 1): option for index, option in enumerate(options)}
    print(label)
    for index, option in enumerate(options, start=1):
        marker = " (default)" if default and option == default else ""
        print(f"  {index}. {option}{marker}")
    while True:
        raw = input("> ").strip()
        if not raw and default:
            return default
        if raw in normalized:
            return normalized[raw]
        if raw in options:
            return raw
        print("Choose a number from the list or paste the exact option.")


def prompt_rating(label: str) -> str:
    mapping = {
        "1": "pass",
        "2": "partial",
        "3": "fail",
    }
    print(f"{label}\n  1. pass\n  2. partial\n  3. fail")
    while True:
        raw = input("> ").strip().lower()
        if raw in mapping:
            return mapping[raw]
        if raw in mapping.values():
            return raw
        print("Choose 1, 2, 3 or type pass/partial/fail.")


def parse_args() -> argparse.Namespace:
    local_config = load_local_config()
    default_gateway_url = str(
        os.environ.get("COMFYUI_GATEWAY_URL")
        or local_config.get("gateway_url")
        or FALLBACK_GATEWAY_URL
    ).strip()
    default_gateway_token = str(
        os.environ.get("COMFYUI_GATEWAY_TOKEN")
        or local_config.get("gateway_token")
        or ""
    ).strip()
    default_workflow = str(local_config.get("default_workflow") or "").strip()
    default_scene_url = str(local_config.get("default_scene_url") or "").strip()
    default_filename_prefix = str(local_config.get("default_filename_prefix") or "").strip()

    parser = argparse.ArgumentParser(description="Interactive QA harness for gateway-driven workflow testing.")
    parser.add_argument("--gateway-url", default=default_gateway_url, help="Gateway base URL.")
    parser.add_argument("--token", default=default_gateway_token, help="Gateway bearer token.")
    parser.add_argument("--workflow", default=default_workflow, help="Prefill workflow selection by exact workflow filename.")
    parser.add_argument("--scene-url", default=default_scene_url, help="Prefill scene reference Instagram/direct image URL.")
    parser.add_argument("--filename-prefix", default=default_filename_prefix, help="Prefill filename prefix.")
    return parser.parse_args()


def sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "qa-run"


def auth_headers(token: str, *, json_body: bool = False) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def api_get_json(base_url: str, path: str, token: str) -> Any:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = urllib.request.Request(url, headers=auth_headers(token))
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post_json(base_url: str, path: str, token: str, payload: dict[str, Any]) -> Any:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_headers(token, json_body=True),
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(base_url: str, path: str, token: str, destination: Path) -> Path:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req = urllib.request.Request(url, headers=auth_headers(token))
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        destination.write_bytes(body)
    return destination


def choose_workflow(base_url: str, token: str, *, workflow_name: str = "") -> dict[str, Any]:
    payload = api_get_json(base_url, "/workflows", token)
    workflows = payload.get("workflows", [])
    if not workflows:
        raise QaHarnessError("Gateway returned no workflows.")
    options = [workflow["name"] for workflow in workflows if workflow.get("name")]
    selected_default = workflow_name if workflow_name in options else options[0]
    selected_name = prompt_choice("Choose a workflow:", options, default=selected_default)
    for workflow in workflows:
        if workflow.get("name") == selected_name:
            return workflow
    raise QaHarnessError(f"Selected workflow not found: {selected_name}")


def upload_scene_reference(base_url: str, token: str, source_url: str) -> str:
    payload = api_post_json(
        base_url,
        "/upload/reference-url",
        token,
        {"url": source_url},
    )
    if not payload.get("ok"):
        raise QaHarnessError(payload.get("error", "scene reference upload failed"))
    filename = str(payload.get("filename", "")).strip()
    if not filename:
        raise QaHarnessError("Scene upload succeeded but no filename was returned.")
    return filename


def submit_run(base_url: str, token: str, workflow_name: str, overrides: dict[str, Any]) -> dict[str, Any]:
    payload = api_post_json(
        base_url,
        "/generate",
        token,
        {
            "workflow": workflow_name,
            "wait": False,
            "overrides": overrides,
        },
    )
    if not payload.get("ok"):
        raise QaHarnessError(payload.get("error", "generation submit failed"))
    return payload


def poll_status(base_url: str, token: str, prompt_id: str, *, max_wait_s: int = 1800) -> dict[str, Any]:
    backoff_schedule = [5, 10, 20, 40, 60]
    deadline = time.time() + max_wait_s
    attempt = 0
    while time.time() < deadline:
        payload = api_get_json(base_url, f"/status/{prompt_id}", token)
        status = str(payload.get("status", "unknown")).lower()
        print(f"Status: {status}")
        if status == "completed":
            return payload
        if status in {"failed", "error"}:
            return payload
        sleep_for = backoff_schedule[min(attempt, len(backoff_schedule) - 1)]
        attempt += 1
        time.sleep(sleep_for)
    raise QaHarnessError(f"Timed out waiting for prompt {prompt_id}.")


def fetch_run_detail(base_url: str, token: str, prompt_id: str) -> dict[str, Any]:
    payload = api_get_json(base_url, f"/runs/{prompt_id}", token)
    if not payload.get("ok"):
        raise QaHarnessError(payload.get("error", "failed to fetch run detail"))
    run = payload.get("run")
    if not isinstance(run, dict):
        raise QaHarnessError("Gateway returned malformed run detail.")
    return run


def build_run_dir(prompt_id: str, workflow_name: str) -> Path:
    QA_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = QA_RUNS_DIR / f"{stamp}_{sanitize_slug(workflow_name)}_{prompt_id[:8]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def download_first_output(base_url: str, token: str, run: dict[str, Any], run_dir: Path) -> Path | None:
    outputs = run.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        return None
    first = outputs[0]
    download_url = first.get("download_url")
    filename = first.get("filename") or "output.bin"
    if not isinstance(download_url, str) or not download_url:
        return None
    destination = run_dir / sanitize_slug(str(filename))
    return download_file(base_url, download_url, token, destination)


def build_report(
    *,
    workflow_name: str,
    prompt_id: str,
    scene_reference_url: str,
    expected_outcome: str,
    run: dict[str, Any],
    local_output_path: Path | None,
    review: dict[str, Any],
) -> str:
    output_line = str(local_output_path) if local_output_path else "No local download captured."
    top_gaps = review.get("top_gaps", "").strip() or "None provided."
    recommended_fixes = review.get("recommended_fixes", "").strip() or "No recommendations recorded."
    raw_notes = review.get("notes", "").strip() or "No additional notes recorded."
    return f"""# QA Gap Report

## Run Summary

- Workflow: `{workflow_name}`
- Prompt ID: `{prompt_id}`
- Submitted At: `{run.get('submitted_at', 'unknown')}`
- Completed At: `{run.get('completed_at', 'unknown')}`
- Scene Reference URL: {scene_reference_url or 'None'}
- Local Output: `{output_line}`

## Expected Outcome

{expected_outcome}

## Structured Review

- Face consistency: **{review.get('face_consistency', 'unknown')}**
- Scene/style similarity: **{review.get('scene_similarity', 'unknown')}**
- Wardrobe adaptation quality: **{review.get('wardrobe_adaptation', 'unknown')}**
- Overall outcome: **{review.get('overall', 'unknown')}**

## Top Gaps

{top_gaps}

## Recommended Fixes

{recommended_fixes}

## Additional Notes

{raw_notes}

## Runtime Metadata

```json
{json.dumps(run, indent=2, ensure_ascii=False)}
```
"""


def collect_review() -> dict[str, Any]:
    print("\nReview the generated output, then answer the QA prompts.\n")
    review = {
        "face_consistency": prompt_rating("How well did the result preserve the workflow's anchor face?"),
        "scene_similarity": prompt_rating("How well did the result follow the intended scene/style inspiration?"),
        "wardrobe_adaptation": prompt_rating("How good was the clothing adaptation versus the expected outcome?"),
        "overall": prompt_rating("Overall QA status for this run?"),
        "top_gaps": prompt_multiline("List the top gaps to fix", required=True),
        "recommended_fixes": prompt_multiline("List recommended fixes or experiments", required=True),
        "notes": prompt_multiline("Additional notes"),
    }
    return review


def main() -> int:
    try:
        args = parse_args()
        print("QA Harness Agent\n")
        base_url = prompt_text("Gateway base URL", default=args.gateway_url, required=True)
        token = args.token or getpass.getpass("Gateway token: ").strip()
        if not token:
            raise QaHarnessError("Gateway token is required.")

        workflow = choose_workflow(base_url, token, workflow_name=args.workflow)
        workflow_name = str(workflow.get("name", "")).strip()
        defaults = workflow.get("defaults", {}) if isinstance(workflow, dict) else {}
        supports_scene_reference = bool(defaults.get("supports_scene_reference_image"))

        print(f"\nSelected workflow: {workflow_name}")
        expected_outcome = prompt_multiline("Describe the expected outcome for this QA run", required=True)

        scene_reference_url = ""
        scene_reference_image = ""
        if supports_scene_reference:
            scene_reference_url = prompt_text(
                "Paste the scene reference Instagram post or direct image URL",
                default=args.scene_url,
                required=True,
            )
            print("Uploading scene reference...")
            scene_reference_image = upload_scene_reference(base_url, token, scene_reference_url)
            print(f"Scene reference saved as: {scene_reference_image}")

        filename_prefix_default = f"qa-{sanitize_slug(workflow_name).lower()}"
        filename_prefix = prompt_text(
            "Filename prefix",
            default=args.filename_prefix or filename_prefix_default,
            required=True,
        )

        overrides: dict[str, Any] = {"filename_prefix": filename_prefix}
        if supports_scene_reference and scene_reference_image:
            overrides["scene_reference_image"] = scene_reference_image

        print("Submitting generation request...")
        submit_payload = submit_run(base_url, token, workflow_name, overrides)
        prompt_id = str(submit_payload.get("prompt_id", "")).strip()
        if not prompt_id:
            raise QaHarnessError("Submit succeeded but no prompt_id was returned.")
        print(f"Submitted prompt: {prompt_id}")

        print("Waiting for completion...")
        terminal_status = poll_status(base_url, token, prompt_id)

        run = fetch_run_detail(base_url, token, prompt_id)
        run_dir = build_run_dir(prompt_id, workflow_name)
        save_json(run_dir / "run.json", run)
        local_output_path = download_first_output(base_url, token, run, run_dir)
        if local_output_path:
            print(f"Downloaded output to: {local_output_path}")
        else:
            print("No downloadable output was found for this run.")
        if str(terminal_status.get("status", "")).lower() in {"failed", "error"}:
            error_text = str(terminal_status.get("error_text", "")).strip()
            if error_text:
                print(f"Run reached a terminal error state: {error_text}")
            else:
                print("Run reached a terminal error state.")

        review = collect_review()
        report_body = build_report(
            workflow_name=workflow_name,
            prompt_id=prompt_id,
            scene_reference_url=scene_reference_url,
            expected_outcome=expected_outcome,
            run=run,
            local_output_path=local_output_path,
            review=review,
        )
        report_path = run_dir / "report.md"
        report_path.write_text(report_body)
        print(f"\nQA report written to: {report_path}")
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except QaHarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
