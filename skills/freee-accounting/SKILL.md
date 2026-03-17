---
name: freee-accounting
description: Uses freee MCP to access and manage freee accounting, invoicing, HR, and sales data. Triggers when the user mentions 営業利益, 売上, 損益, 取引, 請求書, 見積書, 経費, freee, 会計, 取引先, 試算表.
---

# freee 会計・経営 MCP

## When to Use

ユーザーが以下のような発言をしたとき、freee MCP を使用する:

- **会計・集計**: 「営業利益」「売上」「損益」「試算表」「今期の業績」「freeeで〇〇を確認して」
- **取引**: 「取引一覧」「取引を登録」「経費申請」
- **請求**: 「請求書」「請求書一覧」「請求書を作成」「先月の請求書」
- **見積**: 「見積書」「見積書一覧」「見積書を作成」「見積書を発行」
- **マスタ**: 「取引先」「勘定科目」「部門」
- **人事労務**: 従業員、勤怠、給与（freee 人事労務API対応時）
- **汎用**: 「freee」「freee MCP」

## 前提

- 公式 freee MCP (`freee-mcp` npm パッケージ) が Cursor の mcp.json に設定されていること
- ユーザーが `npx freee-mcp configure` で初回認証を完了していること
- 請求書・見積書を使う場合は **[freee請求書] 見積書・請求書・納品書** の権限が必要

---

## 見積書作成の対話フロー（一問一答）

見積書を新規作成するときは、**一問一答形式で順番に質問**し、回答を得てから次に進む。

| 順 | 項目 | 質問例 | 備考 |
|----|------|--------|------|
| 1 | **取引先** | 「取引先はどちらですか？（社名や既存見積の取引先名でOK）」 | 既存見積一覧から partner_id を特定。不明なら候補を提示して選んでもらう |
| 2 | **件名** | 「件名はどうしますか？」 | 例: 「〇〇制作のお見積り」「円陣」など |
| 3 | **有効期限** | 「有効期限はいつにしますか？（YYYY-MM-DD、または「なし」）」 | 空の場合は null |
| 4 | **明細** | 「要件・仕様・機能・工数を整理したファイルを共有してもらえますか？」 | ユーザーが提供したファイル（要件書・仕様書・工数表など）を読み込み、そこから明細（費目・工数・単価）を抽出 |
| 5 | **枝番号**（任意） | 「枝番号を付けますか？（改訂版の場合など）」 | 通常は省略 |

**取引先が存在しない場合**: **取引先を先に登録**してから見積書を作成する。詳細は「取引先が存在しない場合のフロー」を参照。

**作成前の最終確認**: 見積書を **作成** する前には、入力内容の **最終確認** を必ず行う。

---

## 取引先登録に必要な情報

| 項目 | 必須 | 説明 | 対話で聞くタイミング |
|------|------|------|----------------------|
| **取引先名（社名）** | ✓ | 正式名称 | 最初に必ず聞く |
| **敬称** | △ | 御中で統一。聞かない | 固定で「御中」 |
| **住所** | ✓ | 都道府県・市区町村・町域・番地など。郵便番号は住所から逆引き | 社名のあとに必ず聞く |
| **インボイス番号（法人番号）** | ✓ | 適格請求書発行事業者の登録番号。法人は13桁、個人事業主は T+13桁 | 住所のあとに必ず聞く |

---

## 取引先が存在しない場合のフロー

**チャット形式で1項目ずつ聞く**: **1問1答で順番に**情報を集める。

| 順 | 質問例 | 回答例 |
|----|--------|--------|
| 1 | 会社名は？ | 株式会社テスト |
| 2 | 住所は？（都道府県から番地まで） | 福岡県福岡市中央区天神4-7-6 |
| 3 | インボイス番号（法人番号）は？ | 1234567890123 |

※敬称は聞かず、御中で統一する。

1. **確認**: 既存見積一覧（`/quotations`）と会計取引先（`/api/1/partners`）の両方で検索し、該当取引先がないことを確認する。
2. **対話**: 「取引先が見つかりませんでした。新規登録してから見積書を作成します。」→ 上記の順で**1項目ずつ**質問し、回答を得てから次に進む。
3. **郵便番号の逆引き**: 住所が得られたら `scripts/zipcode_from_address.py "<住所>"` を実行して郵便番号を取得。取得できない場合はユーザーに郵便番号を確認する。
   - ※スクリプトは本スキルに同梱（`skills/freee-accounting/scripts/zipcode_from_address.py`）。プロジェクトの `scripts/` にコピーして使用する。
4. **取引先登録（API）**: `freee_api_post` で会計APIの取引先を作成する。
   - service: `"accounting"`
   - path: `"/api/1/partners"`
   - body 例: `{ "company_id": <company_id>, "name": "<取引先名>", "country_code": "JP", "default_title": "御中", "invoice_registration_number": "<インボイス番号>", "address_attributes": { "zipcode": "<逆引きで取得した7桁>", "prefecture_code": <1-47>, "street_name1": "<住所1>", "street_name2": "<住所2>" } }`
   - ※`invoice_registration_number` が効かない場合は `long_name` を試す
5. **partner_id 取得**: レスポンスの `partner.id` を `partner_id` として控える。
6. **見積書作成を続行**: 件名以降の対話に進み、取得した `partner_id` で見積書を作成する。

---

## 見積書作成のAPI手順

### Step 1: 事業所IDの確認

```
freee_get_current_company
```

### Step 2: テンプレートIDの取得

```
freee_api_get
  service: "invoice"
  path: "/quotations/templates"
  query: { "company_id": <company_id> }
```

### Step 3: 取引先の特定

既存見積書または会計取引先から `partner_id` を取得。未登録の場合は上記フローで先に登録。

### Step 4: 見積書 body の組み立て

```json
{
  "company_id": <company_id>,
  "partner_id": <partner_id>,
  "partner_title": "御中",
  "subject": "〇〇開発のお見積り",
  "quotation_date": "YYYY-MM-DD",
  "expiration_date": "YYYY-MM-DD",
  "template_id": <template_id>,
  "tax_entry_method": "out",
  "tax_fraction": "omit",
  "withholding_tax_entry_method": "out",
  "lines": [
    {
      "type": "item",
      "description": "1. 開発費用",
      "unit": "人日",
      "quantity": 10,
      "unit_price": "60000",
      "tax_rate": 10
    }
  ]
}
```

### Step 5: 見積書作成（POST）

```
freee_api_post
  service: "invoice"
  path: "/quotations"
  body: <上記JSON>
```

**重要**: invoice サービスは `company_id` が自動付与されない。body に必ず `company_id` を含める。

---

## 利用可能なツール

| ツール | 用途 |
|-------|------|
| `freee_get_current_company` | 現在の事業所 |
| `freee_api_get` | データ取得 |
| `freee_api_post` | 新規作成 |
| `freee_api_put` | 更新 |

### 主要 API パス

| 用途 | service | パス |
|------|---------|------|
| 見積書 | invoice | `/quotations`, `/quotations/{id}` |
| 見積書テンプレート | invoice | `/quotations/templates` |
| 取引先 | accounting | `/api/1/partners` |
| 損益計算書 | accounting | `/api/1/reports/trial_pl` |

---

## 参考

- [freee MCP GitHub](https://github.com/freee/freee-mcp)
- [freee API ドキュメント](https://developer.freee.co.jp/docs)
