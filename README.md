# DIARY GENERATOR

## 開発方法

### 初期設定

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

### ローカル開発

日記生成: `uv run python -m scripts.generate`  
├─ 日記データキャッシュを使う: `--use-cache`  
└─ スラッグキャッシュを使う: `--use-topic-slug-cache`

サムネイル一括(再)生成: `uv run python -m scripts.generate_thumbnails`

デバッグ用サーバー起動: `uv run python -m http.server 8000 --directory output`

参考: パッケージ更新: `uv sync --upgrade`  
├─ VSCodeを開いているとvenvを掴んでいて面倒なので、ターミナルから更新するといい  
├─ pyproject.toml にて リリースから1週間以上経過したパッケージだけ入れられるようにしてある  
└─ 緊急で入れないといけないときの例: `uv sync --upgrade --exclude-newer-package "{flask=P0D}"`

参考: uv自体の更新: `uv self update`

## デプロイ

本番デプロイはGitHub Actionsから行う。

→ [docs/deployment.md](docs/deployment.md)

## 前提技術

Editor: VSCode  
Linter: ruff
