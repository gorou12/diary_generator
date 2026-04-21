# 01. システム概要

この文書は現行コードの挙動を説明するものであり、仕様の正本ではない。
仕様の変更や判断は docs/ 配下の文書を優先する。

## 何をするプログラムか

`diary_generator` は、Notion の日記データベースを取得し、静的サイトとして出力するジェネレーターです。

- 入力: Notion API（DB + ページブロック）
- 変換: トピック抽出、リンクカード変換、画像保存/サムネイル生成、スラッグ解決
- 出力: `output/` 配下の HTML / JSON / 画像 / サムネイル

## 主な利用シーン

- 日記コンテンツの公開サイト生成
- topic/date/search ページの静的配信
- 既存画像サムネイルの再生成（手動）

## エントリポイント

- `scripts/generate.py`
  - サイト一式を生成
  - オプション:
    - `--use-cache`: 日記キャッシュ利用
    - `--use-topic-slug-cache`: トピックスラッグキャッシュ利用
- `scripts/generate_thumbnails.py`
  - `output/images` 内画像のサムネイルを再生成

## 依存ライブラリ（主要）

- `requests`: Notion API / OGP / oEmbed 呼び出し
- `jinja2`: HTML テンプレート描画
- `beautifulsoup4`: OGP メタ情報抽出
- `Pillow`: 画像サムネイル生成
- `python-dotenv`: `.env` 読み込み

## 重要ディレクトリ

- `diary_generator/`: アプリ本体
- `templates/`: Jinja2 テンプレート
- `static/src/`: CSS/JavaScript
- `cache/`: 各種キャッシュ JSON
- `output/`: 最終生成物

## 非機能的な性質

- バッチ型（実行時に全件生成）
- 生成前に `output/` の HTML/JSON を削除して作り直す
- 画像は再利用（既存画像は削除しない）
- Discord 通知ロガーを持つ（差分通知・警告通知）
