#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
INSTALL_ROOT="$TARGET_HOME/comfy"
CLI_VENV="$TARGET_HOME/comfy-cli-venv"
SERVICE_NAME="comfyui.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

as_user() {
  sudo -u "$TARGET_USER" -H bash -lc "$*"
}

ensure_packages() {
  log "Installing base packages"
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    ubuntu-drivers-common
}

ensure_nvidia_driver() {
  if command -v nvidia-smi >/dev/null 2>&1; then
    log "NVIDIA driver already present"
    return 0
  fi

  log "Installing recommended NVIDIA driver"
  ubuntu-drivers install
  log "Driver installation finished. Reboot the VM, reconnect, and rerun this script."
  exit 10
}

ensure_comfy_cli() {
  if [[ ! -d "$CLI_VENV" ]]; then
    log "Creating comfy-cli virtualenv at $CLI_VENV"
    as_user "python3 -m venv '$CLI_VENV'"
  fi

  log "Installing comfy-cli"
  as_user "source '$CLI_VENV/bin/activate' && pip install --upgrade pip && pip install --upgrade comfy-cli"
}

install_comfyui() {
  log "Installing ComfyUI into $INSTALL_ROOT"
  as_user "source '$CLI_VENV/bin/activate' && comfy --workspace '$INSTALL_ROOT' install"
}

write_service() {
  log "Writing systemd service"
  cat >"$SERVICE_PATH" <<EOF
[Unit]
Description=ComfyUI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$TARGET_USER
WorkingDirectory=$INSTALL_ROOT/ComfyUI
Environment=HOME=$TARGET_HOME
ExecStart=$CLI_VENV/bin/comfy --workspace $INSTALL_ROOT launch -- --listen 127.0.0.1 --port 8188 --preview-method auto
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now "$SERVICE_NAME"
}

verify() {
  log "Checking NVIDIA runtime"
  nvidia-smi

  log "Checking ComfyUI service"
  systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,20p'
}

main() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run this script with sudo."
    exit 1
  fi

  ensure_packages
  ensure_nvidia_driver
  ensure_comfy_cli
  install_comfyui
  write_service
  verify

  cat <<'EOF'

ComfyUI is installed and started on 127.0.0.1:8188.

Next decision:
1. Secure access via SSH tunnel from your Mac
2. Temporary public access via firewall rule and external IP

Stop here and choose access method before exposing the UI.
EOF
}

main "$@"
