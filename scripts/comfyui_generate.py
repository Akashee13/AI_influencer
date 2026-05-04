#!/usr/bin/env python3
"""Submit locked ComfyUI workflows with lightweight overrides.

This script is intentionally scoped to the team's current simple workflow:
- CheckpointLoaderSimple
- 2x CLIPTextEncode (positive + negative)
- EmptyLatentImage
- KSampler
- VAEDecode
- SaveImage

It loads the UI-exported workflow JSON, converts it into the API prompt format
ComfyUI expects, applies optional prompt/settings overrides, and submits the
job to a running ComfyUI server.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "comfyui" / "workflows" / "mumbai-yoga-anchor-v1.json"


class WorkflowError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def api_get(url: str) -> Any:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post(url: str, payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_link_map(workflow: dict[str, Any]) -> dict[int, tuple[int, int, int, int, str]]:
    # ComfyUI links are stored as arrays:
    # [link_id, from_node, from_slot, to_node, to_slot, type]
    link_map: dict[int, tuple[int, int, int, int, str]] = {}
    for raw in workflow.get("links", []):
        link_id, from_node, from_slot, to_node, to_slot, value_type = raw
        link_map[link_id] = (from_node, from_slot, to_node, to_slot, value_type)
    return link_map


def find_nodes_by_type(workflow: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [node for node in workflow.get("nodes", []) if node.get("type") == node_type]


def get_widget_values(node: dict[str, Any]) -> list[Any]:
    return list(node.get("widgets_values", []))


def input_ref(link_map: dict[int, tuple[int, int, int, int, str]], link_id: int, output_name: str) -> list[Any]:
    from_node, *_rest = link_map[link_id]
    return [str(from_node), output_name]


def ui_workflow_to_api_prompt(workflow: dict[str, Any]) -> dict[str, Any]:
    link_map = build_link_map(workflow)
    api_prompt: dict[str, Any] = {}

    for node in workflow.get("nodes", []):
        node_id = str(node["id"])
        node_type = node["type"]
        widgets = get_widget_values(node)

        if node_type == "CheckpointLoaderSimple":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"ckpt_name": widgets[0]},
            }
        elif node_type == "EmptyLatentImage":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "width": widgets[0],
                    "height": widgets[1],
                    "batch_size": widgets[2],
                },
            }
        elif node_type == "CLIPTextEncode":
            clip_input = node["inputs"][0]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "text": widgets[0],
                    "clip": input_ref(link_map, clip_input["link"], "CLIP"),
                },
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


def apply_overrides(
    workflow: dict[str, Any],
    *,
    positive_prompt: str | None,
    negative_prompt: str | None,
    width: int | None,
    height: int | None,
    steps: int | None,
    cfg: float | None,
    sampler: str | None,
    scheduler: str | None,
    seed: int | None,
    control_after_generate: str | None,
    filename_prefix: str | None,
) -> None:
    pos_nodes = find_nodes_by_type(workflow, "CLIPTextEncode")
    if len(pos_nodes) != 2:
        raise WorkflowError("Expected exactly two CLIPTextEncode nodes in the locked workflow.")

    latent_node = find_nodes_by_type(workflow, "EmptyLatentImage")[0]
    ksampler_node = find_nodes_by_type(workflow, "KSampler")[0]
    save_node = find_nodes_by_type(workflow, "SaveImage")[0]

    if positive_prompt is not None:
        pos_nodes[0]["widgets_values"][0] = positive_prompt
    if negative_prompt is not None:
        pos_nodes[1]["widgets_values"][0] = negative_prompt

    if width is not None:
        latent_node["widgets_values"][0] = width
    if height is not None:
        latent_node["widgets_values"][1] = height

    if seed is not None:
        ksampler_node["widgets_values"][0] = seed
    if control_after_generate is not None:
        ksampler_node["widgets_values"][1] = control_after_generate
    if steps is not None:
        ksampler_node["widgets_values"][2] = steps
    if cfg is not None:
        ksampler_node["widgets_values"][3] = cfg
    if sampler is not None:
        ksampler_node["widgets_values"][4] = sampler
    if scheduler is not None:
        ksampler_node["widgets_values"][5] = scheduler

    if filename_prefix is not None:
        save_node["widgets_values"][0] = filename_prefix


def wait_for_history(base_url: str, prompt_id: str, timeout_s: int = 1800) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    history_url = f"{base_url.rstrip('/')}/history/{prompt_id}"
    while time.time() < deadline:
        try:
            history = api_get(history_url)
            if history:
                return history
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit locked ComfyUI workflow runs by API.")
    parser.add_argument("--workflow", default=str(DEFAULT_WORKFLOW), help="Path to locked UI-exported workflow JSON")
    parser.add_argument("--server", default="http://127.0.0.1:8188", help="ComfyUI base URL")
    parser.add_argument("--positive-prompt", help="Override positive prompt")
    parser.add_argument("--negative-prompt", help="Override negative prompt")
    parser.add_argument("--width", type=int, help="Override width")
    parser.add_argument("--height", type=int, help="Override height")
    parser.add_argument("--steps", type=int, help="Override sampler steps")
    parser.add_argument("--cfg", type=float, help="Override CFG")
    parser.add_argument("--sampler", help="Override sampler name")
    parser.add_argument("--scheduler", help="Override scheduler name")
    parser.add_argument("--seed", type=int, help="Override seed")
    parser.add_argument(
        "--control-after-generate",
        choices=["fixed", "randomize", "increment", "decrement"],
        help="Update the locked workflow metadata; not forwarded to the ComfyUI API payload",
    )
    parser.add_argument("--filename-prefix", default="mumbai-yoga", help="Saved filename prefix")
    parser.add_argument("--wait", action="store_true", help="Wait for completion and print history summary")
    parser.add_argument("--save-request", help="Optional path to save the resolved API prompt payload")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workflow_path = Path(args.workflow)
    workflow = load_json(workflow_path)
    apply_overrides(
        workflow,
        positive_prompt=args.positive_prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg=args.cfg,
        sampler=args.sampler,
        scheduler=args.scheduler,
        seed=args.seed,
        control_after_generate=args.control_after_generate,
        filename_prefix=args.filename_prefix,
    )
    api_prompt = ui_workflow_to_api_prompt(workflow)

    if args.save_request:
        Path(args.save_request).write_text(json.dumps(api_prompt, indent=2))

    client_id = str(uuid.uuid4())
    response = api_post(
        f"{args.server.rstrip('/')}/prompt",
        {"prompt": api_prompt, "client_id": client_id},
    )

    prompt_id = response.get("prompt_id")
    print(json.dumps({"prompt_id": prompt_id, "client_id": client_id}, indent=2))

    if args.wait and prompt_id:
        history = wait_for_history(args.server, prompt_id)
        print(json.dumps(history, indent=2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except urllib.error.URLError as exc:
        print(f"network error: {exc}", file=sys.stderr)
        raise SystemExit(3)
