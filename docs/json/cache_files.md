# キャッシュファイル仕様

## 1. 目的

この文書は、日記ブログ生成で使用するキャッシュJSONファイルの責務・構造・制約を定義する。

対象ファイルは以下の2つ。

- 全体インデックスキャッシュ
- 詳細キャッシュ

このキャッシュは Notion API の結果をそのまま保存するものではなく、
**静的サイト生成に適した中間データ**として保持する。

---

## 2. 基本方針

### 2.1 事実を保持する

キャッシュには、元データまたは抽出結果として安定して扱える**事実情報**を保存する。

例:

- NotionページID
- ブロックID
- タイトル
- 日付
- タグ
- 最終更新日時
- ブロック種別
- プレーンテキスト

### 2.2 派生値は原則保持しない

以下のような、ルール変更で変わりうる値は原則保持しない。

- 公開可否
- 出力対象可否
- source status
- 一覧掲載可否
- URL出力先の最終判定

これらはキャッシュ読み込み後に判定する。

### 2.3 構造化データを優先する

本文はHTML断片を主として保持しない。
Notionブロックを構造化した形で保持し、HTMLは必要に応じて生成する。

### 2.4 壊れても再生成可能であること

キャッシュはすべてNotionから再構築可能であることを前提とする。
そのため、キャッシュは永続的な正本ではなく、再生成可能な中間成果物である。

---

## 3. ファイル一覧

## 3.1 index cache

想定パス例:

```text
cache/diary_index.json
```

役割:

- データベース一覧の保持
- 差分更新判定
- 日記ページ単位の基本情報の保持

## 3.2 detail cache

想定パス例:

```text
cache/diary_detail.json
```

役割:

- 日記ページごとのトピック抽出結果の保持
- トピック本文ブロックの保持
- HTML生成・検索用情報の保持

---

## 4. 全体インデックスキャッシュ仕様

## 4.1 トップレベル構造

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-22T08:00:00+09:00",
  "entries": [
    {
      "page_id": "xxxxxxxx",
      "page_name": "20260422",
      "entry_date": "2026-04-22",
      "index_direction": "index",
      "last_edited_time": "2026-04-22T07:10:00.000Z",
      "source_last_edited_time": "2026-04-22T07:10:00.000Z"
    }
  ]
}
```

## 4.2 フィールド定義

### `schema_version`
- 型: number
- 必須
- JSONスキーマバージョン

### `generated_at`
- 型: string
- 必須
- このJSONを書き出した日時

### `entries`
- 型: array
- 必須
- 日記ページ単位の一覧

### `entries[].page_id`
- 型: string
- 必須
- NotionページID

### `entries[].page_name`
- 型: string
- 必須
- Notion上のページ名
- 例: `20260422`

### `entries[].entry_date`
- 型: string
- 必須
- ブログ上での日付
- ISO日付文字列を推奨
- 例: `2026-04-22`

### `entries[].last_edited_time`
- 型: string
- 必須
- キャッシュ側で比較に使う最終更新日時

### `entries[].source_last_edited_time`
- 型: string
- 必須
- Notionから取得した最終更新日時
- `last_edited_time` と同値でもよい
- 今後内部加工が必要になった場合の拡張余地として分けてもよい

### `entries[].index_direction`
- 型: string
- 必須
- Notionの日記ページメタデータ由来の事実値
- 例: `index`, `noindex`

## 4.3 制約

- `page_id` は一意でなければならない
- `entry_date` は日付ページURLの基準になるため、同一公開集合内で一意であることが望ましい
- entries は新しい日付順または処理しやすい一定順で並べる
- `source_status` は持たない

---

## 5. 詳細キャッシュ仕様

## 5.1 トップレベル構造

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-22T08:00:00+09:00",
  "entries": [
    {
      "page_id": "xxxxxxxx",
      "page_name": "20260422",
      "entry_date": "2026-04-22",
      "last_edited_time": "2026-04-22T07:10:00.000Z",
      "has_pending_topics": false,
      "topics": [
        {
          "topic_id": "block_h3_xxxx",
          "title": "買ったもの",
          "last_edited_time": "2026-04-22T07:10:00.000Z",
          "tags": ["買い物", "本"],
          "blocks": [
            {
              "block_id": "block_p_1",
              "type": "paragraph",
              "plain_text": "技術書を1冊買った。",
              "rich_text": [
                {
                  "type": "text",
                  "text": "技術書を1冊買った。",
                  "href": null,
                  "annotations": {
                    "bold": false,
                    "italic": false,
                    "strikethrough": false,
                    "underline": false,
                    "code": false,
                    "color": "default"
                  }
                }
              ]
            }
          ],
          "plain_text": "技術書を1冊買った。"
        }
      ]
    }
  ]
}
```

---

## 5.2 フィールド定義

### `entries`
- 型: array
- 必須
- 日記ページ単位の詳細情報

### `entries[].page_id`
- 型: string
- 必須
- NotionページID
- index cache と対応する

### `entries[].page_name`
- 型: string
- 必須
- Notion上のページ名

### `entries[].entry_date`
- 型: string
- 必須
- 公開上の日付

### `entries[].last_edited_time`
- 型: string
- 必須
- この詳細データが対応するNotion最終更新日時

### `entries[].has_pending_topics`
- 型: boolean
- 必須
- 取得時点で、最終更新から一定時間未満のため詳細キャッシュに含めなかったトピックが存在したか
- `true` の場合、次回実行時は `last_edited_time` が同じでも詳細再取得対象とする

### `entries[].topics`
- 型: array
- 必須
- 当該日記ページから抽出したトピック一覧

---

## 5.3 topic フィールド

### `topics[].topic_id`
- 型: string
- 必須
- 原則として `heading_3` ブロックID
- トピックアンカーの識別子にも利用可能

### `topics[].last_edited_time`
- 型: string
- 必須
- 当該トピック本文に含まれる有効ブロックのうち、最も新しい最終更新日時

### `topics[].title`
- 型: string
- 必須
- 見出し文字列

### `topics[].tags`
- 型: array[string]
- 必須
- `#` から始まる段落行から抽出したタグ一覧
- 見出し中や文中の `#タグ` は抽出対象外
- 存在しない場合は空配列

### `topics[].blocks`
- 型: array
- 必須
- トピック本文を構成するブロック列

### `topics[].plain_text`
- 型: string
- 任意
- トピック本文から抽出したプレーンテキスト
- 検索・抜粋生成用
- 再生成可能な補助データ

---

## 5.4 block フィールド

ブロックはNotionの主要ブロックを、静的サイト生成に必要な範囲で正規化して保持する。

共通フィールド:

```json
{
  "block_id": "block_xxxx",
  "type": "paragraph"
}
```

### 共通項目

#### `block_id`
- 型: string
- 必須
- NotionブロックID

#### `type`
- 型: string
- 必須
- 例:
  - `paragraph`
  - `bulleted_list_item`
  - `numbered_list_item`
  - `to_do`
  - `quote`
  - `callout`
  - `image`
  - `divider`
  - `code`
  - `bookmark`
  - `heading_3`

---

## 5.5 テキスト系ブロック例

```json
{
  "block_id": "block_p_1",
  "type": "paragraph",
  "plain_text": "今日は本を買った。",
  "rich_text": [
    {
      "type": "text",
      "text": "今日は本を買った。",
      "href": null,
      "annotations": {
        "bold": false,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "code": false,
        "color": "default"
      }
    }
  ]
}
```

### `plain_text`
- 型: string
- 任意だが推奨
- ブロック全体の単純テキスト

### `rich_text`
- 型: array
- 任意
- 装飾・リンクを含むテキスト構造

---

## 5.6 リスト系ブロック例

```json
{
  "block_id": "block_li_1",
  "type": "bulleted_list_item",
  "plain_text": "技術書",
  "rich_text": [
    {
      "type": "text",
      "text": "技術書",
      "href": null,
      "annotations": {
        "bold": false,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "code": false,
        "color": "default"
      }
    }
  ]
}
```

必要に応じて将来以下を追加してよい。

- `children`
- `checked` (`to_do` 用)

---

## 5.7 画像ブロック例

```json
{
  "block_id": "block_img_1",
  "type": "image",
  "image": {
    "source_type": "file",
    "url": "https://..."
  }
}
```

### `image.source_type`
- `file` / `external` など

### `image.url`
- 画像URL
- 一時URLの扱いは別途実装ポリシーで定義する

---

## 5.8 コードブロック例

```json
{
  "block_id": "block_code_1",
  "type": "code",
  "plain_text": "print('hello')",
  "code": {
    "language": "python",
    "text": "print('hello')"
  }
}
```

### 空段落の除外

- `type = "paragraph"` かつ本文テキストが空のブロックは保存しない
- 空段落はNotion上で編集過程により増減しやすく、差分通知や更新判定のノイズになるためである

---

## 6. 抽出ルール

### 6.1 トピック区切り

- `heading_3` をトピック開始ブロックとみなす
- 次の `heading_3` 直前までをそのトピック本文とする

### 6.2 タグ抽出

- タグは本文または見出し中の `#タグ` 表記から抽出する
- タグは、`#` から始まる段落行から抽出する
- 保存時は `#` を除いた文字列に正規化してよい
- 同一タグは topic 内で重複除去する
- タグ行そのものは topic の本文ブロック列には含めない

### 6.3 プレーンテキスト生成

- `plain_text` は検索・抜粋用補助データ
- 元となるブロック列から再生成可能であること

### 6.4 編集中トピック

- 最終更新から一定時間未満のトピックは詳細キャッシュに含めない
- その場合は entry 単位で `has_pending_topics = true` を保持する
- `has_pending_topics = true` の entry は、次回実行時に再取得対象とする
- これにより、編集中データの取り込み防止と、後続実行での確実な反映を両立する

---

## 7. 更新ルール

### 7.1 index cache 更新

- Notionデータベース一覧から全件再生成してよい
- ただし entries 単位で既存と比較し、差分判定に利用する

### 7.2 detail cache 更新

- 新規または更新対象ページのみ再取得する
- 非更新ページの詳細は既存キャッシュを再利用する
- 削除ページは detail cache から除外する

### 7.3 一貫性

- `page_id` をキーとして index cache と detail cache を対応づける
- detail cache に存在するページは、原則として index cache にも存在しなければならない

---

## 8. 非採用項目

以下は現時点では採用しない。

### `source_status`
理由:
- 元データから導出できる
- 取得失敗は異常終了とするため、中途半端な状態管理が不要

### `topic.is_public`
理由:
- `#非公開` などのルールから生成時に判定できる
- ルール変更時にキャッシュ更新が不要になる

### 1記事1JSON保存
理由:
- まずは単一ファイルのほうが実装が単純
- 現時点では分割の恩恵より複雑さが勝つ

### 旧 `diary_data.json` 互換
理由:
- 旧形式互換を維持すると、表示都合で平坦化したデータと通知都合で必要な構造化データが混ざる
- 現在は `diary_index.json` / `diary_detail.json` を正とする

### 差分通知の比較単位
- 差分通知は `diary_detail.json` の topic 単位で行う
- 主キーは `topic_id`
- 更新判定は `last_edited_time` の変化による

---

## 9. バージョン管理方針

- JSON構造を変更した場合は `schema_version` を更新する
- 互換性がない場合は旧キャッシュを破棄して再生成する
- キャッシュ移行ロジックは、必要になるまで原則作らない

---

## 10. 想定ファイルサイズと将来方針

現時点では単一JSONで管理するが、将来以下に該当した場合は分割を検討する。

- detail cache のサイズが大きくなりすぎる
- 更新対象の一部書き換えが非効率になる
- diff確認やデバッグが困難になる
- 実行時間やメモリ使用量が問題になる

その場合の候補:

- 日付単位で分割
- ページID単位で分割
- indexは単一、detailのみ分割
