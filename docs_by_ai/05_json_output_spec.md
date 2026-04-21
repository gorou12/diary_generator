# 05. JSON出力仕様

この文書は現行コードの挙動を説明するものであり、仕様の正本ではない。
仕様の変更や判断は docs/ 配下の文書を優先する。

`output/json/` にはフロントエンド参照用JSONを出力する。

## 1. `search_data.json`

## 目的

- 検索ページ `/search.html` の全文検索インデックス

## 生成単位

- `DiaryEntry` 内の各 `Topic` ごとに1レコード

## スキーマ

```json
[
  {
    "date": "YYYY-MM-DD",
    "title": "トピック名",
    "content": "本文結合文字列 #tag1 #tag2",
    "url": "dates/YYYY-MM-DD.html"
  }
]
```

## 備考

- `content` は表示HTMLではなくプレーンな結合文字列
- クライアント側で `title + content` の部分一致検索を行う

## 2. `calendar_data.json`

## 目的

- 全ページ共通サイドバーの月別カレンダー表示

## スキーマ

```json
{
  "available_months": ["YYYY-MM", "YYYY-MM"],
  "calendars": {
    "YYYY-MM": "<table>...</table>"
  }
}
```

## `calendars[month]` の内容

- 1か月分のHTML文字列
- 日記が存在する日付には `/dates/YYYY-MM-DD.html` へのリンクを付与
- 日付セルにトピック数密度クラスを付与
  - `density-1`: 1〜2件
  - `density-2`: 3〜5件
  - `density-3`: 6件以上

## データ順

- `available_months` は昇順（古い月 -> 新しい月）
- 初期表示月はページ側の `initial_month` が優先、なければ最新月
