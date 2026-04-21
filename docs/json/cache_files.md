# 内部キャッシュJSON設計

## 1. この文書の目的

この文書は、Notion から取得した日記データを内部的に保存するための JSON キャッシュ構造を定義する。

本キャッシュは公開用データではなく、以下の目的で使用する。

- 差分取得判定
- 再取得不要ページの詳細データ再利用
- 全件生成データの再構成
- キャッシュ欠損時の復旧判断

本キャッシュは内部実装用であり、公開URLや公開JSONの仕様は定義しない。  
全体方針は `docs/policies.md`、変更目的は `docs/features/json_storage_change.md` を参照する。

---

## 2. 基本方針

### 2.1 キャッシュの分離

内部キャッシュは、少なくとも以下の2種類に分ける。

- 一覧メタ情報キャッシュ
- 詳細データキャッシュ

必要であれば、生成直前の統合データキャッシュを追加してもよい。  
ただし、差分判定に必要な情報と詳細本文データは論理的に分離すること。

---

### 2.2 保存単位

キャッシュの保存単位は **Notion の日付ページ単位（page_id 単位）** とする。

理由：

- 差分判定に `last_edited_time` を使いやすい
- 詳細取得処理が日付ページ単位である
- 日付ページごとの再取得・再利用に対応しやすい

---

### 2.3 JSONの優先事項

本キャッシュ設計では、以下を重視する。

- 読みやすさ
- 壊れにくさ
- 差分更新しやすさ
- デバッグしやすさ
- 将来の項目追加がしやすいこと

過度な圧縮や難解なネストは避ける。

---

## 3. キャッシュファイル一覧

### 3.1 必須ファイル

#### `cache/diary_page_index.json`
日付ページ単位の一覧メタ情報を保存する。

用途：

- 差分取得判定
- 公開対象・収集対象の判定
- 削除・非公開化・対象外化の検知

---

#### `cache/diary_page_details.json`
日付ページ単位の詳細データを保存する。

用途：

- 再取得不要ページの再利用
- 全件生成データの再構成

---

### 3.2 任意ファイル

#### `cache/diary_data.json`
生成用に組み立てた全件データを保存する。

用途：

- 従来互換
- デバッグ
- 生成確認

このファイルは必須ではない。  
ただし既存コードとの互換維持や確認用途のため、当面残してもよい。

---

## 4. `diary_page_index.json` 仕様

## 4.1 役割

`diary_page_index.json` は、各日付ページの最小限の一覧情報を保持する。  
詳細ブロック本文は保持しない。

---

## 4.2 JSON構造

トップレベルはオブジェクトとし、`page_id` をキーにする。

例：

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-22T14:30:00+09:00",
  "pages": {
    "1d4b3c...": {
      "page_id": "1d4b3c...",
      "date": "2026-04-21",
      "title": "20260421",
      "last_edited_time": "2026-04-21T22:14:03.000Z",
      "is_public": true,
      "is_collectible": true,
      "index_direction": "public",
      "source_status": "active"
    },
    "8a92ef...": {
      "page_id": "8a92ef...",
      "date": "2026-04-20",
      "title": "20260420",
      "last_edited_time": "2026-04-20T23:59:12.000Z",
      "is_public": true,
      "is_collectible": false,
      "index_direction": "private",
      "source_status": "filtered_out"
    }
  }
}
```

---

## 4.3 フィールド定義

### トップレベル

* `schema_version`

  * 型: number
  * 必須
  * このJSON構造のバージョン
* `generated_at`

  * 型: string (ISO 8601)
  * 必須
  * このキャッシュを書き出した日時
* `pages`

  * 型: object
  * 必須
  * `page_id` をキーとするページ辞書

---

### `pages[page_id]`

* `page_id`

  * 型: string
  * 必須
  * Notion ページID
* `date`

  * 型: string (`YYYY-MM-DD`)
  * 必須
  * 日付ページの日付
* `title`

  * 型: string
  * 必須
  * Notion 上のページタイトル
* `last_edited_time`

  * 型: string (ISO 8601)
  * 必須
  * 差分判定に使用する
* `is_public`

  * 型: boolean
  * 必須
  * 公開対象かどうか
* `is_collectible`

  * 型: boolean
  * 必須
  * 収集対象かどうか
* `index_direction`

  * 型: string
  * 必須
  * 現行実装の index_direction を保持する
* `source_status`

  * 型: string
  * 必須
  * `active` / `filtered_out` / `deleted` などの内部状態を表す

---

## 4.4 制限事項

* `pages` のキーと `page_id` フィールドは一致しなければならない
* `date` は1ページにつき1つとする
* `last_edited_time` は Notion の値をそのまま保持する
* 差分判定は基本的に `last_edited_time` を基準に行う
* `source_status` の列挙値は実装とドキュメントで一致させること

---

## 5. `diary_page_details.json` 仕様

## 5.1 役割

`diary_page_details.json` は、各日付ページから取得した詳細データを保持する。
ここには、最終的に `DiaryEntry` 生成へ必要なトピック単位データを保存する。

---

## 5.2 JSON構造

トップレベルはオブジェクトとし、`page_id` をキーにする。

例：

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-22T14:30:00+09:00",
  "pages": {
    "1d4b3c...": {
      "page_id": "1d4b3c...",
      "date": "2026-04-21",
      "last_edited_time": "2026-04-21T22:14:03.000Z",
      "topics": [
        {
          "title": "近鉄",
          "body_html": "<p>今日は近鉄で移動した。</p>",
          "hashtags": ["交通", "近鉄"],
          "is_private": false,
          "slug_hint": null
        },
        {
          "title": "作業メモ",
          "body_html": "<p>内部作業のメモ。</p>",
          "hashtags": ["非公開"],
          "is_private": true,
          "slug_hint": null
        }
      ]
    }
  }
}
```

---

## 5.3 フィールド定義

### トップレベル

* `schema_version`

  * 型: number
  * 必須
* `generated_at`

  * 型: string (ISO 8601)
  * 必須
* `pages`

  * 型: object
  * 必須

---

### `pages[page_id]`

* `page_id`

  * 型: string
  * 必須
* `date`

  * 型: string (`YYYY-MM-DD`)
  * 必須
* `last_edited_time`

  * 型: string (ISO 8601)
  * 必須
  * 一覧キャッシュとの対応確認にも使用する
* `topics`

  * 型: array
  * 必須
  * 日付ページ配下のトピック一覧

---

### `topics[]`

* `title`

  * 型: string
  * 必須
  * トピック見出し
* `body_html`

  * 型: string
  * 必須
  * HTML化済み本文
* `hashtags`

  * 型: array of string
  * 必須
  * 本文内から抽出したハッシュタグ
* `is_private`

  * 型: boolean
  * 必須
  * `#非公開` 等により公開除外されるトピックかどうか
* `slug_hint`

  * 型: string or null
  * 任意
  * 将来の slug 制御や調査に使う補助情報。不要なら省略可

---

## 5.4 制限事項

* `topics` の順序は日付ページ上の記載順を維持する
* 本文データは生成に必要な粒度を保持する
* 公開除外対象トピックを保持するかどうかは実装方針次第だが、少なくとも最終出力では除外されなければならない
* `last_edited_time` は対応する一覧キャッシュと一致することが望ましい
* 詳細キャッシュ単体では差分判定を行わず、一覧キャッシュと併用する

---

## 6. `diary_data.json` 仕様（任意）

## 6.1 役割

`diary_data.json` は、全件生成用に再構成したデータを保存するための任意キャッシュである。

用途：

* 従来コードとの互換維持
* デバッグ
* 生成前後比較

このファイルは将来的に廃止してもよい。

---

## 6.2 注意

* 正本は `diary_page_index.json` と `diary_page_details.json` とする
* `diary_data.json` が存在しても、差分判定の基準にしてはならない
* 必要なら毎回再生成してよい

---

## 7. 更新ルール

### 7.1 一覧メタ情報更新

毎回の一覧走査結果をもとに、`diary_page_index.json` を更新する。

* 新規ページは追加
* 更新ページは `last_edited_time` 等を更新
* 非公開化・対象外化・削除は `source_status` に反映する
* 必要なら対象外ページを残したまま状態変更してよい

---

### 7.2 詳細データ更新

`diary_page_details.json` は、再取得対象ページのみ上書き更新する。

* 再取得対象ページは最新内容で置き換える
* 再取得不要ページは既存値を保持する
* 削除・非公開化・対象外化ページは、必要に応じて削除または無効化してよい

---

## 8. 障害時・破損時の扱い

### 8.1 基本方針

キャッシュが壊れている場合、不整合な状態で無理に続行しない。

---

### 8.2 想定する対処

* JSONパース不能: キャッシュ無効として扱う
* 必須キー欠損: キャッシュ無効として扱う
* schema_version 不一致: 互換処理がなければ再生成する
* index と details の対応不整合: 必要に応じて全件再取得へフォールバックする

---

## 9. schema_version

将来の形式変更に備え、各キャッシュファイルは `schema_version` を持つ。

ルール：

* 互換性のない変更をした場合は version を上げる
* 実装側は version を確認し、読めない場合は再生成またはフォールバックする

---

## 10. 実装上の注意

* 文字列キーの順序や整形は可読性を重視してよい
* JSON書き込みは可能な限り原子的に行う
* 一覧キャッシュと詳細キャッシュは、同一実行内で整合が取れていること
* 内部キャッシュは公開ディレクトリに配置しない

---

## 11. 非目標

この文書では以下は定義しない。

* 公開用 JSON (`search_data.json`, `calendar_data.json`) の仕様
* HTMLテンプレート構造
* slug最終決定ロジック
* OGPキャッシュ仕様
* Notion入力ルール

---

## 12. Cursor への補足

Cursor に実装を依頼する際は、以下を明示すること。

* 本文書は内部キャッシュJSONの正本である
* 公開用 JSON の形式変更は今回の対象外である
* URL構造変更は今回の対象外である
* 不明点は `docs/policies.md` と `docs/features/json_storage_change.md` を優先する
