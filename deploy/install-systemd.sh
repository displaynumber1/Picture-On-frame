#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="pictureonframe"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo cp "${ROOT_DIR}/deploy/pictureonframe.service" "${SERVICE_FILE}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl start "${SERVICE_NAME}"
sudo systemctl status "${SERVICE_NAME}" --no-pager
