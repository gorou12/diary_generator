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

## TOPICS

Editor: VSCode
Linter: ruff

