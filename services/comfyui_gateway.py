#!/usr/bin/env python3
"""Small authenticated gateway for a ComfyUI instance running on the same VM.

This service exposes a minimal HTTP API that:
- accepts generation requests from your local project
- loads a locked ComfyUI workflow JSON
- applies prompt/setting overrides
- submits to local ComfyUI on 127.0.0.1:8188
- optionally waits for completion

It is intentionally stdlib-only so deployment on the VM stays simple.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "comfyui" / "workflows" / "mumbai-yoga-anchor-v1.json"
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
WORKFLOW_DIR = Path(os.environ.get("WORKFLOW_DIR", str(DEFAULT_WORKFLOW.parent)))
API_TOKEN = os.environ.get("COMFYUI_GATEWAY_TOKEN", "")
HOST = os.environ.get("COMFYUI_GATEWAY_HOST", "0.0.0.0")
PORT = int(os.environ.get("COMFYUI_GATEWAY_PORT", "9000"))


class WorkflowError(RuntimeError):
    pass


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


def build_link_map(workflow: dict[str, Any]) -> dict[int, tuple[int, int, int, int, str]]:
    link_map: dict[int, tuple[int, int, int, int, str]] = {}
    for raw in workflow.get("links", []):
        link_id, from_node, from_slot, to_node, to_slot, value_type = raw
        link_map[link_id] = (from_node, from_slot, to_node, to_slot, value_type)
    return link_map


def find_nodes_by_type(workflow: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [node for node in workflow.get("nodes", []) if node.get("type") == node_type]


def input_ref(link_map: dict[int, tuple[int, int, int, int, str]], link_id: int, output_name: str) -> list[Any]:
    from_node, *_rest = link_map[link_id]
    return [str(from_node), output_name]


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
                "inputs": {"text": widgets[0], "clip": input_ref(link_map, clip_input["link"], "CLIP")},
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
                    "model": input_ref(link_map, model_link, "MODEL"),
                    "positive": input_ref(link_map, pos_link, "CONDITIONING"),
                    "negative": input_ref(link_map, neg_link, "CONDITIONING"),
                    "latent_image": input_ref(link_map, latent_link, "LATENT"),
                },
            }
        elif node_type == "VAEDecode":
            samples_link = next(inp for inp in node["inputs"] if inp["name"] == "samples")["link"]
            vae_link = next(inp for inp in node["inputs"] if inp["name"] == "vae")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "samples": input_ref(link_map, samples_link, "LATENT"),
                    "vae": input_ref(link_map, vae_link, "VAE"),
                },
            }
        elif node_type == "SaveImage":
            image_link = next(inp for inp in node["inputs"] if inp["name"] == "images")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "filename_prefix": widgets[0],
                    "images": input_ref(link_map, image_link, "IMAGE"),
                },
            }
        else:
            raise WorkflowError(f"Unsupported node type in locked workflow: {node_type}")

    return api_prompt


def apply_overrides(workflow: dict[str, Any], overrides: dict[str, Any]) -> None:
    prompt_nodes = find_nodes_by_type(workflow, "CLIPTextEncode")
    if len(prompt_nodes) != 2:
        raise WorkflowError("Expected exactly two CLIPTextEncode nodes")

    latent_node = find_nodes_by_type(workflow, "EmptyLatentImage")[0]
    ksampler_node = find_nodes_by_type(workflow, "KSampler")[0]
    save_node = find_nodes_by_type(workflow, "SaveImage")[0]

    if "positive_prompt" in overrides:
        prompt_nodes[0]["widgets_values"][0] = overrides["positive_prompt"]
    if "negative_prompt" in overrides:
        prompt_nodes[1]["widgets_values"][0] = overrides["negative_prompt"]
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
            ksampler_node["widgets_values"][idx] = overrides[key]

    if "filename_prefix" in overrides:
        save_node["widgets_values"][0] = overrides["filename_prefix"]


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


class Handler(BaseHTTPRequestHandler):
    server_version = "ComfyUIGateway/0.1"

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

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            try:
                queue = api_get(f"{COMFYUI_URL.rstrip('/')}/queue")
                self._send_json(HTTPStatus.OK, {"ok": True, "comfyui": "reachable", "queue": queue})
            except Exception as exc:  # pragma: no cover - best effort health endpoint
                self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth_ok():
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
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
            result: dict[str, Any] = {
                "ok": True,
                "workflow": workflow_name,
                "client_id": client_id,
                "prompt_id": response.get("prompt_id"),
            }
            if wait and result["prompt_id"]:
                result["history"] = wait_for_history(result["prompt_id"], timeout_s)
            self._send_json(HTTPStatus.OK, result)
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})


def main() -> None:
    if not WORKFLOW_DIR.exists():
        raise SystemExit(f"workflow directory not found: {WORKFLOW_DIR}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"ComfyUI gateway listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
