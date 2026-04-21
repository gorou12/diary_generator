# 02. アーキテクチャと生成フロー

この文書は現行コードの挙動を説明するものであり、仕様の正本ではない。
仕様の変更や判断は docs/ 配下の文書を優先する。

## レイヤー構成

- `scripts/`
  - CLI引数処理、実行開始
- `diary_generator/generator.py`
  - 全体オーケストレーション
- `diary_generator/contents.py`
  - Notion日記DB取得、Topic抽出、本文変換
- `diary_generator/topic_slugs/`
  - 手動スラッグ取得・正規化・競合検出・URL解決
- `diary_generator/html/`
  - HTML生成（index/dates/topics/search）
- `diary_generator/json/`
  - `search_data.json` / `calendar_data.json` 生成
- `diary_generator/util/`
  - テンプレート描画、差分通知、画像/リンクカード処理

## 生成処理の順序（`generate_all`）

1. `contents.get()` で日記データを取得
2. `TopicSlugResolver` を構築し、`topic_url` 関数を差し替え
3. `filemaintenance.reflesh_files()` で `output` 内HTML/JSON削除
4. `filemaintenance.copy_static_files()` で `static/` を `output/` にコピー
5. HTML生成
   - `index`
   - `dates/list`
   - `dates/detail`
   - `topics/list`
   - `topics/detail`
   - `search`
6. JSON生成
   - `search_data.json`
   - `calendar_data.json`

## 日記データ取得フロー

### キャッシュ分岐

- `USE_CACHE=True` かつ `cache/diary_data.json` がある:
  - キャッシュ読み込み
- それ以外:
  - 旧JSONを `cache/diary_data_prev.json` にコピー
  - Notion から再取得
  - `cache/diary_data.json` に保存
  - 新旧差分を作成して通知

### Notion DB -> Topic 変換ルール（要点）

- DB項目フィルタ:
  - `日付` が空 -> 除外
  - `公開` が false -> 除外
  - `収集対象` が空 -> 除外
- ページ内ブロック:
  - `heading_3`: 新しいトピック開始
  - `image`: 画像ダウンロード + `picture` タグ埋め込み
  - `#` で始まる行: ハッシュタグ抽出（`#tag` -> `tag`）
  - その他テキスト: 本文として保持（改行は `<br>`）
- 非公開トピック:
  - ハッシュタグに `非公開` を含むトピックは除外
- 編集直後除外:
  - `last_edited_time + 5分` を過ぎたトピックのみ採用

## スラッグ解決フロー

- `load_topic_slug_rules()` で以下を実施
  - `USE_TOPIC_SLUG_CACHE=True` なら `cache/topic_slugs.json` を優先読込
  - それ以外は Notion のスラッグDBを取得し、キャッシュ保存
- キー正規化:
  - `NFKC` + 全角空白を半角化 + 空白圧縮
- 競合:
  - 同一正規化キーに異なるslugが割り当たると例外
- 未定義トピック:
  - `t-xxxxxxxxxx`（SHA1先頭10桁）を自動採番

## 失敗時挙動

- `scripts/generate.py` は例外時に終了コード1で終了
- Notion API 呼び出しで非200は例外
- OGP / oEmbed / 画像ダウンロード失敗は原則フォールバックして継続
