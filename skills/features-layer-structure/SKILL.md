---
name: features-layer-structure
description: featuresパッケージのレイヤー構造（domain/、repo/、usecase/の3層構造）
---

# featuresパッケージのレイヤー構造

`packages/features`パッケージは以下の3つのレイヤーディレクトリで構成されています：

- `domain/`: ドメインモデルとビジネスロジック
- `repo/`: データアクセス層
- `usecase/`: ユースケース層

## ディレクトリ構造

各機能（例：`short-url`、`site`）は以下のような構造になります：

```
packages/features/src/{feature-name}/
├── domain/
│   ├── index.ts          # 型定義とスキーマのエクスポート
│   ├── {entity}.ts       # エンティティの定義とドメインロジック
│   └── {value-object}.ts # 値オブジェクトの定義
├── repo/
│   └── index.ts          # データアクセス関数
└── usecase/
    ├── index.ts          # 共通ユースケース
    └── {usecase-name}.ts # 個別ユースケース（各ファイルが1つのユースケース）
```

## レイヤーの責務

### domain/

- **型定義**: Valibotスキーマを使用した型定義（`v.object()`, `v.pipe()`など）
- **値オブジェクト**: `v.brand()`を使用して型安全な値オブジェクトを定義
- **ドメインロジック**: 純粋関数として実装（例：`constructSite`, `updateName`, `updateUrl`）
- **バリデーション**: Valibotスキーマによるバリデーション
- **エンコード/デコード**: IDのエンコード/デコード関数（例：`encodeSiteId`, `decodeShortUrlId`）
- **エラーハンドリング**: `TaggedError`を使用したエラー返却
- **外部依存を持たない**: Prismaクライアントや外部APIに依存しない

### repo/

- **データベースアクセス**: Prismaクライアント（`@repo/schema/src/client`）を使用
- **データ取得**: `find*`関数でデータを取得し、Valibotスキーマで検証して返す
- **データ保存**: `create`, `update`などの関数でデータを保存
- **エラーハンドリング**: データベースエラーやバリデーションエラーを`TaggedError`で返す
- **型変換**: データベースの型をドメイン型に変換

### usecase/

- **ユースケースの実装**: 各ユースケースごとにファイルを分ける（例：`update-site-name.ts`）
- **エラーハンドリング**: `TaggedError`を使用してエラーを返す
- **ドメインロジックとデータアクセスの調整**: `repo`と`domain`を組み合わせてユースケースを実現
- **トランザクションの境界**: 必要に応じてトランザクション管理を行う
- **`index.ts`**: 共通のユースケース（例：`createSiteUsecase`）を定義

## 依存関係

- `usecase` → `repo`, `domain`
- `repo` → `domain`
- `domain` → 依存なし（他のfeaturesパッケージのdomainは参照可能）

## 実装例

### 値オブジェクトの実装（valibotのbrandを使用）

値オブジェクトは`v.pipe()`と`v.brand()`を使用して型安全に実装します。

#### ID値オブジェクトの例

```typescript
// domain/site-id.ts
import * as v from "valibot"
import { TaggedError } from "@nakanoaas/tagged-error"

// 基本のIDスキーマ（brandで型を区別）
export const SiteIdSchema = v.pipe(
  v.string(),
  v.uuid(),
  v.brand("SiteId")
)
export type SiteId = v.InferOutput<typeof SiteIdSchema>

// エンコードされたIDスキーマ（URL用など）
export const EncodedSiteIdSchema = v.pipe(
  v.string(),
  v.check(isUuid58),
  v.brand("EncodedSiteId")
)
export type EncodedSiteId = v.InferOutput<typeof EncodedSiteIdSchema>

// パース関数（文字列から値オブジェクトへの変換）
export function parseSiteId(
  value: string | EncodedSiteId,
): SiteId | TaggedError<"INVALID_SITE_ID", unknown> | TaggedError<"INVALID_ENCODED_SITE_ID", unknown> {
  if (value.length === 22) {
    // エンコードされたIDのデコード
    const result = uuid58DecodeSafe(value)
    if (result instanceof Error) {
      return new TaggedError("INVALID_ENCODED_SITE_ID", {
        message: "不正なエンコードされたサイトIDです",
        cause: result,
      })
    }
    return result as SiteId
  }

  // UUID形式のパース
  const result = v.safeParse(SiteIdSchema, value)
  if (!result.success) {
    return new TaggedError("INVALID_SITE_ID", {
      message: "不正なサイトIDです",
      cause: result,
    })
  }
  return result.output
}

// エンコード関数
export function encodeSiteId(siteId: SiteId): EncodedSiteId {
  return uuid58Encode(siteId) as EncodedSiteId
}

// 生成関数
export function generateSiteId(): SiteId {
  return generateUuid() as SiteId
}
```

#### 数値型のID値オブジェクトの例

```typescript
// domain/id.ts (short-url)
import * as v from "valibot"

// 数値型のID（brandで型を区別）
export const ShortUrlIdSchema = v.pipe(
  v.number(),
  v.minValue(0),
  v.integer(),
  v.brand("ShortUrlId")
)
export type ShortUrlId = v.InferOutput<typeof ShortUrlIdSchema>

// エンコードされたID
export const EncodedShortUrlIdSchema = v.pipe(
  v.string(),
  v.regex(/^[1-9A-HJ-NP-Za-km-z]+$/),
  v.brand("EncodedShortUrlId")
)
export type EncodedShortUrlId = v.InferOutput<typeof EncodedShortUrlIdSchema>

// エンコード/デコード関数
export function encodeShortUrlId(num: ShortUrlId): EncodedShortUrlId | Error {
  // Base58エンコードの実装
}

export function decodeShortUrlId(
  encoded: EncodedShortUrlId,
): ShortUrlId | Error {
  // Base58デコードの実装
}
```

#### シンプルな値オブジェクトの例

```typescript
// domain/year-month.ts
import * as v from "valibot"

// 年月を表す値オブジェクト（brandなしでも可）
export const YearMonthSchema = v.pipe(
  v.string(),
  v.regex(/^\d{4}-\d{2}$/, "YYYY-MM形式である必要があります"),
)
export type YearMonth = v.InferOutput<typeof YearMonthSchema>

// より複雑な値オブジェクト（brandを使用）
export const ColorCodeSchema = v.pipe(
  v.string(),
  v.regex(/^#([0-9a-fA-F]{6})$/),
  v.brand("ColorCode")
)
export type ColorCode = v.InferOutput<typeof ColorCodeSchema>
```

### エンティティの例

```typescript
// domain/site.ts
import * as v from "valibot"
import { TaggedError } from "@nakanoaas/tagged-error"

export const SiteSchema = v.object({
  id: SiteIdSchema,
  organizationId: OrganizationIdSchema,
  name: v.string(),
  lpUrl: v.pipe(v.string(), v.url()),
  createdAt: v.date(),
  updatedAt: v.date(),
})

export type Site = v.InferOutput<typeof SiteSchema>

export function constructSite(
  orgId: string,
  name: string,
  lpUrl: string,
): Site | TaggedError<"INVALID_SITE", unknown> {
  const result = v.safeParse(SiteSchema, {
    id: generateSiteId(),
    organizationId: orgId,
    name: name,
    lpUrl: lpUrl,
    createdAt: new Date(),
    updatedAt: new Date(),
  })
  if (!result.success) {
    return new TaggedError("INVALID_SITE", {
      message: "不正なサイトです",
      cause: result.issues,
    })
  }
  return result.output
}
```

### repo/の例

```typescript
// repo/index.ts
import { client } from "@repo/schema/src/client"
import { SiteSchema } from "../domain/site"

export async function findSiteById(
  orgId: OrganizationId,
  siteId: SiteId,
): Promise<Site | TaggedError<"INVALID_SITE", unknown> | null> {
  const site = await client.site.findUnique({
    where: { id: siteId, organizationId: orgId },
  })

  if (!site) return null

  const result = v.safeParse(SiteSchema, site)
  if (!result.success) {
    return new TaggedError("INVALID_SITE", { ... })
  }
  return result.output
}
```

### usecase/の例

```typescript
// usecase/update-site-name.ts
import { updateName } from "../domain/site"
import * as repo from "../repo"

export async function updateSiteNameUsecase(
  orgId: OrganizationId,
  siteId: SiteId,
  name: string,
) {
  const site = await repo.findSiteById(orgId, siteId)
  if (site === null || site instanceof Error) {
    return new TaggedError("NOT_FOUND_SITE", { ... })
  }

  const newSite = updateName(site, name)
  if (newSite instanceof Error) {
    return new TaggedError("INVALID_SITE", { ... })
  }

  await repo.saveSite(newSite)
  return
}
```

## ベストプラクティス

1. **各レイヤーの責務を明確に分離する**: レイヤー間の依存関係を守る
2. **型安全性**: Valibotスキーマを使用して型安全性を確保する
3. **値オブジェクトの実装**:
   - `v.brand()`を使用してプリミティブ型を区別する（例：`SiteId`と`OrganizationId`を区別）
   - ID値オブジェクトには`parse*`関数を提供して、文字列からの変換を型安全に行う
   - URL用などには`Encoded*`型と`encode*`/`decode*`関数を提供する
4. **エラーハンドリング**: `TaggedError`を使用してエラーを型安全に扱う
5. **純粋関数**: `domain/`の関数は純粋関数として実装する
6. **ユースケースの分割**: 各ユースケースは個別のファイルに分ける
7. **バリデーション**: `repo/`でデータベースから取得したデータをValibotスキーマで検証する
