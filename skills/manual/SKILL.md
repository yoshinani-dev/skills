---
name: manual
description: マニュアル・手順書の検索・新規作成・更新を行う。実装では Notion のマニュアル用データベースを利用する。マニュアルを探す、手順書を追加する、既存マニュアルを更新する際に利用。トリガー: マニュアル検索、マニュアル作成、手順書を追加、マニュアル更新、手順書を直す。
---

# マニュアル操作

マニュアルの検索・新規作成・更新は **Notion** を利用して行う（MCP サーバー識別子: `Notion`）。マニュアル用DBへの操作はすべて **Notion** のツールで行う。

マニュアルは Notion 上に1つのデータベース（DB）で管理する。その DB の **data_source_id** とデータソースURL（`collection://<data_source_id>`）は [reference.md](reference.md) に定義し、**Notion** のツールでその ID を参照してアクセスする。マニュアルDBには **ステータス** プロパティがあり、値は **下書き** | **公開** | **アーカイブ** のいずれか。新規作成・更新時は properties でステータスを指定する。

**利用前に設定が必要**: このスキルを使う前に、[reference.md](reference.md) の **data_source_id** と **データソースURL** を、利用する Notion のマニュアル用DBの値に設定すること。未設定のままではマニュアルDBへの操作が行えない。

## 参照の読み方

操作前に [reference.md](reference.md) を読み、マニュアルDBの **data_source_id** と **データソースURL**（`collection://<data_source_id>`）が設定されているか確認する。未設定の場合は利用者に設定を依頼する。

## ワークフロー

### マニュアルを新規作成

1. [reference.md](reference.md) の data_source_id を取得
2. **Notion** の `notion-create-pages` を実行  
   - `parent`: `{ "data_source_id": "<reference の値>" }`  
   - `pages`: properties にタイトルと **ステータス**（`下書き` / `公開` / `アーカイブ`）を指定。例: `{ "properties": { "title": "マニュアルタイトル", "ステータス": "下書き" }, "content": "本文" }`
3. 作成されたページの URL を返す

### 既存マニュアルの更新

1. [reference.md](reference.md) の data_source_url を取得
2. **Notion** の `notion-search` で該当ページを検索  
   - `data_source_url`: `collection://<data_source_id>`  
   - `query`: 機能名・画面名・手順名など
3. `notion-fetch` でページ内容を取得
4. `notion-update-page` で更新（`replace_content` / `replace_content_range` / `insert_content_after` のいずれか）
5. 更新した旨と URL を返す

### マニュアルの検索・参照

1. [reference.md](reference.md) の data_source_url を取得
2. **Notion** の `notion-search` でマニュアルDB内を検索  
   - `data_source_url`: `collection://<data_source_id>`  
   - `query`: キーワード
3. ヒットしたページを `notion-fetch` で取得し、要点を要約して提示。必要なら URL を渡す

## 利用ツール（Notion）

マニュアルDBへの操作は **Notion** の以下のツールを用いる。ツール呼び出し時はサーバーに **`Notion`** を指定する。マニュアルDBのステータス（`下書き` | `公開` | `アーカイブ`）は、新規作成・更新時に properties で指定する。

| 操作 | ツール | 主なパラメータ |
|------|--------|----------------|
| DB内検索 | `notion-search` | data_source_url, query |
| ページ取得 | `notion-fetch` | id（ページURLまたはUUID） |
| 新規作成 | `notion-create-pages` | parent（data_source_id）, pages |
| 更新 | `notion-update-page` | data（page_id, command, 本文など） |

## 本文フォーマット（Notion Markdown）

- 見出し: `#`, `##`
- 手順: 番号リスト or `- [ ]` チェックリスト
- コード: コードブロック
- 注意: `<callout type="warning">...</callout>`
- リンク: `[テキスト](url)`
