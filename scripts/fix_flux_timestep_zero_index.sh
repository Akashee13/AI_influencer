#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
COMFY_ROOT="${COMFY_ROOT:-$TARGET_HOME/comfy}"
COMFY_APP_DIR=""
CUSTOM_NODES_DIR="$COMFY_ROOT/custom_nodes"
PULID_NODE_DIR="$CUSTOM_NODES_DIR/ComfyUI-PuLID-Flux"
PATCH_DIR="$CUSTOM_NODES_DIR/ai_influencer_runtime_compat"
PATCH_FILE="$PATCH_DIR/__init__.py"
CAN_SUDO=0
PYTHON_BIN="python3"

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_as_user() {
  if [[ "$(id -un)" == "$TARGET_USER" ]]; then
    bash -lc "$*"
    return
  fi

  if [[ "$CAN_SUDO" -eq 1 ]]; then
    sudo -u "$TARGET_USER" -H bash -lc "$*"
    return
  fi

  echo "Cannot run as target user without sudo. Current user: $(id -un), target user: $TARGET_USER"
  exit 1
}

init_privileges() {
  if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    CAN_SUDO=1
  fi
}

detect_python_bin() {
  local candidates=(
    "$COMFY_ROOT/.venv/bin/python"
    "$COMFY_ROOT/venv/bin/python"
    "$TARGET_HOME/comfy-cli-venv/bin/python"
  )

  for candidate in "${candidates[@]}"; do
    if run_as_user "[[ -x '$candidate' ]]"; then
      PYTHON_BIN="$candidate"
      log "Using Python interpreter: $PYTHON_BIN"
      return
    fi
  done

  PYTHON_BIN="python3"
  log "Using Python interpreter: $PYTHON_BIN"
}

install_with_pip() {
  local pip_args="$*"

  if run_as_user "$PYTHON_BIN -m pip $pip_args"; then
    return
  fi

  log "pip command failed; retrying with --break-system-packages (PEP 668 fallback)"
  run_as_user "$PYTHON_BIN -m pip --break-system-packages $pip_args"
}

ensure_prereqs() {
  if [[ -f "$COMFY_ROOT/main.py" ]]; then
    COMFY_APP_DIR="$COMFY_ROOT"
  elif [[ -f "$COMFY_ROOT/ComfyUI/main.py" ]]; then
    COMFY_APP_DIR="$COMFY_ROOT/ComfyUI"
  else
    echo "ComfyUI was not found in either:"
    echo "  - $COMFY_ROOT/main.py"
    echo "  - $COMFY_ROOT/ComfyUI/main.py"
    echo "Set COMFY_ROOT if your install lives elsewhere."
    exit 1
  fi

  log "Detected ComfyUI app dir: $COMFY_APP_DIR"
  run_as_user "mkdir -p '$CUSTOM_NODES_DIR'"
}

refresh_pulid_flux() {
  if [[ ! -d "$PULID_NODE_DIR/.git" ]]; then
    log "Cloning ComfyUI-PuLID-Flux"
    run_as_user "cd '$CUSTOM_NODES_DIR' && git clone https://github.com/balazik/ComfyUI-PuLID-Flux.git"
  else
    log "Updating ComfyUI-PuLID-Flux"
    run_as_user "cd '$PULID_NODE_DIR' && git fetch --all --tags && git pull --ff-only"
  fi

  log "Installing ComfyUI-PuLID-Flux Python dependencies"
  install_with_pip "install --upgrade pip"
  install_with_pip "install -r '$PULID_NODE_DIR/requirements.txt'"
}

install_runtime_patch() {
  log "Installing runtime compatibility patch"
  run_as_user "mkdir -p '$PATCH_DIR'"
  cat >"$PATCH_FILE" <<'PYEOF'
"""Runtime compatibility patch for Flux forward_orig kwargs.

This module is loaded by ComfyUI as a custom node side-effect. It wraps
Flux-like classes that expose forward_orig() and removes kwargs that older
patched implementations do not accept.
"""

from __future__ import annotations

import inspect
import logging
from functools import wraps


LOGGER = logging.getLogger("ai_influencer_runtime_compat")
_PATCH_MARK = "__ai_influencer_runtime_compat_applied__"


def _wrap_forward_orig_method(cls: type) -> bool:
    method = getattr(cls, "forward_orig", None)
    if method is None:
        return False
    if getattr(method, _PATCH_MARK, False):
        return False

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        # Some PuLID/Flux stacks expose forward_orig() without this kwarg.
        if "timestep_zero_index" in kwargs:
            kwargs = dict(kwargs)
            kwargs.pop("timestep_zero_index", None)
        return method(self, *args, **kwargs)

    setattr(wrapped, _PATCH_MARK, True)
    setattr(cls, "forward_orig", wrapped)
    return True


def apply_patch() -> int:
    try:
        from comfy.ldm.flux import model as flux_model
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("flux runtime compat patch skipped: failed to import flux model module: %s", exc)
        return 0

    patched = 0
    for _, value in vars(flux_model).items():
        if inspect.isclass(value) and hasattr(value, "forward_orig"):
            if _wrap_forward_orig_method(value):
                patched += 1

    if patched:
        LOGGER.warning(
            "Applied Flux runtime compatibility patch to %s class(es). "
            "This is a temporary bridge; align ComfyUI and ComfyUI-PuLID-Flux versions for a permanent fix.",
            patched,
        )
    else:
        LOGGER.info("Flux runtime compatibility patch found no forward_orig targets")
    return patched


apply_patch()

# Keep custom-node discovery happy; this module is side-effect-only.
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
PYEOF
  if [[ "$CAN_SUDO" -eq 1 ]]; then
    chown "$TARGET_USER":"$TARGET_USER" "$PATCH_FILE"
  fi
}

restart_services() {
  if [[ "$CAN_SUDO" -eq 1 ]] && systemctl list-unit-files | grep -q '^comfyui.service'; then
    log "Restarting comfyui.service"
    systemctl restart comfyui.service
    systemctl --no-pager --full status comfyui.service | sed -n '1,25p'
    return
  fi

  log "Using process restart fallback (no sudo/systemd control)"
  run_as_user "pkill -f 'python3 main.py' || true"
  run_as_user "cd '$COMFY_APP_DIR' && nohup python3 main.py --listen 127.0.0.1 --port 8188 > '$TARGET_HOME/comfy.log' 2>&1 &"
  run_as_user "tail -n 30 '$TARGET_HOME/comfy.log'"
}

main() {
  init_privileges
  ensure_prereqs
  detect_python_bin
  refresh_pulid_flux
  install_runtime_patch
  restart_services

  cat <<'EOF'

Runtime compatibility fix has been applied.

Next:
1. Re-run the same QA harness command.
2. If it still fails, inspect comfy logs for custom node load errors.
EOF
}

main "$@"
