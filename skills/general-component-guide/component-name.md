# コンポーネントの命名規則

## 関連ガイド

- React 19 のベストプラクティスは [react-19-tips.md](react-19-tips.md) を参照

## ルール

### コンポーネント名

- ファイル名とそのファイルが提供するメインコンポーネント名は完全に一致させる
- **コンポーネント名は基本的に2単語以上にする**（例: `DataTable`, `UserCard`, `SearchInput`）

### Props型の命名

Props型は `{ComponentName}Props` という命名にする

例: `DataTable` コンポーネントの場合は `DataTableProps`

## コンポーネント作成完了チェックリスト

新しいコンポーネントを作成した際は、以下の項目を確認してください:

- [ ] ファイル名とエクスポートされるコンポーネント名が完全一致している
- [ ] コンポーネント名は2単語以上になっている
- [ ] Props型は `{ComponentName}Props` という命名になっている
- [ ] 機能固有の動作は props や内部実装で区別している (コンポーネント名では区別しない)
- [ ] Storybook でコンポーネントの動作を確認した
- [ ] TypeScript の型エラーがない
- [ ] [react-19-tips.md](react-19-tips.md) のベストプラクティスに従っている
- [ ] `pnpm run format` でフォーマットを実行した

## 注意

機能固有の動作は props で制御し、コンポーネント名では区別しない

## ❌ 間違った例

### 例1: DataTable.tsx - コンポーネント名の不一致

```tsx
// ファイル名: DataTable.tsx
// ❌ ファイル名と異なるコンポーネント名
export function Table() {
  // ...
}
```

### 例2: SelectMenu.tsx - Props型の命名ミス

```tsx
// ファイル名: SelectMenu.tsx
// ❌ Props型の命名が ComponentNameProps になっていない
type Props = {
  options: Option[];
  onSelect: (option: Option) => void;
};

export function SelectMenu({ options, onSelect }: Props) {
  // ...
}
```

## ✅ 正しい例

### 例1: DataTable.tsx

```tsx
// ファイル名: DataTable.tsx
// ✅ ファイル名とコンポーネント名が一致
// ✅ 2単語のコンポーネント名
// ✅ Props型が ComponentNameProps の命名

type DataTableProps = {
  data: DataItem[];
  columns: Column[];
  onRowClick?: (row: DataItem) => void;
};

export function DataTable({ data, columns, onRowClick }: DataTableProps) {
  // 機能固有の動作は props で制御
  return <table>{/* テーブルの実装 */}</table>;
}
```

### 例2: UserCard.tsx

```tsx
// ファイル名: UserCard.tsx
// ✅ ファイル名とコンポーネント名が一致
// ✅ 2単語のコンポーネント名
// ✅ Props型が ComponentNameProps の命名

type UserCardProps = {
  name: string;
  email: string;
  avatar?: string;
};

export function UserCard({ name, email, avatar }: UserCardProps) {
  // 機能固有の動作は props や内部実装で区別
  return (
    <div>
      {avatar && <img src={avatar} alt={name} />}
      <h2>{name}</h2>
      <p>{email}</p>
    </div>
  );
}
```
