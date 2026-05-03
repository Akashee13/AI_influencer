#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$HOME/ai-influencer}"
SERVICE_NAME="comfyui-gateway.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo ./scripts/deploy_comfyui_gateway.sh [target-dir]"
  exit 1
fi

mkdir -p "$ROOT_DIR"
chown -R "$TARGET_USER":"$TARGET_USER" "$ROOT_DIR"

cat > "$SERVICE_PATH" <<EOF2
[Unit]
Description=ComfyUI Gateway
After=network-online.target comfyui.service
Wants=network-online.target

[Service]
Type=simple
User=$TARGET_USER
WorkingDirectory=$ROOT_DIR
Environment=PYTHONUNBUFFERED=1
Environment=COMFYUI_URL=http://127.0.0.1:8188
Environment=WORKFLOW_DIR=$ROOT_DIR/comfyui/workflows
EnvironmentFile=-$ROOT_DIR/.env.gateway
ExecStart=/usr/bin/env python3 $ROOT_DIR/services/comfyui_gateway.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF2

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,25p'
