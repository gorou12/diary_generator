# 04. ページ仕様とURL契約

この文書は現行コードの挙動を説明するものであり、仕様の正本ではない。
仕様の変更や判断は docs/ 配下の文書を優先する。

## 生成される主要ページ

- トップ:
  - `/index.html`
  - `/index_2.html` 以降（トピック数基準ページング）
- 日付一覧:
  - `/dates.html`
  - `/dates_2.html` 以降
- 日付詳細:
  - `/dates/YYYY-MM-DD.html`
  - `/dates/YYYY-MM-DD/page/{n}/`（2ページ目以降）
- トピック一覧:
  - `/topics.html`
  - `/topics_2.html` 以降
- トピック詳細（canonical）:
  - `/topics/{slug}/`
  - `/topics/{slug}/page/{n}/`
- 小トピック恒久リンク:
  - `/entries/{Topic.id}/`
- 検索:
  - `/search.html`

## トピックURL解決規約

- テンプレートは `topic_url(title_or_hashtag)` を利用
- resolverが有効な場合:
  - 手動スラッグ定義があればそれを採用
  - なければ自動スラッグ `t-xxxxxxxxxx`
- resolver未設定時（フォールバック）:
  - `/topics/{title}.html` 形式を返す

## リダイレクト仕様（互換性維持）

`topics/detail` 生成時に以下を出力する。

- `/topics/{canonical_slug}/page/1/` -> `/topics/{canonical_slug}/`
- 旧URL `/topics/{raw_label}.html` -> canonical URL
- 旧自動スラッグ `/topics/{auto_slug}/` -> canonical URL（slugが異なる場合）

実装方式は `redirect.html`（meta refresh + JS `location.replace`）。

## 小トピックアンカーと恒久リンク

- トップ、日付詳細、トピック詳細に表示される小トピック見出しには `topic-{Topic.id}` のHTML IDを付与する。
- 見出しのトピック詳細リンク（🔍）の右隣に、`/entries/{Topic.id}/` への恒久リンク（🔗）を表示する。
- `/entries/{Topic.id}/index.html` は検索インデックス対象外（`noindex, follow`）のリダイレクトページ。
- 転送先は日付詳細ページ内のアンカーで、1ページ目は `/dates/YYYY-MM-DD.html#topic-{Topic.id}`、2ページ目以降は `/dates/YYYY-MM-DD/page/{n}/#topic-{Topic.id}`。
- ページ番号は日付詳細ページと同じ `DATE_DETAIL_TOPICS` による分割結果から決定するため、日付ページのページネーションと整合する。

## インデックス制御

共通テンプレート `base.html` で以下を出力:

- `should_index=True`:
  - `<meta name="robots" content="index, follow">`
- `should_index=False`:
  - `<meta name="robots" content="noindex, follow">`

### 日付詳細ページの判定

- `index_direction=index` -> index
- `index_direction=noindex` -> noindex
- `index_direction=auto`:
  - 先頭文字が「夢」のトピックを除いた件数が3件以上なら index

## ページネーション仕様

- トップ:
  - 日付を新しい順に並べ、1ページの総トピック数が `INDEX_TOPICS` を超えたら改ページ
  - 1日だけで上限超過してもその日を単独ページとして保持
- 日付一覧:
  - ユニークな日付を新しい順に `DATE_LIST` 件ごと
- トピック一覧:
  - 出現回数（見出し + ハッシュタグ）で降順、`TOPIC_LIST` 件ごと
- 日付詳細:
  - 1日内の小トピックを元の並び順のまま `DATE_DETAIL_TOPICS` 件ごと
  - 1ページ目は `/dates/YYYY-MM-DD.html`、2ページ目以降は `/dates/YYYY-MM-DD/page/{n}/`
- トピック詳細:
  - 日付ブロックを新しい順に `TOPIC_DETAIL_DATES` 件ごと

## 画面機能（フロントJS）

- テーマ切替:
  - ボタンクリックで `html.dark` を切替
  - `localStorage.theme` に保存
- サイドバーカレンダー:
  - `/json/calendar_data.json` を読込
  - 月送り、現在月ラベル、日付ページで選択日強調
- 全文検索:
  - `/json/search_data.json` を読込
  - タイトル + 本文 + ハッシュタグ文字列で部分一致
