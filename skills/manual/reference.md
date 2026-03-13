# Notion マニュアルDB 参照

マニュアル用データベースの **data_source_id** と **データソースURL** を定義する。**Notion** の各ツールでこの ID を参照してアクセスする。  
利用前に、このファイル内の値を Notion のマニュアル用DBに合わせて設定すること。

## マニュアルDB

| 項目 | 値 |
|------|-----|
| data_source_id | （未設定） |
| データソースURL | （未設定） |

- **notion-create-pages**: `parent` に `{ "data_source_id": "<上記の data_source_id>" }` を指定
- **notion-search**: `data_source_url` に `collection://<data_source_id>` を指定してマニュアルDB内に絞る

## DB プロパティ

- **ステータス**（必須）: `下書き` | `公開` | `アーカイブ`。新規作成・更新時に properties で指定する。
- その他（タイトル・カテゴリ等）は Notion 上で確認し、作成・更新時に必要に応じて properties に指定する。
