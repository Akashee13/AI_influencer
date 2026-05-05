#!/usr/bin/env python3
"""Submit locked ComfyUI workflows with lightweight overrides.

This script supports both the original simple checkpoint workflows and the
newer FLUX-native face-ID workflows used by the team.
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
WORKFLOW_BINDINGS_PATH = ROOT / "comfyui" / "workflow_bindings.json"
COMFYUI_INPUT_DIR = Path(
    Path.home() / "comfy" / "input"
)


class WorkflowError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_workflow_bindings() -> dict[str, Any]:
    if not WORKFLOW_BINDINGS_PATH.exists():
        return {}
    try:
        data = load_json(WORKFLOW_BINDINGS_PATH)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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


def node_map(workflow: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in workflow.get("nodes", [])}


def get_widget_values(node: dict[str, Any]) -> list[Any]:
    return list(node.get("widgets_values", []))


def input_ref(link_map: dict[int, tuple[int, int, int, int, str]], link_id: int) -> list[Any]:
    from_node, from_slot, *_rest = link_map[link_id]
    return [str(from_node), from_slot]


def workflow_extra(workflow: dict[str, Any]) -> dict[str, Any]:
    extra = workflow.get("extra", {})
    return extra if isinstance(extra, dict) else {}


def workflow_name(workflow: dict[str, Any]) -> str:
    extra = workflow_extra(workflow)
    name = extra.get("workflow_name", "")
    return str(name).strip() if name else ""


def workflow_binding_for(workflow: dict[str, Any]) -> dict[str, Any]:
    bindings = load_workflow_bindings()
    name = workflow_name(workflow)
    value = bindings.get(name, {})
    return value if isinstance(value, dict) else {}


def workflow_input_roles(workflow: dict[str, Any]) -> dict[str, list[int]]:
    raw_roles = workflow_extra(workflow).get("input_roles", {})
    if not isinstance(raw_roles, dict):
        return {}
    roles: dict[str, list[int]] = {}
    for key, value in raw_roles.items():
        if isinstance(value, int):
            roles[str(key)] = [value]
        elif isinstance(value, list):
            resolved = [int(item) for item in value if isinstance(item, int)]
            if resolved:
                roles[str(key)] = resolved
    return roles


def workflow_anchor_face_image(workflow: dict[str, Any]) -> str:
    binding = workflow_binding_for(workflow)
    if binding.get("anchor_face_image"):
        return str(binding.get("anchor_face_image")).strip()
    value = workflow_extra(workflow).get("anchor_face_image", "")
    return str(value).strip() if value else ""


def workflow_anchor_face_source(workflow: dict[str, Any]) -> str:
    binding = workflow_binding_for(workflow)
    if binding.get("anchor_face_source"):
        return str(binding.get("anchor_face_source")).strip()
    value = workflow_extra(workflow).get("anchor_face_source", "")
    return str(value).strip() if value else ""


def ensure_input_asset(target_filename: str, source_relative_path: str) -> str:
    source_path = (ROOT / source_relative_path).resolve()
    if not source_path.exists() or not source_path.is_file():
        raise WorkflowError(f"workflow anchor face source not found: {source_path}")
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = COMFYUI_INPUT_DIR / target_filename
    if not destination.exists() or source_path.stat().st_mtime > destination.stat().st_mtime:
        destination.write_bytes(source_path.read_bytes())
    return target_filename


def resolve_prompt_nodes(workflow: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ksampler_nodes = find_nodes_by_type(workflow, "KSampler")
    link_map = build_link_map(workflow)
    nodes = node_map(workflow)
    if ksampler_nodes:
        ksampler_node = ksampler_nodes[0]
        pos_link = next(inp for inp in ksampler_node["inputs"] if inp["name"] == "positive")["link"]
        neg_link = next(inp for inp in ksampler_node["inputs"] if inp["name"] == "negative")["link"]
        return nodes[int(link_map[pos_link][0])], nodes[int(link_map[neg_link][0])]

    guider_nodes = find_nodes_by_type(workflow, "BasicGuider")
    if guider_nodes:
        guider_node = guider_nodes[0]
        conditioning_link = next(inp for inp in guider_node["inputs"] if inp["name"] == "conditioning")["link"]
        positive_node = nodes[int(link_map[conditioning_link][0])]
        if positive_node.get("type") == "FluxGuidance":
            guidance_link = next(inp for inp in positive_node["inputs"] if inp["name"] == "conditioning")["link"]
            positive_node = nodes[int(link_map[guidance_link][0])]
        return positive_node, {"widgets_values": [""]}

    raise WorkflowError("Could not resolve prompt nodes for locked workflow.")


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
        elif node_type == "EmptySD3LatentImage":
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
                    "clip": input_ref(link_map, clip_input["link"]),
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
                    "model": input_ref(link_map, model_link),
                    "positive": input_ref(link_map, pos_link),
                    "negative": input_ref(link_map, neg_link),
                    "latent_image": input_ref(link_map, latent_link),
                },
            }
        elif node_type == "RandomNoise":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"noise_seed": widgets[0]},
            }
        elif node_type == "FluxGuidance":
            conditioning_link = next(inp for inp in node["inputs"] if inp["name"] == "conditioning")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "conditioning": input_ref(link_map, conditioning_link),
                    "guidance": widgets[0],
                },
            }
        elif node_type == "KSamplerSelect":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"sampler_name": widgets[0]},
            }
        elif node_type == "BasicScheduler":
            model_link = next(inp for inp in node["inputs"] if inp["name"] == "model")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "model": input_ref(link_map, model_link),
                    "scheduler": widgets[0],
                    "steps": widgets[1],
                    "denoise": widgets[2],
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
        elif node_type == "LoadImage":
            image_name = widgets[0] if widgets else ""
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"image": image_name, "upload": "image"},
            }
        elif node_type == "PulidFluxInsightFaceLoader":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"provider": widgets[0]},
            }
        elif node_type == "PulidFluxEvaClipLoader":
            api_prompt[node_id] = {"class_type": node_type, "inputs": {}}
        elif node_type == "PulidFluxModelLoader":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"pulid_file": widgets[0]},
            }
        elif node_type == "ApplyPulidFlux":
            inputs: dict[str, Any] = {
                "weight": widgets[0],
                "start_at": widgets[1],
                "end_at": widgets[2],
            }
            for input_name in ("model", "pulid_flux", "eva_clip", "face_analysis", "image", "attn_mask"):
                link = next((inp["link"] for inp in node["inputs"] if inp["name"] == input_name), None)
                if link is not None:
                    inputs[input_name] = input_ref(link_map, link)
            api_prompt[node_id] = {"class_type": node_type, "inputs": inputs}
        elif node_type == "BasicGuider":
            model_link = next(inp for inp in node["inputs"] if inp["name"] == "model")["link"]
            conditioning_link = next(inp for inp in node["inputs"] if inp["name"] == "conditioning")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "model": input_ref(link_map, model_link),
                    "conditioning": input_ref(link_map, conditioning_link),
                },
            }
        elif node_type == "SamplerCustomAdvanced":
            inputs: dict[str, Any] = {}
            for input_name in ("noise", "guider", "sampler", "sigmas", "latent_image"):
                link = next(inp["link"] for inp in node["inputs"] if inp["name"] == input_name)
                inputs[input_name] = input_ref(link_map, link)
            api_prompt[node_id] = {"class_type": node_type, "inputs": inputs}
        elif node_type == "UNETLoader":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"unet_name": widgets[0], "weight_dtype": widgets[1]},
            }
        elif node_type == "VAELoader":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"vae_name": widgets[0]},
            }
        elif node_type == "DualCLIPLoader":
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {
                    "clip_name1": widgets[0],
                    "clip_name2": widgets[1],
                    "type": widgets[2],
                },
            }
        elif node_type == "PreviewImage":
            image_link = next(inp for inp in node["inputs"] if inp["name"] == "images")["link"]
            api_prompt[node_id] = {
                "class_type": node_type,
                "inputs": {"images": input_ref(link_map, image_link)},
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
    face_reference_image: str | None,
    scene_reference_image: str | None,
) -> None:
    positive_node, negative_node = resolve_prompt_nodes(workflow)
    latent_nodes = find_nodes_by_type(workflow, "EmptyLatentImage") or find_nodes_by_type(workflow, "EmptySD3LatentImage")
    ksampler_nodes = find_nodes_by_type(workflow, "KSampler")
    random_noise_nodes = find_nodes_by_type(workflow, "RandomNoise")
    scheduler_nodes = find_nodes_by_type(workflow, "BasicScheduler")
    flux_guidance_nodes = find_nodes_by_type(workflow, "FluxGuidance")
    save_nodes = find_nodes_by_type(workflow, "SaveImage")
    load_image_nodes = find_nodes_by_type(workflow, "LoadImage")
    nodes_by_id = node_map(workflow)
    input_roles = workflow_input_roles(workflow)
    locked_anchor_face_image = workflow_anchor_face_image(workflow)
    locked_anchor_face_source = workflow_anchor_face_source(workflow)

    if positive_prompt is not None:
        positive_node["widgets_values"][0] = positive_prompt
    if negative_prompt is not None and negative_node.get("widgets_values"):
        negative_node["widgets_values"][0] = negative_prompt

    if latent_nodes:
        latent_node = latent_nodes[0]
        if width is not None:
            latent_node["widgets_values"][0] = width
        if height is not None:
            latent_node["widgets_values"][1] = height

    if ksampler_nodes:
        ksampler_node = ksampler_nodes[0]
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

    if random_noise_nodes:
        random_noise_node = random_noise_nodes[0]
        if seed is not None:
            random_noise_node["widgets_values"][0] = seed
        if control_after_generate is not None:
            random_noise_node["widgets_values"][1] = control_after_generate

    if scheduler_nodes:
        scheduler_node = scheduler_nodes[0]
        if scheduler is not None:
            scheduler_node["widgets_values"][0] = scheduler
        if steps is not None:
            scheduler_node["widgets_values"][1] = steps

    if flux_guidance_nodes and cfg is not None:
        flux_guidance_nodes[0]["widgets_values"][0] = cfg

    if save_nodes and filename_prefix is not None:
        save_nodes[0]["widgets_values"][0] = filename_prefix

    def assign_load_image(role_key: str, filename: str | None) -> bool:
        if not filename:
            return False
        node_ids = input_roles.get(role_key, [])
        if not node_ids and role_key == "scene_reference_image" and load_image_nodes:
            load_image_nodes[0]["widgets_values"][0] = filename
            return True
        assigned = False
        for node_id in node_ids:
            node = nodes_by_id.get(int(node_id))
            if node and node.get("type") == "LoadImage":
                node["widgets_values"][0] = filename
                assigned = True
        return assigned

    if locked_anchor_face_image:
        if locked_anchor_face_source:
            ensure_input_asset(locked_anchor_face_image, locked_anchor_face_source)
        assign_load_image("face_reference_image", locked_anchor_face_image)
    else:
        assign_load_image("face_reference_image", face_reference_image)
    assign_load_image("scene_reference_image", scene_reference_image)


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
    parser.add_argument("--face-reference-image", help="Filename already present in ComfyUI input for face identity workflows")
    parser.add_argument("--scene-reference-image", help="Filename already present in ComfyUI input for scene-guided workflows")
    parser.add_argument("--wait", action="store_true", help="Wait for completion and print history summary")
    parser.add_argument("--save-request", help="Optional path to save the resolved API prompt payload")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workflow_path = Path(args.workflow)
    workflow = load_json(workflow_path)
    workflow.setdefault("extra", {})
    if isinstance(workflow["extra"], dict):
        workflow["extra"]["workflow_name"] = workflow_path.name
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
        face_reference_image=args.face_reference_image,
        scene_reference_image=args.scene_reference_image,
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
