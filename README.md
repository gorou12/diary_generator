# DIARY GENERATOR

## HOW TO DEVELOPMENT

try this

```powershell
# install uv on Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex

# cd this repository and
uv sync
uv run pre-commit install
```

```bash
# install uv on macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
exec "$SHELL" -l

# cd this repository and
uv sync
uv run pre-commit install
```

Run local debug server: `uv run python -m http.server 8000 --directory output`

## DEPLOYMENT

Production deployment is performed by GitHub Actions over SSH.

See [docs/deployment.md](docs/deployment.md).

## TOPICS

Editor: VSCode  
Linter: ruff
