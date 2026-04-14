# NotionデータローカルキャッシュJSON データ仕様

## データベースキャッシュJSON

Notionの日記データベースの各ページメタ情報を保持し、APIの結果と突き合わせてページ取得・再取得が必要かどうかの判断に用いる。

### データ構造

```json
{
  "version": 1,
  "database": {
    "source": "Notion",
    "notion_database_id": "167fdbfc-0161-8013-8e5e-cbe200e6ad8c"
  },
  "sync": {
    "last_full_query_at": "2026-04-08T23:10:00+09:00",
    "last_success_at": "2026-04-08T23:10:12+09:00"
  },
  "pages": {
    "2d0fdbfc-0161-8023-a85f-ff90e85ec76d": {
      "page_id": "2d0fdbfc-0161-8023-a85f-ff90e85ec76d",
      "title": "20251222",
      "date": "2025-12-22",
      "published": true,
      "index_direction": "auto",
      "created_time": "2025-12-21T20:50:00.000Z",
      "last_edited_time": "2025-12-22T14:41:00.000Z",
      "content_cache_path": "cache/pages/2d0fdbfc-0161-8023-a85f-ff90e85ec76d.json",
      "content_last_synced_at": "2026-04-08T23:10:05+09:00",
      "status": "active"
    }
  }
}
```

トップレベル要素について

- version (数値)
  - データバージョン
  - 1 とする
- database (オブジェクト)
  - 取得したデータベースのメタデータを保存
- sync (オブジェクト)
  - 取得状況を保存
- property_map (オブジェクト)
  - データベース上のプロパティ名とプログラム内の名前の対応表
- pages (オブジェクト)
  - 各ページのメタデータを保存

databaseオブジェクトについて

- source (文字列)
  - データ取得元
  - "Notion" とする
- notion_database_id (文字列)
  - 取得したデータベースのオブジェクトID

syncオブジェクトについて

- last_full_query_at (文字列)
  - 最後にクエリを実行した日時を記録
- last_success_at (文字列)
  - 最後にクエリ取得・JSON保存処理が成功した日時を記録

pagesオブジェクトについて

- (id) (オブジェクト)
  - 当該ページの情報
  - オブジェクトキーとして使うidはpage_id

page_idオブジェクトについて

- page_id (文字列)
  - 当該ページのpage_id
- title (文字列)
  - 当該ページの[title].plain_text
- date (文字列)
  - 当該ページの[date].start
- published (真偽)
  - 当該ページの[publish].checkbox
- index_direction (文字列)
  - 当該ページの[index_direction].select.name
- created_time (文字列)
  - 当該ページのcreated_time
- last_edited_time (文字列)
  - 当該ページのlast_edited_time
- content_cache_path (文字列)
  - 当該ページをキャッシュしたJSONの保存先パス
- content_last_synced_at (文字列)
  - 当該ページを最後に更新した日時
- status (文字列)
  - 当該ページの管理用状態

### 利用方法

- データベース取得APIの結果で pages を更新する
- キャッシュに存在しないがAPIレスポンスに存在するページは新規ページとして pages に追加する
- last_edited_time がキャッシュと異なるページ、および実行時刻から一定時間（別途定義）のページは変更ページとして pages の内容を更新する
    - いずれも後述のページキャッシュを生成・再生成する
- キャッシュに存在するがAPIレスポンスに存在しないページは削除ページとして pages.[page_id].status を更新する（別途提議）


## ページキャッシュJSON

Notionの各ページのブロック情報を保持し、日記各ページのレンダリングを効率化する。

### データ構造

```json
{
  "version": 2,
  "page": {
    "page_id": "339fdbfc-0161-807d-a855-ee091bd0da75",
    "source": "Notion",
    "date": "2026-04-05",
    "title": "20260405",
    "last_edited_time": "2026-04-06T17:53:00.000Z",
    "index_direction": "auto"
  },
  "topics": [
    {
      "topic_id": "339fdbfc-0161-802c-9721-e796457d9279",
      "title": "作業用サンプル",
      "hashtags": ["非公開"],
      "last_edited_time": "2026-04-06T17:53:00.000Z",
      "blocks": []
    }
  ]
}
```

トップレベル要素について

- version (数値)
  - データバージョン
  - 2 とする
- page (オブジェクト)
  - 取得したページのメタ情報を保存
- topics (リスト(オブジェクト))
  - 取得したトピックを出現順にリストにする


pageオブジェクトについて

- page_id (文字列)
  - 当該ページのpage_id
- source (文字列)
  - データ取得元
  - "Notion" とする
- date (文字列)
  - 当該ページの[date].start
  - データベースと同じ値を格納する
- title (文字列)
  - 当該ページの[title].plain_text
  - データベースと同じ値を格納する
- last_edited_time (文字列)
  - 当該ページのlast_edited_time
  - データベースと同じ値を格納する
- index_direction (文字列)
  - 当該ページの[index_direction].select.name
  - データベースと同じ値を格納する


topicsリストのオブジェクトについて

- topic_id (文字列)
  - トピックのID
  - 現時点では、見出しブロックのNotionブロックID
- title (文字列)
  - タイトル
- hashtags (リスト(文字列))
  - ハッシュタグ
- last_edited_time (文字列)
  - トピックの最終編集日時
- blocks (リスト(オブジェクト))
  - トピックの本文になりうるブロック
  - 上から出現順に並べる

blocksリストのオブジェクトについては後述


### 利用方法

- データベースでpublished=falseが設定されているページは、ページキャッシュを生成しない

