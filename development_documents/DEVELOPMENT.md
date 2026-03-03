````md
# Development Guide

## 前提
- Python: `.python-version` に準拠
- パッケージ管理: uv
- Lint/Format: ruff
- pre-commit を使用

## セットアップ
```bash
# uv インストール（例）
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL -l

# 依存関係
uv sync

# pre-commit
pre-commit install
```

## 環境変数

`.env` を用意する（dotenvで読み込む）

* `NOTION_API_KEY` : Notionのインテグレーションキー
* `DATABASE_ID` : Notionの日記DB ID
* `NOTICE_WEBHOOK_URL` : 通知先（Discord等）※不要なら空でもよい / 無効化の方針を後で決める

例:

```env
NOTION_API_KEY=secret_...
DATABASE_ID=xxxxxxxxxxxxxxxxxxxx
NOTICE_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## 生成（ローカル）

```bash
# 通常生成（Notionから取得）
uv run python scripts/generate.py

# キャッシュ使用（output/cache 等がある前提）
uv run python scripts/generate.py --use-cache
```

## サムネ生成（使う場合）

```bash
uv run python scripts/generate_thumbnails.py
```

## ローカルで生成物を見る

```bash
uv run python -m http.server 8000 --directory output
# http://localhost:8000/
```

## コーディング規約（簡易）

* 「Notion取得」「正規化」「出力」をなるべく分離する
* 生成物のパス/ファイル名は `config/filenames.py` に寄せる
* テンプレ変更は `templates/` を中心に、ロジックにHTMLを埋め込みすぎない

## よくある詰まりどころ

* Notionのブロック取得が途中で切れる → ページネーション確認
* 画像URLが期限切れ → file type のURL更新、DL/キャッシュ方針
* OGP取得が遅い → linkcardキャッシュを活用、失敗時のフォールバック

