# Notion Schema (Diary DB)

## Database Properties
- 日付（date）: `YYYY-MM-DD`
- 公開（checkbox）: true のページのみ対象
- 収集対象（select）: index / noindex / auto（現状の運用）
- （他にあれば追記）

## Page Structure (Blocks)
- 見出し3（heading_3）: トピックの開始
- 段落: トピック本文
- 画像（image）: 画像タグとして本文に埋め込む
- ハッシュタグ: `#...` から始まる行はタグとして抽出し本文に含めない
  - `#非公開` を含むトピックは出力しない

## Special Rules / Edge Cases
- 見出しが連続する場合の扱い:
- 空見出し:
- 同一トピック名が複数日に存在:
- ブロック編集直後の取り扱い（例: 5分経過で対象）:
