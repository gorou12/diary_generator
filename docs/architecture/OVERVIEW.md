# Diary Generator Architecture

このリポジトリは、Notion の日記DBからデータを取得し、静的HTML/JSONを生成して公開するためのジェネレータです。

## 目的
- Notion を編集UIとして使い、日記を静的サイトとして出力する
- 「日付ベース」「トピックベース」で横断閲覧できるようにする

---

## 入出力

### Input（Notion）
- 対象DB: `DATABASE_ID` で指定
- 認証: `NOTION_API_KEY` で指定
- 取得対象ページの条件:
  - `日付` が入っている
  - `公開` が true
- 取得対象コンテンツ:
  - 見出しレベル3を見出し、次の見出しレベル3またはページの最後までを本文とする

### Output（生成物）
- 生成先: `output/`
- 静的ファイル: `static/` → `output/src/` へコピー
  - ファビコン: `favicon.ico`
  - 共通JS: `script.js`
  - 共通CSS: `style.css`
  - 検索ページ用JS: `search.js`
  - 検索ページ用CSS: `search.css`
- HTML:
  - トップ: `output/index.html`
  - 日付一覧/詳細: `output/dates/...`
  - トピック一覧/詳細: `output/topics/...`
  - 検索ページ: `output/search.html`
- JSON:
  - 検索用: `output/json/search_data.json`
  - カレンダー用: `output/json/calendar_data.json`
- 画像:
  - オリジナル画像: `output/images/...`
  - サムネイル大: `output/thumbnails/large/...`
  - サムネイル中: `output/thumbnails/middle/...`
  - サムネイル小: `output/thumbnails/small/...`

### ログ出力
- 生成先: `logs/`

---

## 処理の全体フロー（パイプライン）

1. Notion DB から日記ページ一覧を取得（ページネーションあり）
2. 各日記ページのブロックを取得
3. ブロック列を「トピック（見出し3単位）」に分割して正規化
4. 画像・リンクカード・ハッシュタグなどを整形
5. HTML生成（テンプレート + データ）
6. JSON生成（検索・カレンダー等）
7. `output/` に書き出し、静的公開

主要エントリポイント:
- `scripts/generate.py` → `diary_generator/generator.generate_all()`

---

## データモデル（概念）
- DiaryEntry（1日分）
  - date: `YYYY-MM-DD`
  - index_direction: index/noindex/auto
  - topics: Topic[]
- Topic（1トピック）
  - title: 見出し3の本文
  - id: Notion block id
  - content: 文字列の配列（HTML化前の行）
  - content_html: リンクカード等を埋め込んだHTML
  - hashtags: `#...` から抽出したタグ（`#非公開` は除外フラグとして扱う）

※ 実体は `diary_generator/models/*` を参照。

---

## Notionブロックの解釈ルール（現状）
- `heading_3` をトピックの開始として扱う
- `image` は `<img ...>` 相当のタグを生成して content に追加
- `#...` から始まる行はハッシュタグとして抽出（本文には入れない）
- `#非公開` を含むトピックは出力しない
- 「編集直後のブロック」は取得タイミングによって不安定なので、一定時間（例: 5分）経過したものだけを対象にする

---

## 主なモジュール責務

### 取得・正規化
- `diary_generator/contents.py`
  - キャッシュ読み込み/書き込み
  - Notion DB の取得
  - ブロック列の解析→DiaryEntry/Topicへの変換
  - 画像タグ生成、リンクカード生成の呼び出し

### Notion API
- `diary_generator/notion_api/*`
  - database query
  - block children list

### HTML生成
- `diary_generator/html/*`
  - index / dates / topics / search の各ページ生成

### JSON生成
- `diary_generator/json/*`
  - 検索用・カレンダー用データの生成

### 付加機能（ユーティリティ）
- 画像: `diary_generator/util/img/*`（ダウンロード/サムネ生成など）
- リンクカード: `diary_generator/util/linkcard/*`（OGP取得・キャッシュなど）
- 差分: `diary_generator/util/diarydiff.py`（前回JSONとの差分）
- ロガー: `diary_generator/logger/*`（Discord通知など）

---

## 設計上の意図（後で埋める）
- なぜ topic は heading_3 なのか:
- なぜハッシュタグを本文から除外するのか:
- 生成物に JSON を分けている理由:
- キャッシュの目的と扱い（`--use-cache`）:

---

## 今後の拡張ポイント（メモ）
- 検索: インデックス方式 / 正規化ルール / 日本語トークナイズ
- 人気タグ: 集計単位（topic単位？日付単位？）
- カレンダー: 表示の粒度 / 範囲
- 非公開の扱い: `#非公開` 以外のルール追加（例: `#自分用`）
- URL/slug: topic title の揺れと永続ID（block idを主にするか等）
