---
name: features-layer-structure
description: featuresパッケージのレイヤー構造（domain/、read/、write/のCQRS構造）
---

# featuresパッケージのレイヤー構造

`packages/features`パッケージはCQRSの考え方を取り入れ、以下の3つのレイヤーディレクトリで構成されています：

- `domain/`: ドメインモデルとビジネスロジック
- `read/`: 取得系（クエリ）処理
- `write/`: 更新系（コマンド）処理

## ディレクトリ構造

各機能（例：`short-url`、`site`）は以下のような構造になります：

```
packages/features/src/{feature-name}/
├── domain/
│   ├── entity/
│   │   └── {entity}.ts        # エンティティの定義とドメインロジック
│   ├── value-object/
│   │   └── {value-object}.ts  # 値オブジェクトの定義
│   └── service/
│       └── {service}.ts       # ドメインサービス
├── read/
│   ├── query/
│   │   └── {query-name}.ts    # 取得系のユースケース（DBなどへの問い合わせも含める）
│   ├── presenter/
│   │   └── {presenter}.ts     # 取得結果をUI向けに変換
│   └── schema/
│       └── index.ts           # 取得用DTO定義
└── write/
    ├── usecase/
    │   └── {usecase-name}.ts  # 更新系ユースケース（コマンド）
    ├── repository/
    │   └── {repository}.ts    # Entity <-> DB永続化
    └── gateway/
        └── {gateway}.ts       # 外部SDKや外部サービス連携
```

### 依存に基づくネスト構造

`{feature-name}`配下は、依存関係を表現するために機能をネストしてよいです。

- 子featureは親featureに依存してよい
- 親featureは子featureに依存しない（一方向依存）
- 同階層feature同士の直接依存は避け、必要なら共通の親featureへ寄せる

例: 「organizationの中にprojectがある」場合

```
packages/features/src/organization/
├── domain/
├── read/
├── write/
└── project/
    ├── domain/
    ├── read/
    └── write/
```

この場合、`organization/project/*` は `organization/*` を参照してよく、`organization/*` から `organization/project/*` は参照しません。

## レイヤーの責務

### domain/

- **型定義**: Valibotスキーマを使用した型定義（`v.object()`, `v.pipe()`など）
- **値オブジェクト**: `v.brand()`を使用して型安全な値オブジェクトを定義
- **ドメインロジック**: 純粋関数として実装（例：`constructSite`, `updateName`, `updateUrl`）
- **ドメインサービス**: 複数エンティティ/値オブジェクトにまたがるドメインルールを表現
- **バリデーション**: Valibotスキーマによるバリデーション
- **エンコード/デコード**: IDのエンコード/デコード関数（例：`encodeSiteId`, `decodeShortUrlId`）
- **エラーハンドリング**: `TaggedError`を使用したエラー返却
- **外部依存を持たない**: Prismaクライアントや外部APIに依存しない

### read/

- **query/**: DBなどからの取得処理を実装する
- **presenter/**: 取得結果をUIが必要とする形へ整形する
- **schema/**: 取得専用DTO（レスポンススキーマ）を定義する
- **責務の分離**: 取得系では状態変更を行わない

### write/

- **usecase/**: 更新系ユースケース（コマンド）を実装する
- **repository/**: Entityの永続化と復元（Entity -> DB、DB -> Entity）を担当する
- **gateway/**: 外部SDKや外部サービス連携を抽象化する
- **エラーハンドリング**: `TaggedError`を使用してエラーを返す
- **トランザクションの境界**: 必要に応じてwrite側で管理する

## 依存関係

- `read` → `domain`（必要な型や値オブジェクトを参照）
- `write/usecase` → `domain`, `write/repository`, `write/gateway`
- `write/repository` → `domain`
- `write/gateway` → 外部SDK
- `domain` → 依存なし（他のfeaturesパッケージのdomainは参照可能）
- ネストfeatureの依存方向: `親/子` は `親` へ依存可能、`親` は `親/子` に依存不可

## 実装例

### 値オブジェクトの実装（valibotのbrandを使用）

値オブジェクトは`v.pipe()`と`v.brand()`を使用して型安全に実装します。

#### ID値オブジェクトの例

```typescript
// domain/value-object/site-id.ts
import * as v from "valibot";
import { TaggedError } from "@nakanoaas/tagged-error";

// 基本のIDスキーマ（brandで型を区別）
export const SiteIdSchema = v.pipe(v.string(), v.uuid(), v.brand("SiteId"));
export type SiteId = v.InferOutput<typeof SiteIdSchema>;

// エンコードされたIDスキーマ（URL用など）
export const EncodedSiteIdSchema = v.pipe(
  v.string(),
  v.check(isUuid58),
  v.brand("EncodedSiteId"),
);
export type EncodedSiteId = v.InferOutput<typeof EncodedSiteIdSchema>;

// パース関数（文字列から値オブジェクトへの変換）
export function parseSiteId(
  value: string | EncodedSiteId,
):
  | SiteId
  | TaggedError<"INVALID_SITE_ID", unknown>
  | TaggedError<"INVALID_ENCODED_SITE_ID", unknown> {
  if (value.length === 22) {
    // エンコードされたIDのデコード
    const result = uuid58DecodeSafe(value);
    if (result instanceof Error) {
      return new TaggedError("INVALID_ENCODED_SITE_ID", {
        message: "不正なエンコードされたサイトIDです",
        cause: result,
      });
    }
    return result as SiteId;
  }

  // UUID形式のパース
  const result = v.safeParse(SiteIdSchema, value);
  if (!result.success) {
    return new TaggedError("INVALID_SITE_ID", {
      message: "不正なサイトIDです",
      cause: result,
    });
  }
  return result.output;
}

// エンコード関数
export function encodeSiteId(siteId: SiteId): EncodedSiteId {
  return uuid58Encode(siteId) as EncodedSiteId;
}

// 生成関数
export function generateSiteId(): SiteId {
  return generateUuid() as SiteId;
}
```

#### 数値型のID値オブジェクトの例

```typescript
// domain/value-object/id.ts (short-url)
import * as v from "valibot";

// 数値型のID（brandで型を区別）
export const ShortUrlIdSchema = v.pipe(
  v.number(),
  v.minValue(0),
  v.integer(),
  v.brand("ShortUrlId"),
);
export type ShortUrlId = v.InferOutput<typeof ShortUrlIdSchema>;

// エンコードされたID
export const EncodedShortUrlIdSchema = v.pipe(
  v.string(),
  v.regex(/^[1-9A-HJ-NP-Za-km-z]+$/),
  v.brand("EncodedShortUrlId"),
);
export type EncodedShortUrlId = v.InferOutput<typeof EncodedShortUrlIdSchema>;

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
// domain/value-object/year-month.ts
import * as v from "valibot";

// 年月を表す値オブジェクト（brandなしでも可）
export const YearMonthSchema = v.pipe(
  v.string(),
  v.regex(/^\d{4}-\d{2}$/, "YYYY-MM形式である必要があります"),
);
export type YearMonth = v.InferOutput<typeof YearMonthSchema>;

// より複雑な値オブジェクト（brandを使用）
export const ColorCodeSchema = v.pipe(
  v.string(),
  v.regex(/^#([0-9a-fA-F]{6})$/),
  v.brand("ColorCode"),
);
export type ColorCode = v.InferOutput<typeof ColorCodeSchema>;
```

### エンティティの例

```typescript
// domain/entity/site.ts
import * as v from "valibot";
import { TaggedError } from "@nakanoaas/tagged-error";

export const SiteSchema = v.object({
  id: SiteIdSchema,
  organizationId: OrganizationIdSchema,
  name: v.string(),
  lpUrl: v.pipe(v.string(), v.url()),
  createdAt: v.date(),
  updatedAt: v.date(),
});

export type Site = v.InferOutput<typeof SiteSchema>;

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
  });
  if (!result.success) {
    return new TaggedError("INVALID_SITE", {
      message: "不正なサイトです",
      cause: result.issues,
    });
  }
  return result.output;
}
```

### write/repository/の例

```typescript
// write/repository/site-repository.ts
import { client } from "@repo/schema/src/client"
import { SiteSchema } from "../../domain/entity/site"

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

### write/usecase/の例

```typescript
// write/usecase/update-site-name.ts
import { updateName } from "../../domain/entity/site"
import * as repository from "../repository/site-repository"

export async function updateSiteNameUsecase(
  orgId: OrganizationId,
  siteId: SiteId,
  name: string,
) {
  const site = await repository.findSiteById(orgId, siteId)
  if (site === null || site instanceof TaggedError) {
    return new TaggedError("NOT_FOUND_SITE", { ... })
  }

  const newSite = updateName(site, name)
  if (newSite instanceof TaggedError) {
    return new TaggedError("INVALID_SITE", { ... })
  }

  await repository.saveSite(newSite)
  return
}
```

### read/query + presenter/の例

```typescript
// read/query/find-site-detail.ts
import { client } from "@repo/schema/src/client";
import { presentSiteDetail } from "../presenter/site-detail-presenter";
import { type SiteDetailDto } from "../schema/site-detail-dto";

export async function findSiteDetailQuery(
  siteId: SiteId,
): Promise<
  SiteDetailDto | TaggedError<"INVALID_SITE_DETAIL_DTO", unknown> | null
> {
  const row = await client.site.findUnique({ where: { id: siteId } });
  if (!row) return null;

  const dto = presentSiteDetail(row);
  if (dto instanceof TaggedError) {
    return dto;
  }
  return dto;
}
```

## ベストプラクティス

1. **CQRSの責務分離を守る**: read（取得）とwrite（更新）を明確に分離する
2. **型安全性**: Valibotスキーマを使用して型安全性を確保する
3. **値オブジェクトの実装**:
   - `v.brand()`を使用してプリミティブ型を区別する（例：`SiteId`と`OrganizationId`を区別）
   - ID値オブジェクトには`parse*`関数を提供して、文字列からの変換を型安全に行う
   - URL用などには`Encoded*`型と`encode*`/`decode*`関数を提供する
4. **エラーハンドリング**: `TaggedError`を使用してエラーを型安全に扱う
5. **純粋関数**: `domain/`の関数は純粋関数として実装する
6. **ユースケースの分割**: `write/usecase/`の各ユースケースは個別ファイルに分ける
7. **DTOの明示**: `read/schema/`で取得用DTOを定義し、レスポンス整形を一元化する
8. **永続化の責務**: 永続化ロジックは`write/repository/`に集約する
