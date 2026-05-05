# GCP ComfyUI Setup

This is the VM bootstrap flow for the current `1 x NVIDIA T4` instance.

## Files
- Script: [scripts/gcp-comfyui-setup.sh](/Users/akash/Documents/PetProjects/AI Influencer/scripts/gcp-comfyui-setup.sh)

## What the script does
1. Installs Ubuntu packages needed for Python and Git-based tooling.
2. Installs the recommended NVIDIA driver if it is missing.
3. Stops and asks for a reboot after driver installation.
4. Installs `comfy-cli`.
5. Installs `ComfyUI` plus `ComfyUI-Manager`.
6. Creates a `systemd` service named `comfyui.service`.
7. Starts ComfyUI bound to `127.0.0.1:8188`.

## Run It On The VM
Open the VM's `SSH` console in GCP and run:

```bash
cat > /tmp/gcp-comfyui-setup.sh <<'EOF'
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
  cat >"$SERVICE_PATH" <<EOF2
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
EOF2

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

  cat <<'EOF2'

ComfyUI is installed and started on 127.0.0.1:8188.

Next decision:
1. Secure access via SSH tunnel from your Mac
2. Temporary public access via firewall rule and external IP

Stop here and choose access method before exposing the UI.
EOF2
}

main "$@"
EOF

chmod +x /tmp/gcp-comfyui-setup.sh
sudo /tmp/gcp-comfyui-setup.sh
```

## Expected Pause
- If `nvidia-smi` is not yet available, the script will install the driver and stop.
- At that point, reboot the VM from GCP, reconnect over SSH, and rerun the same command block.
- After the second run succeeds, stop and choose how you want to open ComfyUI from your Mac.

## If Face-Locked FLUX Runs Fail

If the QA run fails with:

`forward_orig() got an unexpected keyword argument 'timestep_zero_index'`

run the runtime repair from the VM:

```bash
cd ~/ai-influencer
chmod +x scripts/fix_flux_timestep_zero_index.sh
./scripts/fix_flux_timestep_zero_index.sh
```

If your VM user has sudo, running with `sudo` is also fine.

Then rerun the same QA harness command to confirm image generation succeeds.
