# 03. データ契約（モデル・環境変数・キャッシュ）

## Pythonモデル契約

### `DiaryEntry`

- `date: str`
  - 形式: `YYYY-MM-DD`
- `date_jpn: str`
  - 形式: `YYYY年MM月DD日`
- `index_direction: IndexDirection`
  - `INDEX` / `NO_INDEX` / `AUTO`
- `topics: list[Topic]`

### `Topic`

- `title: str`
- `id: str`（Notion block id）
- `content: list[str]`
  - 生本文。画像は `<a><picture>...</picture></a>` 文字列として格納される
- `hashtags: list[str]`
  - `#` は除去済み
- `content_html: list[str]`
  - `content` をリンクカード変換した表示用本文

### `TopicSlugEntry`

- `name: str`（正式名）
- `slug: str`（canonical slug）
- `aliases: list[str]`（別名）

## 環境変数契約（`.env`）

- `NOTION_API_KEY`
  - Notion APIのBearerトークン
- `DATABASE_ID`
  - 日記DBのID
- `NOTICE_WEBHOOK_URL`
  - Discord通知先Webhook URL
- `SLUG_DATABASE_ID`
  - トピックスラッグDBのID

## 設定値契約（固定値）

### ページング

- `INDEX_TOPICS = 20`（トップページ: 1ページあたりトピック数）
- `TOPIC_LIST = 20`（トピック一覧件数）
- `DATE_LIST = 30`（日付一覧件数）
- `TOPIC_DETAIL_DATES = 20`（トピック詳細: 日付ブロック件数）

### サムネイル

- `small = 380px`
- `medium = 520px`
- `large = 720px`
- `quality = 85`（WebP）

### その他

- `MAX_OGP_LEN = 90`（リンクカード説明文の最大文字数）

## キャッシュファイル契約

- `cache/diary_data.json`
  - 最新取得した日記生データ
- `cache/diary_data_prev.json`
  - 比較用旧データ
- `cache/ogp.json`
  - URL -> OGP辞書
- `cache/twitter.json`
  - URL -> oEmbed辞書（Twitter/Bluesky/Mastodon含む）
- `cache/topic_slugs.json`
  - `[{name, slug, aliases}]` 形式のスラッグルール

## Notionデータ契約（前提）

### 日記DB側

- プロパティ名:
  - `日付`（date）
  - `公開`（checkbox）
  - `収集対象`（select: `index` / `noindex` / `auto`）
- 本文側:
  - `heading_3` をトピック見出しとして扱う
  - `#`始まり行はハッシュタグ行として扱う

### スラッグDB側

- プロパティ名:
  - `名前`（title）
  - `スラッグ`（rich_text）
  - `エイリアス`（rich_text、改行区切り）
- `in_trash` / `archived` は読み飛ばし
