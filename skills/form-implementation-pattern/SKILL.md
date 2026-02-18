---
name: form-implementation-pattern
description: React Hook Form + Valibotを使用したフォームコンポーネントを実装する。Controller、Fieldコンポーネント、Card、FormProviderを使用した標準的なフォームパターン。Container/Presentationalパターンと統合して、Server Actionsを使用したデータ送信を行う。新規フォーム作成時や既存フォームのリファクタリング時に使用する。
---

# フォーム実装パターン

React Hook Form + Valibot / `useActionState` の両方に対応したフォーム実装ガイド。共通部分を先に整理し、必要な差分だけを後半に記載する。

## 使い分け

- **React Hook Form + Valibot**: 複雑なバリデーションが必要、編集フォーム、入力項目が多い
- **useActionState**: シンプルな送信、削除確認、バリデーション不要

## 共通設計

### コンポーネント構成

1. **コンテナ**（`ComponentName`）: `component-name/index.tsx`
   - `Suspense`でラップし、`fallback`にSkeleton
   - データ取得関数で`Promise`を作成し、プレゼンテーションに渡す
2. **プレゼンテーション**（`ComponentNamePresenter`）: `component-name/presenter.tsx`
   - `"use client"` + `use(dataPromise)`
   - フォーム実装（RHF or useActionState）
   - データ取得が不要な場合、プレゼンテーションは不要（コンテナ内に直接フォーム実装）
3. **Skeleton**（`ComponentNameSkeleton`）: `component-name/index.tsx`内
4. **Action**: `component-name/action.ts`
   - Server Actionはこのファイルに集約する

### 命名規則

- コンテナ: `ComponentName`
- プレゼンテーション: `ComponentNamePresenter`
- Skeleton: `ComponentNameSkeleton`（非公開）
- データ型: `ComponentNameData`（例: `FormData`）
- フォーム値型: `ComponentNameFormValues`（例: `FormValues`）
- Server Action: `actionNameAction`（例: `updateDataAction`）

### カード + フォームの基本構造

`<Card>`直下に`<form>`を置き、`CardHeader`/`CardContent`/`CardFooter`を包む。ボタンは右寄せ。

```tsx
<Card>
  <form onSubmit={...} action={...}>
    <CardHeader>...</CardHeader>
    <CardContent>...</CardContent>
    <CardFooter>
      <div className="flex justify-end w-full">
        <Button type="submit">保存</Button>
      </div>
    </CardFooter>
  </form>
</Card>
```

### アクセシビリティ

- `aria-invalid`の付与
- `htmlFor`と`id`の対応
- エラー表示は`FieldError`を使用

### 成功/失敗の扱い

- **クライアント側**: `toast.success()` / `toast.error()`
- **リダイレクト時**: `redirectToast`を使用（`redirect()`前）
- **再取得**: `router.refresh()`（クライアント） or `revalidatePath()`（Server Action）

### ローディング

- 送信ボタンに`disabled`を付与
- 進行中は`Spinner`を表示

## パターンA: React Hook Form + Valibot

### 必須要素

- `useForm` + `standardSchemaResolver(formSchema)`
- `Valibot`でスキーマ定義 (`v.object`)
- `Controller`で各フィールドをラップ
- **複数コンポーネントに分割する場合のみ** `FormProvider`

### 最小テンプレート（抜粋）

```tsx
"use client"

import { standardSchemaResolver } from "@hookform/resolvers/standard-schema"
import { useRouter } from "next/navigation"
import { use } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import * as v from "valibot"

const formSchema = v.object({
  name: v.optional(v.pipe(v.string(), v.trim())),
})

type FormValues = v.InferInput<typeof formSchema>

export function ComponentNamePresenter({ dataPromise }: { dataPromise: Promise<FormData> }) {
  const data = use(dataPromise)
  const router = useRouter()
  const form = useForm<FormValues>({
    resolver: standardSchemaResolver(formSchema),
    defaultValues: { name: data.initialName ?? "" },
  })

  const onSubmit = async (values: FormValues) => {
    try {
      await updateAction(values.name ?? null)
      toast.success("保存しました")
      router.refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "エラーが発生しました")
    }
  }

  return <form onSubmit={form.handleSubmit(onSubmit)}>{/* fields */}</form>
}
```

### Field構造（共通UI）

フィールドのUIは`@repo/ui`（shadcn/ui）の`Field`系コンポーネントを使用する。

```tsx
<Field data-invalid={fieldState.invalid}>
  <FieldLabel htmlFor={field.name}>ラベル</FieldLabel>
  <FieldContent>
    <Input {...field} aria-invalid={fieldState.invalid} />
    <FieldDescription>説明</FieldDescription>
    {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
  </FieldContent>
</Field>
```

### バリデーション例

- 必須: `v.pipe(v.string(), v.trim(), v.minLength(1, "必須"))`
- オプショナル: `v.optional(v.pipe(v.string(), v.trim()))`
- カスタム: `v.pipe(v.string(), v.check((value) => isValid(value), "エラー"))`

詳細: https://valibot.dev/llms.txt

### ダイアログ内フォームのリセット

`useEffect`で`form.reset()`は使わず、**マウント/アンマウント**で初期化する。

- 作成: 条件付きレンダリングでアンマウント
- 編集: `key`で再マウント
- 初期値: `defaultValues`にpropsから直接渡す

## パターンB: useActionState

### 使いどころ

- 削除確認、簡易送信などバリデーションが不要なケース
- `form`の`action`に`formAction`を直接渡したい場合

### 最小テンプレート（抜粋）

```tsx
"use client"

import { useActionState, useEffect, useState } from "react"
import { toast } from "sonner"

export function Component({ id }: { id: string }) {
  const [open, setOpen] = useState(false)
  const [state, formAction, pending] = useActionState(
    deleteAction.bind(null, id),
    null,
  )

  useEffect(() => {
    if (state?.error) {
      toast.error(state.error)
      setOpen(false)
    }
  }, [state])

  return (
    <form action={formAction}>
      <Button type="submit" disabled={pending}>削除</Button>
    </form>
  )
}
```

### Server Actionのシグネチャ

```ts
export async function deleteAction(
  id: string,
  // remove if unneeded
  prevState: DeleteState | null,
  formData: FormData,
): Promise<DeleteState> {
  try {
    await deleteItem(id)
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "削除に失敗しました",
    }
  }

  revalidatePath("/")
  await redirectToast.success("削除しました")
  redirect("/")
}
```

### 重要ポイント

- `const [state, formAction, pending] = useActionState(action.bind(null, id), null)`
- `pending`でローディング制御
- エラーは**戻り値**として返す（`throw`しない）
- `redirect` は try-catch の外で実行
