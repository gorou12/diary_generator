# 07. 変更ガイド（AI実装依頼用）

## 依頼フォーマット（推奨）

AIへは次の形で渡すと、実装精度が上がる。

1. 背景:
   - 何を実現したいか
2. 変更仕様:
   - 入力条件
   - 出力期待値
   - 例外時の扱い
3. 影響範囲:
   - どのページ/JSON/処理に効くか
4. 受け入れ条件:
   - 目視確認ポイント
   - 自動テスト（必要なら）

## 依頼テンプレート

```md
### 背景
（例）トピック詳細ページのページサイズを調整したい

### 現状
- `TOPIC_DETAIL_DATES = 20`
- 対象: `/topics/{slug}/page/{n}/`

### 変更したい仕様
- 1ページあたり日付ブロックを 30 件にする
- 既存URL互換（redirect）を壊さない

### 受け入れ条件
- 既存生成が失敗しない
- `/topics/{slug}/` と `/topics/{slug}/page/2/` が期待件数で出る
- `search_data.json` / `calendar_data.json` に副作用がない
```

## 変更の起点マップ（どこを触るか）

- データ取得ルール変更:
  - `diary_generator/contents.py`
- スラッグ/URL変更:
  - `diary_generator/topic_slugs/*`
  - `diary_generator/topic_slug.py`
  - `diary_generator/html/topics/detail.py`
  - `diary_generator/util/utilities.py`
- ページング変更:
  - `diary_generator/config/paginate.py`
  - 各 `html/*/list.py`, `html/index.py`, `html/topics/detail.py`
- 検索仕様変更:
  - `diary_generator/json/search.py`
  - `static/src/search.js`
  - `templates/search.html`
- カレンダー仕様変更:
  - `diary_generator/json/calendar.py`
  - `static/src/script.js`
  - `templates/sidebar.html`
- 画像/サムネイル仕様変更:
  - `diary_generator/util/img/*`
  - `scripts/generate_thumbnails.py`
- リンクカード仕様変更:
  - `diary_generator/util/linkcard/*`

## 現状の注意点（実装由来）

- `copy_static_files()` は `output/src/` を一度削除してからコピーする
- `TopicSlugConflictError` は競合時に生成全体を止める
- `index_direction=AUTO` は「夢」始まり除外後3件以上で index
- 編集後5分未満のトピックは収集対象外
- OGP/oEmbed失敗はフォールバックリンクで継続する

## 変更時の最低チェックリスト

- `uv run -m scripts.generate` が成功する
- `output/index.html` と `output/dates/*.html` が生成される
- `output/topics/*` の canonical + redirect が成立する
- `output/json/search_data.json` と `output/json/calendar_data.json` が生成される
- 既存の `cache/*.json` が壊れていない
