# 06. 実行・運用仕様

この文書は現行コードの挙動を説明するものであり、仕様の正本ではない。
仕様の変更や判断は docs/ 配下の文書を優先する。

## ローカル実行

### フル生成

```bash
uv run -m scripts.generate
```

### キャッシュ利用

```bash
uv run -m scripts.generate --use-cache --use-topic-slug-cache
```

### サムネイル再生成

```bash
uv run -m scripts.generate_thumbnails
```

## 出力物（`output/`）

- HTML:
  - `index*.html`, `dates*.html`, `topics*.html`, `search.html`
  - `dates/*.html`
  - `topics/**/index.html`（canonical + redirect）
- JSON:
  - `json/search_data.json`
  - `json/calendar_data.json`
- 静的アセット:
  - `src/*`（`static/` からコピー）
- 画像:
  - `images/*`
  - `thumbnails/{small,medium,large}/*.webp`

## 生成時の削除/保持ポリシー

- 削除:
  - `output/**` の `.html` / `.json`
- 保持:
  - `output/images/*`
  - `cache/*`

## ログ出力

- `logs/system.log`
  - 通常ログ + 警告
- `logs/logger.log`
  - ロガー内部エラー
- Discord通知
  - `NOTICE_WEBHOOK_URL` へ送信
  - 日記差分、警告を送る

## CI/CD（GitHub Actions）

- `main` への push で実行
- VPSにSSH接続し、以下を実行
  - `uv sync`
  - `uv run -m scripts.generate`
  - `rsync -a --delete output/ /var/www/html/diary/`

## 障害時の一次確認ポイント

1. `.env` の必須変数が埋まっているか
2. Notion APIキー・DB ID の有効性
3. `cache/topic_slugs.json` とスラッグDBの内容不整合
4. ネットワーク不調（OGP/oEmbed/画像URL）
5. `output/images` の権限・容量
