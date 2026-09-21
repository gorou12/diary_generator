#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV="/home/gorou12/.local/bin/uv"

cd "$ROOT"

echo "== Sync dependencies =="
"$UV" sync

echo "== Generate and publish through systemd =="
sudo -n /usr/bin/systemctl start diary-generator.service

echo "== Deployment completed =="
