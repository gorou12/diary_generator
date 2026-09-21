# Production deployment

## Overview

Production deployment is initiated by GitHub Actions.

```text
push to main
    |
    v
GitHub Actions
    |
    | SSH
    v
pokete1_vps2
/home/gorou12/diary_generator
    |
    +-- git pull --ff-only origin main
    +-- uv sync
    +-- systemctl start diary-generator.service
            |
            +-- scripts.generate
            +-- rsync output/ -> /var/www/html/diary/
```

The application repository owns the GitHub Actions workflow and the deploy script.
The VPS-side systemd/nginx/sudoers configuration is owned by `gorou12/pokete-network`.

## Trigger

Workflow:

```text
.github/workflows/main.yml
```

Automatic deployment runs on pushes to `main`.

Documentation-only and deployment-definition-only changes are excluded from the automatic trigger:

- `docs/**`
- `README.md`
- `.github/**`
- `scripts/deploy_vps.sh`

This prevents a deployment workflow edit from immediately executing against a VPS whose receiving configuration may not yet have been updated.

A manual `workflow_dispatch` trigger is also available. Use it after changing deployment infrastructure to verify the connection and deployment path.

## GitHub Actions secrets

The repository requires these Actions secrets:

- `VPS_HOST`
- `VPS_USER`
- `SSH_PRIVATE_KEY`

Values must never be committed to Git.

`SSH_PRIVATE_KEY` is the private key used by GitHub Actions to connect to the production VPS.
Its matching public key must be present in:

```text
/home/gorou12/.ssh/authorized_keys
```

on the VPS.

The private key may be restored from a secure migration backup when rebuilding GitHub Actions, but it must remain only in GitHub Actions Secrets / secure backup storage.

## VPS requirements

The VPS must provide:

- user: `gorou12`
- checkout: `/home/gorou12/diary_generator`
- uv: `/home/gorou12/.local/bin/uv`
- systemd unit: `diary-generator.service`
- publication directory: `/var/www/html/diary`
- passwordless sudo permission limited to:
  - `/usr/bin/systemctl start diary-generator.service`

The VPS-side configuration is documented and managed in:

```text
gorou12/pokete-network
docs/apps/diary-generator.md
config/host/systemd/
config/host/sudoers/
```

## Deployment script

`scripts/deploy_vps.sh` is executed on the VPS after `git pull`.

It performs:

1. `uv sync`
2. `sudo -n /usr/bin/systemctl start diary-generator.service`

HTML generation and rsync are intentionally not duplicated here.
They are defined once in the systemd service managed by `pokete-network`.

## Why systemd owns generation/publishing

The same generation process is used by:

- the hourly timer
- GitHub Actions deployments
- manual runs

Keeping generation and publication in one systemd unit avoids three slightly different command sequences.

It also keeps execution logs in journald:

```bash
journalctl -u diary-generator.service -n 100 --no-pager
```

## Manual production test

After the VPS-side configuration is updated, run the `Deploy to VPS` workflow manually from GitHub Actions.

On the VPS, verify:

```bash
systemctl status diary-generator.timer --no-pager
journalctl -u diary-generator.service -n 100 --no-pager
```

Then confirm the published site.

## SSH troubleshooting

The deployment uses two separate Git relationships:

1. GitHub Actions -> VPS
   - uses `SSH_PRIVATE_KEY`
   - matching public key is in VPS `authorized_keys`

2. VPS -> GitHub for `git pull`
   - this repository is public, so an HTTPS `origin` can pull without a GitHub SSH key

Check the VPS repository remote with:

```bash
cd /home/gorou12/diary_generator
git remote -v
```

Do not print or paste the private key while troubleshooting.
