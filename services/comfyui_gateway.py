#!/usr/bin/env python3
"""Small authenticated gateway for a ComfyUI instance running on the same VM.

This service exposes a minimal HTTP API that:
- accepts generation requests from your local project
- loads a locked ComfyUI workflow JSON
- applies prompt/setting overrides
- submits to local ComfyUI on 127.0.0.1:8188
- returns prompt IDs immediately for async polling
- optionally waits for completion when explicitly requested

It is intentionally stdlib-only so deployment on the VM stays simple.
"""

from __future__ import annotations

import base64
import html
import json
import os
import random
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import parse
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "comfyui" / "workflows" / "mumbai-yoga-anchor-v1.json"
WEB_DIR = ROOT / "web"
DASHBOARD_PATH = WEB_DIR / "dashboard.html"
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
COMFYUI_BROWSER_URL = os.environ.get("COMFYUI_BROWSER_URL", COMFYUI_URL)
WORKFLOW_DIR = Path(os.environ.get("WORKFLOW_DIR", str(DEFAULT_WORKFLOW.parent)))
API_TOKEN = os.environ.get("COMFYUI_GATEWAY_TOKEN", "")
HOST = os.environ.get("COMFYUI_GATEWAY_HOST", "0.0.0.0")
PORT = int(os.environ.get("COMFYUI_GATEWAY_PORT", "9000"))
RUNS_DB_PATH = Path(os.environ.get("COMFYUI_RUNS_DB", str(ROOT / "data" / "runs.db")))
COMFYUI_OUTPUT_DIR = Path(
    os.environ.get("COMFYUI_OUTPUT_DIR", str(Path.home() / "comfy" / "output"))
)
COMFYUI_INPUT_DIR = Path(
    os.environ.get("COMFYUI_INPUT_DIR", str(Path.home() / "comfy" / "input"))
)
ALLOWED_REFERENCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REMOTE_IMAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
REMOTE_PAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


class WorkflowError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def random_seed() -> int:
    return random.SystemRandom().randrange(10**14, 10**15)


def ensure_db() -> None:
    RUNS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(RUNS_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                prompt_id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                client_id TEXT NOT NULL,
                status TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                completed_at TEXT,
                overrides_json TEXT NOT NULL,
                raw_request_json TEXT NOT NULL,
                raw_response_json TEXT,
                history_json TEXT,
                outputs_json TEXT,
                error_text TEXT,
                deleted_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_runs_status_submitted
            ON runs(status, submitted_at DESC)
            """
        )
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(runs)").fetchall()
        }
        if "deleted_at" not in columns:
            conn.execute("ALTER TABLE runs ADD COLUMN deleted_at TEXT")


def db_connect() -> sqlite3.Connection:
    ensure_db()
    conn = sqlite3.connect(RUNS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def record_run_submission(
    *,
    prompt_id: str,
    workflow_name: str,
    client_id: str,
    overrides: dict[str, Any],
    raw_request: dict[str, Any],
    raw_response: dict[str, Any],
) -> None:
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO runs (
                prompt_id,
                workflow_name,
                client_id,
                status,
                submitted_at,
                overrides_json,
                raw_request_json,
                raw_response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(prompt_id) DO UPDATE SET
                workflow_name=excluded.workflow_name,
                client_id=excluded.client_id,
                status=excluded.status,
                submitted_at=excluded.submitted_at,
                overrides_json=excluded.overrides_json,
                raw_request_json=excluded.raw_request_json,
                raw_response_json=excluded.raw_response_json,
                error_text=NULL,
                deleted_at=NULL
            """,
            (
                prompt_id,
                workflow_name,
                client_id,
                "submitted",
                utc_now(),
                json_dumps(overrides),
                json_dumps(raw_request),
                json_dumps(raw_response),
            ),
        )


def upsert_discovered_run(
    *,
    prompt_id: str,
    status: str,
    prompt_payload: dict[str, Any] | None = None,
    client_id: str = "",
    workflow_name: str = DEFAULT_WORKFLOW.name,
) -> None:
    raw_request = {"prompt": prompt_payload or {}, "client_id": client_id} if prompt_payload else {}
    raw_response = {"prompt_id": prompt_id}
    with db_connect() as conn:
        existing = conn.execute(
            "SELECT deleted_at FROM runs WHERE prompt_id = ?",
            (prompt_id,),
        ).fetchone()
        if existing and existing["deleted_at"] and status == "completed":
            return
        conn.execute(
            """
            INSERT INTO runs (
                prompt_id,
                workflow_name,
                client_id,
                status,
                submitted_at,
                overrides_json,
                raw_request_json,
                raw_response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(prompt_id) DO UPDATE SET
                status=excluded.status
            """,
            (
                prompt_id,
                workflow_name,
                client_id,
                status,
                utc_now(),
                json_dumps({}),
                json_dumps(raw_request),
                json_dumps(raw_response),
            ),
        )
        conn.execute(
            """
            UPDATE runs
            SET deleted_at = NULL
            WHERE prompt_id = ? AND deleted_at IS NOT NULL AND status != 'completed'
            """,
            (prompt_id,),
        )


def infer_workflow_name_from_prompt(prompt_payload: dict[str, Any] | None) -> str:
    if not prompt_payload:
        return DEFAULT_WORKFLOW.name
    save_image = prompt_payload.get("7")
    if isinstance(save_image, dict):
        inputs = save_image.get("inputs", {})
        if isinstance(inputs, dict) and inputs.get("filename_prefix"):
            return DEFAULT_WORKFLOW.name
    return DEFAULT_WORKFLOW.name


def row_to_run(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    for key in ("overrides_json", "raw_request_json", "raw_response_json", "history_json", "outputs_json"):
        if result.get(key):
            result[key.removesuffix("_json")] = json.loads(result[key])
        result.pop(key, None)
    return result


def list_runs_by_status(
    statuses: list[str],
    *,
    limit: int = 100,
    offset: int = 0,
    query: str = "",
) -> tuple[list[dict[str, Any]], int]:
    placeholders = ", ".join("?" for _ in statuses)
    where = [f"status IN ({placeholders})", "deleted_at IS NULL"]
    params: list[Any] = list(statuses)

    if query:
        where.append(
            "("
            "prompt_id LIKE ? OR "
            "workflow_name LIKE ? OR "
            "overrides_json LIKE ? OR "
            "outputs_json LIKE ?"
            ")"
        )
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    where_sql = " AND ".join(where)
    with db_connect() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM runs WHERE {where_sql}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT *
            FROM runs
            WHERE {where_sql}
            ORDER BY submitted_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    return [row_to_run(row) for row in rows], int(total)


def list_nonterminal_prompt_ids() -> list[str]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT prompt_id
            FROM runs
            WHERE status IN ('submitted', 'pending', 'running', 'unknown')
              AND deleted_at IS NULL
            ORDER BY submitted_at DESC
            """
        ).fetchall()
    return [row["prompt_id"] for row in rows]


def parse_history_record(history: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    if prompt_id in history:
        record = history[prompt_id]
    elif history:
        record = next(iter(history.values()))
    else:
        record = {}
    if not isinstance(record, dict):
        return {}
    return record


def extract_outputs_from_history(history: dict[str, Any], prompt_id: str) -> list[dict[str, Any]]:
    record = parse_history_record(history, prompt_id)
    outputs = record.get("outputs", {})
    files: list[dict[str, Any]] = []

    if not isinstance(outputs, dict):
        return files

    for node_id, node_output in outputs.items():
        if not isinstance(node_output, dict):
            continue
        for kind in ("images", "gifs", "audio"):
            items = node_output.get(kind, [])
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                filename = item.get("filename")
                subfolder = item.get("subfolder", "")
                file_type = item.get("type", "")
                relative_path = Path(subfolder) / filename if subfolder else Path(str(filename))
                files.append(
                    {
                        "node_id": str(node_id),
                        "kind": kind,
                        "index": index,
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": file_type,
                        "relative_path": str(relative_path),
                        "download_url": f"/download/{prompt_id}/{len(files)}",
                    }
                )
    return files


def resolve_output_path(output: dict[str, Any]) -> Path:
    relative_path = Path(output["relative_path"])
    return (COMFYUI_OUTPUT_DIR / relative_path).resolve()


def update_run_record(
    prompt_id: str,
    *,
    status: str,
    history: dict[str, Any] | None = None,
    error_text: str | None = None,
) -> None:
    outputs = extract_outputs_from_history(history, prompt_id) if history else None
    completed_at = utc_now() if status == "completed" else None
    with db_connect() as conn:
        conn.execute(
            """
            UPDATE runs
            SET status = ?,
                completed_at = COALESCE(?, completed_at),
                history_json = COALESCE(?, history_json),
                outputs_json = COALESCE(?, outputs_json),
                error_text = COALESCE(?, error_text)
            WHERE prompt_id = ?
              AND deleted_at IS NULL
            """,
            (
                status,
                completed_at,
                json_dumps(history) if history is not None else None,
                json_dumps(outputs) if outputs is not None else None,
                error_text,
                prompt_id,
            ),
        )


def get_run(prompt_id: str) -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE prompt_id = ? AND deleted_at IS NULL",
            (prompt_id,),
        ).fetchone()
    return row_to_run(row) if row else None


def mark_run_deleted(prompt_id: str) -> None:
    with db_connect() as conn:
        conn.execute(
            """
            UPDATE runs
            SET deleted_at = ?, outputs_json = '[]'
            WHERE prompt_id = ?
            """,
            (utc_now(), prompt_id),
        )


def api_post_nojson(url: str, payload: dict[str, Any]) -> tuple[int, str]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req) as resp:
            return int(resp.status), resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")


def delete_run_and_outputs(prompt_id: str) -> dict[str, Any]:
    run = get_run(prompt_id)
    if not run:
        raise WorkflowError("run not found")

    deleted_files: list[str] = []
    missing_files: list[str] = []
    comfy_actions: list[dict[str, Any]] = []
    outputs = run.get("outputs", []) or []

    for output in outputs:
        try:
            file_path = resolve_output_path(output)
            if COMFYUI_OUTPUT_DIR.resolve() not in file_path.parents:
                continue
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
            else:
                missing_files.append(str(file_path))
        except Exception:
            continue

    for endpoint, payload in (
        (f"{COMFYUI_URL.rstrip('/')}/history", {"delete": [prompt_id]}),
        (f"{COMFYUI_URL.rstrip('/')}/queue", {"delete": [prompt_id]}),
    ):
        try:
            status, body = api_post_nojson(endpoint, payload)
            comfy_actions.append({"endpoint": endpoint, "status": status, "body": body[:500]})
        except Exception as exc:
            comfy_actions.append({"endpoint": endpoint, "error": str(exc)})

    mark_run_deleted(prompt_id)
    return {
        "ok": True,
        "prompt_id": prompt_id,
        "deleted_files": deleted_files,
        "missing_files": missing_files,
        "comfy_actions": comfy_actions,
    }


def summarize_run(run: dict[str, Any], *, include_outputs: bool = False) -> dict[str, Any]:
    summary = {
        "prompt_id": run["prompt_id"],
        "workflow_name": run["workflow_name"],
        "client_id": run["client_id"],
        "status": run["status"],
        "submitted_at": run["submitted_at"],
        "completed_at": run.get("completed_at"),
        "error_text": run.get("error_text"),
        "overrides": run.get("overrides"),
    }
    if include_outputs:
        summary["outputs"] = run.get("outputs", [])
    return summary


def detail_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_id": run["prompt_id"],
        "workflow_name": run["workflow_name"],
        "client_id": run["client_id"],
        "status": run["status"],
        "submitted_at": run["submitted_at"],
        "completed_at": run.get("completed_at"),
        "error_text": run.get("error_text"),
        "overrides": run.get("overrides"),
        "outputs": run.get("outputs", []),
        "history": run.get("history"),
        "raw_request": run.get("raw_request"),
        "raw_response": run.get("raw_response"),
    }


def api_get(url: str) -> Any:
    with request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post(url: str, payload: dict[str, Any]) -> Any:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = f"HTTP {exc.code}: {body or exc.reason}"
        raise RuntimeError(message) from exc


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def sanitize_reference_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip().replace(" ", "_")
    if not cleaned:
        cleaned = f"reference_{uuid.uuid4().hex[:8]}.png"
    stem = Path(cleaned).stem or f"reference_{uuid.uuid4().hex[:8]}"
    suffix = Path(cleaned).suffix.lower() or ".png"
    if suffix not in ALLOWED_REFERENCE_SUFFIXES:
        raise WorkflowError("unsupported reference image type")
    safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in {"-", "_"}).strip("._-") or "reference"
    return f"{safe_stem}_{uuid.uuid4().hex[:8]}{suffix}"


def save_reference_image(filename: str, content_b64: str) -> str:
    safe_name = sanitize_reference_filename(filename)
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        raw = base64.b64decode(content_b64, validate=True)
    except Exception as exc:  # pragma: no cover - malformed payload
        raise WorkflowError("invalid base64 image payload") from exc
    if not raw:
        raise WorkflowError("empty reference image payload")
    destination = COMFYUI_INPUT_DIR / safe_name
    destination.write_bytes(raw)
    return safe_name


def guess_suffix_from_content_type(content_type: str) -> str:
    content_type = (content_type or "").split(";", 1)[0].strip().lower()
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }.get(content_type, ".jpg")


def extract_preview_image_url(html: str) -> str | None:
    patterns = (
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return html_unescape_url(match.group(1))
    return None


def html_unescape_url(value: str) -> str:
    return html.unescape(value.strip())


def fetch_url_bytes(url: str) -> tuple[bytes, str]:
    req = request.Request(url, headers=REMOTE_IMAGE_HEADERS)
    with request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read(15 * 1024 * 1024 + 1)
        if len(data) > 15 * 1024 * 1024:
            raise WorkflowError("remote image is too large")
        return data, content_type


def save_reference_image_from_url(source_url: str) -> str:
    parsed = parse.urlsplit(source_url)
    if parsed.scheme not in {"http", "https"}:
        raise WorkflowError("reference URL must start with http or https")

    direct_image = Path(parsed.path).suffix.lower() in ALLOWED_REFERENCE_SUFFIXES
    target_url = source_url

    if not direct_image:
        req = request.Request(source_url, headers=REMOTE_PAGE_HEADERS)
        with request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if content_type.lower().startswith("image/"):
                data = resp.read(15 * 1024 * 1024 + 1)
                if len(data) > 15 * 1024 * 1024:
                    raise WorkflowError("remote image is too large")
                suffix = guess_suffix_from_content_type(content_type)
                filename = sanitize_reference_filename(Path(parsed.path).stem + suffix)
                COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
                destination = COMFYUI_INPUT_DIR / filename
                destination.write_bytes(data)
                return filename
            body = resp.read(1024 * 1024).decode("utf-8", errors="replace")
            preview_url = extract_preview_image_url(body)
            if not preview_url:
                raise WorkflowError("could not extract a preview image from the provided page")
            target_url = parse.urljoin(source_url, preview_url)

    data, content_type = fetch_url_bytes(target_url)
    suffix = Path(parse.urlsplit(target_url).path).suffix.lower()
    if suffix not in ALLOWED_REFERENCE_SUFFIXES:
        suffix = guess_suffix_from_content_type(content_type)
    filename = sanitize_reference_filename(Path(parse.urlsplit(target_url).path).stem + suffix)
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = COMFYUI_INPUT_DIR / filename
    destination.write_bytes(data)
    return filename


def list_workflow_files() -> list[str]:
    return sorted(path.name for path in WORKFLOW_DIR.glob("*.json"))


def workflow_defaults(path: Path) -> dict[str, Any]:
    workflow = load_json(path)
    nodes_by_type = {node["type"]: node for node in workflow.get("nodes", [])}
    extra = workflow.get("extra", {}) if isinstance(workflow.get("extra", {}), dict) else {}
    ui_defaults = extra.get("ui_defaults", {}) if isinstance(extra.get("ui_defaults", {}), dict) else {}

    latent = nodes_by_type.get("EmptyLatentImage", {})
    sampler = nodes_by_type.get("KSampler", {})
    save = nodes_by_type.get("SaveImage", {})
    load_image = nodes_by_type.get("LoadImage", {})
    positive_node, negative_node = resolve_prompt_nodes(workflow)

    latent_widgets = list(latent.get("widgets_values", []))
    sampler_widgets = list(sampler.get("widgets_values", []))
    save_widgets = list(save.get("widgets_values", []))
    load_image_widgets = list(load_image.get("widgets_values", []))

    positive_prompt = positive_node["widgets_values"][0] if positive_node.get("widgets_values") else ""
    negative_prompt = negative_node["widgets_values"][0] if negative_node.get("widgets_values") else ""

    return {
        "name": path.name,
        "defaults": {
            "width": ui_defaults.get("width", latent_widgets[0] if len(latent_widgets) > 0 else None),
            "height": ui_defaults.get("height", latent_widgets[1] if len(latent_widgets) > 1 else None),
            "batch_size": ui_defaults.get("batch_size", latent_widgets[2] if len(latent_widgets) > 2 else None),
            "seed": sampler_widgets[0] if len(sampler_widgets) > 0 else None,
            "control_after_generate": sampler_widgets[1] if len(sampler_widgets) > 1 else None,
            "steps": sampler_widgets[2] if len(sampler_widgets) > 2 else None,
            "cfg": sampler_widgets[3] if len(sampler_widgets) > 3 else None,
            "sampler": sampler_widgets[4] if len(sampler_widgets) > 4 else None,
            "scheduler": sampler_widgets[5] if len(sampler_widgets) > 5 else None,
            "denoise": sampler_widgets[6] if len(sampler_widgets) > 6 else None,
            "filename_prefix": save_widgets[0] if len(save_widgets) > 0 else None,
            "supports_reference_image": bool(load_image),
            "reference_image": load_image_widgets[0] if len(load_image_widgets) > 0 else None,
            "positive_prompt": positive_prompt,
            "positive_prompt_sections": split_positive_prompt_sections(positive_prompt),
            "negative_prompt": negative_prompt,
        },
    }


def list_workflow_summaries() -> list[dict[str, Any]]:
    return [workflow_defaults(path) for path in sorted(WORKFLOW_DIR.glob("*.json"))]


PROMPT_SECTION_KEYS = (
    "identity",
    "composition",
    "clothing",
    "background",
    "mood",
    "camera",
)

SECTION_KEYWORDS = {
    "identity": (
        "same face identity",
        "indian facial",
        "skin",
        "eyes",
        "eyebrows",
        "nose",
        "lips",
        "hair",
        "makeup",
        "body",
        "waist",
        "arms",
        "hourglass",
        "wellness influencer",
        "creator look",
        "creator presence",
        "creator energy",
    ),
    "composition": (
        "pose",
        "framing",
        "front-facing",
        "front facing",
        "standing",
        "seated",
        "sitting",
        "portrait",
        "three-quarter",
        "three quarter",
        "mirror",
        "centered",
        "body angle",
        "posture",
    ),
    "clothing": (
        "sports bra",
        "leggings",
        "shirt",
        "athleisure",
        "activewear",
        "outfit",
        "wearing",
        "wardrobe",
        "knitwear",
        "yoga set",
        "styling",
        "fabric",
    ),
    "background": (
        "cafe",
        "apartment",
        "studio",
        "interior",
        "resort",
        "daylight",
        "background",
        "setting",
        "environment",
        "bangalore",
        "mumbai",
        "luxury decor",
        "location",
    ),
    "mood": (
        "smile",
        "confidence",
        "expression",
        "energy",
        "serene",
        "calm",
        "approachable",
        "editorial mood",
        "self-assured",
        "self assured",
        "composed",
        "warm",
    ),
    "camera": (
        "realistic",
        "smartphone",
        "sharp focus",
        "crisp",
        "skin texture",
        "lighting",
        "photo",
        "editorial",
        "daylight realism",
        "camera",
        "detail",
        "pores",
        "contrast",
        "depth",
    ),
}


def merge_positive_prompt_sections(sections: Any) -> str:
    if not isinstance(sections, dict):
        return ""
    parts: list[str] = []
    for key in PROMPT_SECTION_KEYS:
        value = sections.get(key)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                parts.append(cleaned)
    return ", ".join(parts)


def split_positive_prompt_sections(prompt: str) -> dict[str, str]:
    sections = {key: [] for key in PROMPT_SECTION_KEYS}
    chunks = [chunk.strip() for chunk in prompt.replace("\n", " ").split(",") if chunk.strip()]

    for chunk in chunks:
        chunk_lower = chunk.lower()
        assigned_key = "identity"
        best_score = 0
        for key, keywords in SECTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in chunk_lower)
            if score > best_score:
                best_score = score
                assigned_key = key
        sections[assigned_key].append(chunk)

    return {key: ", ".join(value) for key, value in sections.items()}


def build_link_map(workflow: dict[str, Any]) -> dict[int, tuple[int, int, int, int, str]]:
    link_map: dict[int, tuple[int, int, int, int, str]] = {}
    for raw in workflow.get("links", []):
        link_id, from_node, from_slot, to_node, to_slot, value_type = raw
        link_map[link_id] = (from_node, from_slot, to_node, to_slot, value_type)
    return link_map


def find_nodes_by_type(workflow: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [node for node in workflow.get("nodes", []) if node.get("type") == node_type]


def node_map(workflow: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in workflow.get("nodes", [])}


def input_ref(link_map: dict[int, tuple[int, int, int, int, str]], link_id: int) -> list[Any]:
    from_node, from_slot, *_rest = link_map[link_id]
    return [str(from_node), from_slot]


def resolve_prompt_nodes(workflow: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ksampler_node = find_nodes_by_type(workflow, "KSampler")[0]
    link_map = build_link_map(workflow)
    nodes = node_map(workflow)

    pos_link = next(inp for inp in ksampler_node["inputs"] if inp["name"] == "positive")["link"]
    neg_link = next(inp for inp in ksampler_node["inputs"] if inp["name"] == "negative")["link"]

    pos_node_id = link_map[pos_link][0]
    neg_node_id = link_map[neg_link][0]
    return nodes[int(pos_node_id)], nodes[int(neg_node_id)]


def ui_workflow_to_api_prompt(workflow: dict[str, Any]) -> dict[str, Any]:
    link_map = build_link_map(workflow)
    api_prompt: dict[str, Any] = {}

    for node in workflow.get("nodes", []):
        node_id = str(node["id"])
        node_type = node["type"]
        widgets = list(node.get("widgets_values", []))

        if node_type == "CheckpointLoaderSimple":
            api_prompt[node_id] = {"class_type": node_type, "inputs": {"ckpt_name": widgets[0]}}
        elif node_type == "EmptyLatentImage":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"width": widgets[0], "height": widgets[1], "batch_size": widgets[2]},
            }
        elif node_type == "CLIPTextEncode":
            clip_input = node["inputs"][0]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"text": widgets[0], "clip": input_ref(link_map, clip_input["link"])},
            }
        elif node_type == "KSampler":
            model_link = next(inp for inp in node["inputs"] if inp["name"] == "model")["link"]
            pos_link = next(inp for inp in node["inputs"] if inp["name"] == "positive")["link"]
            neg_link = next(inp for inp in node["inputs"] if inp["name"] == "negative")["link"]
            latent_link = next(inp for inp in node["inputs"] if inp["name"] == "latent_image")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "seed": widgets[0],
                    "steps": widgets[2],
                    "cfg": widgets[3],
                    "sampler_name": widgets[4],
                    "scheduler": widgets[5],
                    "denoise": widgets[6],
                    "model": input_ref(link_map, model_link),
                    "positive": input_ref(link_map, pos_link),
                    "negative": input_ref(link_map, neg_link),
                    "latent_image": input_ref(link_map, latent_link),
                },
            }
        elif node_type == "LoadImage":
            image_name = widgets[0] if widgets else ""
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "image": image_name,
                    "upload": "image",
                },
            }
        elif node_type == "VAEEncode":
            pixels_link = next(inp for inp in node["inputs"] if inp["name"] == "pixels")["link"]
            vae_link = next(inp for inp in node["inputs"] if inp["name"] == "vae")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "pixels": input_ref(link_map, pixels_link),
                    "vae": input_ref(link_map, vae_link),
                },
            }
        elif node_type == "VAEDecode":
            samples_link = next(inp for inp in node["inputs"] if inp["name"] == "samples")["link"]
            vae_link = next(inp for inp in node["inputs"] if inp["name"] == "vae")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "samples": input_ref(link_map, samples_link),
                    "vae": input_ref(link_map, vae_link),
                },
            }
        elif node_type == "SaveImage":
            image_link = next(inp for inp in node["inputs"] if inp["name"] == "images")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "filename_prefix": widgets[0],
                    "images": input_ref(link_map, image_link),
                },
            }
        else:
            raise WorkflowError(f"Unsupported node type in locked workflow: {node_type}")

    return api_prompt


def apply_overrides(workflow: dict[str, Any], overrides: dict[str, Any]) -> None:
    positive_node, negative_node = resolve_prompt_nodes(workflow)
    latent_nodes = find_nodes_by_type(workflow, "EmptyLatentImage")
    ksampler_node = find_nodes_by_type(workflow, "KSampler")[0]
    save_node = find_nodes_by_type(workflow, "SaveImage")[0]
    load_image_nodes = find_nodes_by_type(workflow, "LoadImage")

    merged_positive_prompt = overrides.get("positive_prompt")
    if not merged_positive_prompt and "positive_prompt_sections" in overrides:
        merged_positive_prompt = merge_positive_prompt_sections(overrides.get("positive_prompt_sections"))
    if merged_positive_prompt:
        positive_node["widgets_values"][0] = merged_positive_prompt
    if "negative_prompt" in overrides:
        negative_node["widgets_values"][0] = overrides["negative_prompt"]
    if latent_nodes:
        latent_node = latent_nodes[0]
        if "width" in overrides:
            latent_node["widgets_values"][0] = overrides["width"]
        if "height" in overrides:
            latent_node["widgets_values"][1] = overrides["height"]
        if "batch_size" in overrides:
            latent_node["widgets_values"][2] = overrides["batch_size"]

    k_map = {
        "seed": 0,
        "control_after_generate": 1,
        "steps": 2,
        "cfg": 3,
        "sampler": 4,
        "scheduler": 5,
        "denoise": 6,
    }
    for key, idx in k_map.items():
        if key in overrides:
            value = overrides[key]
            if key == "seed" and (value is None or value == ""):
                value = random_seed()
            ksampler_node["widgets_values"][idx] = value

    if "filename_prefix" in overrides:
        save_node["widgets_values"][0] = overrides["filename_prefix"]
    if "reference_image" in overrides and load_image_nodes:
        load_image_nodes[0]["widgets_values"][0] = overrides["reference_image"]


def wait_for_history(prompt_id: str, timeout_s: int) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    url = f"{COMFYUI_URL.rstrip('/')}/history/{prompt_id}"
    while time.time() < deadline:
        try:
            history = api_get(url)
            if history:
                return history
        except error.HTTPError as exc:
            if exc.code != 404:
                raise
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def build_status(prompt_id: str) -> dict[str, Any]:
    history_url = f"{COMFYUI_URL.rstrip('/')}/history/{prompt_id}"
    queue_url = f"{COMFYUI_URL.rstrip('/')}/queue"

    try:
        history = api_get(history_url)
        if history:
            return {
                "ok": True,
                "prompt_id": prompt_id,
                "status": "completed",
                "history": history,
            }
    except error.HTTPError as exc:
        if exc.code != 404:
            raise

    queue = api_get(queue_url)
    for item in queue.get("queue_running", []):
        if len(item) > 1 and item[1] == prompt_id:
            return {
                "ok": True,
                "prompt_id": prompt_id,
                "status": "running",
                "queue_item": item,
            }

    for item in queue.get("queue_pending", []):
        if len(item) > 1 and item[1] == prompt_id:
            return {
                "ok": True,
                "prompt_id": prompt_id,
                "status": "pending",
                "queue_item": item,
            }

    return {
        "ok": True,
        "prompt_id": prompt_id,
        "status": "unknown",
    }


def backfill_runs_from_queue() -> None:
    queue = api_get(f"{COMFYUI_URL.rstrip('/')}/queue")
    for status, key in (("running", "queue_running"), ("pending", "queue_pending")):
        for item in queue.get(key, []):
            if len(item) < 2:
                continue
            prompt_id = item[1]
            prompt_payload = item[2] if len(item) > 2 and isinstance(item[2], dict) else None
            client_id = ""
            if len(item) > 3 and isinstance(item[3], dict):
                client_id = str(item[3].get("client_id", ""))
            upsert_discovered_run(
                prompt_id=prompt_id,
                status=status,
                prompt_payload=prompt_payload,
                client_id=client_id,
                workflow_name=infer_workflow_name_from_prompt(prompt_payload),
            )


def backfill_runs_from_history(limit: int = 200) -> None:
    history = api_get(f"{COMFYUI_URL.rstrip('/')}/history")
    if not isinstance(history, dict):
        return

    count = 0
    for prompt_id, record in history.items():
        if count >= limit:
            break
        if not isinstance(record, dict):
            continue

        prompt_payload = record.get("prompt")
        client_id = ""
        prompt_meta = record.get("prompt")
        if isinstance(prompt_meta, list) and len(prompt_meta) >= 2:
            prompt_id = str(prompt_meta[1])
            if len(prompt_meta) >= 4 and isinstance(prompt_meta[3], dict):
                client_id = str(prompt_meta[3].get("client_id", ""))
            prompt_payload = prompt_meta[2] if len(prompt_meta) >= 3 and isinstance(prompt_meta[2], dict) else None

        upsert_discovered_run(
            prompt_id=prompt_id,
            status="completed",
            prompt_payload=prompt_payload if isinstance(prompt_payload, dict) else None,
            client_id=client_id,
            workflow_name=infer_workflow_name_from_prompt(prompt_payload if isinstance(prompt_payload, dict) else None),
        )
        update_run_record(prompt_id, status="completed", history={prompt_id: record})
        count += 1


def sync_run_status(prompt_id: str) -> dict[str, Any]:
    status = build_status(prompt_id)
    history = status.get("history") if status.get("status") == "completed" else None
    update_run_record(prompt_id, status=status["status"], history=history)
    return status


def sync_nonterminal_runs() -> None:
    for prompt_id in list_nonterminal_prompt_ids():
        try:
            sync_run_status(prompt_id)
        except Exception:
            continue


def active_runs_payload(*, limit: int = 100, offset: int = 0, query: str = "") -> dict[str, Any]:
    backfill_runs_from_queue()
    sync_nonterminal_runs()
    runs, total = list_runs_by_status(
        ["submitted", "pending", "running", "unknown"],
        limit=limit,
        offset=offset,
        query=query,
    )
    return {
        "ok": True,
        "runs": [summarize_run(run) for run in runs],
        "total": total,
        "comfyui_browser_url": COMFYUI_BROWSER_URL,
    }


def completed_runs_payload(*, limit: int = 50, offset: int = 0, query: str = "") -> dict[str, Any]:
    backfill_runs_from_history()
    sync_nonterminal_runs()
    runs, total = list_runs_by_status(["completed"], limit=limit, offset=offset, query=query)
    return {"ok": True, "runs": [summarize_run(run, include_outputs=True) for run in runs], "total": total}


class Handler(BaseHTTPRequestHandler):
    server_version = "ComfyUIGateway/0.2"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        if not API_TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        expected = f"Bearer {API_TOKEN}"
        return header == expected

    def _require_auth(self) -> bool:
        if self._auth_ok():
            return True
        self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
        return False

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parsed_url(self) -> parse.SplitResult:
        return parse.urlsplit(self.path)

    def _query_params(self) -> dict[str, list[str]]:
        return parse.parse_qs(self._parsed_url().query)

    def _query_int(self, name: str, default: int, minimum: int = 0, maximum: int = 500) -> int:
        raw = self._query_params().get(name, [str(default)])[0]
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(minimum, min(maximum, value))

    def _query_str(self, name: str, default: str = "") -> str:
        return self._query_params().get(name, [default])[0].strip()

    def do_GET(self) -> None:  # noqa: N802
        parsed = self._parsed_url()
        path = parsed.path

        if path in ("/", "/dashboard"):
            if not DASHBOARD_PATH.exists():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "dashboard not found"})
                return
            self._send_bytes(HTTPStatus.OK, DASHBOARD_PATH.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/healthz":
            try:
                queue = api_get(f"{COMFYUI_URL.rstrip('/')}/queue")
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "comfyui": "reachable",
                        "queue": queue,
                        "comfyui_browser_url": COMFYUI_BROWSER_URL,
                    },
                )
            except Exception as exc:  # pragma: no cover - best effort health endpoint
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if not self._require_auth():
            return

        if path == "/workflows":
            try:
                self._send_json(HTTPStatus.OK, {"ok": True, "workflows": list_workflow_summaries()})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path == "/queue":
            try:
                queue = api_get(f"{COMFYUI_URL.rstrip('/')}/queue")
                self._send_json(HTTPStatus.OK, {"ok": True, "queue": queue})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path == "/runs/active":
            try:
                self._send_json(
                    HTTPStatus.OK,
                    active_runs_payload(
                        limit=self._query_int("limit", 100),
                        offset=self._query_int("offset", 0),
                        query=self._query_str("q"),
                    ),
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path == "/runs/completed":
            try:
                self._send_json(
                    HTTPStatus.OK,
                    completed_runs_payload(
                        limit=self._query_int("limit", 24),
                        offset=self._query_int("offset", 0),
                        query=self._query_str("q"),
                    ),
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path.startswith("/runs/"):
            prompt_id = path.removeprefix("/runs/").strip()
            if prompt_id and "/" not in prompt_id and prompt_id not in {"active", "completed"}:
                run = get_run(prompt_id)
                if not run:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "run not found"})
                    return
                self._send_json(HTTPStatus.OK, {"ok": True, "run": detail_run(run)})
                return

        if path.startswith("/history/"):
            prompt_id = path.removeprefix("/history/").strip()
            if not prompt_id:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing prompt_id"})
                return
            try:
                history = api_get(f"{COMFYUI_URL.rstrip('/')}/history/{prompt_id}")
                update_run_record(prompt_id, status="completed", history=history)
                self._send_json(HTTPStatus.OK, {"ok": True, "prompt_id": prompt_id, "history": history})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path.startswith("/status/"):
            prompt_id = path.removeprefix("/status/").strip()
            if not prompt_id:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing prompt_id"})
                return
            try:
                self._send_json(HTTPStatus.OK, sync_run_status(prompt_id))
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if path.startswith("/download/"):
            parts = path.split("/")
            if len(parts) != 4:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid download path"})
                return
            _, _, prompt_id, output_index_raw = parts
            try:
                output_index = int(output_index_raw)
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid output index"})
                return

            run = get_run(prompt_id)
            outputs = run.get("outputs", []) if run else []
            if output_index < 0 or output_index >= len(outputs):
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "output not found"})
                return

            output = outputs[output_index]
            file_path = resolve_output_path(output)
            if not file_path.exists() or COMFYUI_OUTPUT_DIR.resolve() not in file_path.parents:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "file not found"})
                return

            try:
                body = file_path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.send_header(
                    "Content-Disposition",
                    f"attachment; filename={parse.quote(file_path.name)}",
                )
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._require_auth():
            return

        if self.path == "/upload/reference-url":
            raw_length = self.headers.get("Content-Length", "0")
            length = int(raw_length)
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8") or "{}")
            source_url = str(payload.get("url", "")).strip()
            if not source_url:
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing url"})
                return
            try:
                saved_name = save_reference_image_from_url(source_url)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "filename": saved_name,
                        "input_dir": str(COMFYUI_INPUT_DIR),
                        "source_url": source_url,
                    },
                )
            except WorkflowError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if self.path == "/upload/reference-image":
            raw_length = self.headers.get("Content-Length", "0")
            length = int(raw_length)
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8") or "{}")
            filename = str(payload.get("filename", "")).strip()
            content_b64 = str(payload.get("content_base64", "")).strip()
            if not filename or not content_b64:
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing filename or content_base64"})
                return
            try:
                saved_name = save_reference_image(filename, content_b64)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "filename": saved_name,
                        "input_dir": str(COMFYUI_INPUT_DIR),
                    },
                )
            except WorkflowError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        if self.path != "/generate":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        raw_length = self.headers.get("Content-Length", "0")
        length = int(raw_length)
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8") or "{}")

        workflow_name = payload.get("workflow", DEFAULT_WORKFLOW.name)
        workflow_path = WORKFLOW_DIR / workflow_name
        if not workflow_path.exists():
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"workflow not found: {workflow_name}"})
            return

        overrides = payload.get("overrides", {})
        wait = bool(payload.get("wait", False))
        timeout_s = int(payload.get("timeout_s", 1800))

        try:
            workflow = load_json(workflow_path)
            apply_overrides(workflow, overrides)
            prompt = ui_workflow_to_api_prompt(workflow)
            client_id = str(uuid.uuid4())
            response = api_post(
                f"{COMFYUI_URL.rstrip('/')}/prompt",
                {"prompt": prompt, "client_id": client_id},
            )
            prompt_id = response.get("prompt_id")
            if not prompt_id:
                raise RuntimeError("ComfyUI did not return a prompt_id")
            raw_request = {"prompt": prompt, "client_id": client_id}
            record_run_submission(
                prompt_id=prompt_id,
                workflow_name=workflow_name,
                client_id=client_id,
                overrides=overrides,
                raw_request=raw_request,
                raw_response=response,
            )
            result: dict[str, Any] = {
                "ok": True,
                "workflow": workflow_name,
                "client_id": client_id,
                "prompt_id": prompt_id,
                "status": "submitted",
            }
            if wait and result["prompt_id"]:
                history = wait_for_history(result["prompt_id"], timeout_s)
                update_run_record(result["prompt_id"], status="completed", history=history)
                result["status"] = "completed"
                result["history"] = history
            self._send_json(HTTPStatus.OK, result)
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._require_auth():
            return

        parsed = self._parsed_url()
        path = parsed.path

        if path.startswith("/runs/"):
            prompt_id = path.removeprefix("/runs/").strip()
            if not prompt_id or "/" in prompt_id or prompt_id in {"active", "completed"}:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid prompt_id"})
                return
            try:
                self._send_json(HTTPStatus.OK, delete_run_and_outputs(prompt_id))
            except WorkflowError as exc:
                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})


def main() -> None:
    if not WORKFLOW_DIR.exists():
        raise SystemExit(f"workflow directory not found: {WORKFLOW_DIR}")
    if not DASHBOARD_PATH.exists():
        raise SystemExit(f"dashboard not found: {DASHBOARD_PATH}")
    ensure_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"ComfyUI gateway listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
