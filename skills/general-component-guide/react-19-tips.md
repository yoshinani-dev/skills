# React 実装のコツ

## 目次

- ref props
- Context as Provider
- use(Context) の使用

## ref props

### ルール

- `forwardRef` を使用しない: React 19では関数コンポーネントが自動的にrefを受け取る
- `displayName` は不要: `forwardRef`を使わないため設定不要

### チェックポイント

- [ ] `forwardRef` の使用がないか
- [ ] 不要な `displayName` の設定がないか

### ❌ React 18の書き方

```tsx
import { forwardRef } from "react";

export const MyComponent = forwardRef<HTMLDivElement, Props>(
  ({ children, ...props }, ref) => {
    return (
      <div ref={ref} {...props}>
        {children}
      </div>
    );
  },
);

MyComponent.displayName = "MyComponent";
```

### ✅ React 19の書き方

```tsx
export function MyComponent({ children, ...props }: Props) {
  return <div {...props}>{children}</div>;
}
```

## Context as Provider

### ルール

`Context.Provider` の代わりに `Context` を直接 Provider として使用できる

### ❌ React 18の書き方

```tsx
const ThemeContext = createContext("");

function App({ children }) {
  return <ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>;
}
```

### ✅ React 19の書き方

```tsx
const ThemeContext = createContext("");

function App({ children }) {
  return <ThemeContext value="dark">{children}</ThemeContext>;
}
```

## use(Context) の使用

### ルール

- `useContext(Context)` の代わりに `use(Context)` を使用する
- `use` は React 19 で導入された新しい Hook で、Context の読み取りに推奨される
- より簡潔で、将来的な React の最適化にも対応しやすい

### チェックポイント

- [ ] `useContext` を使用していないか
- [ ] `use` をインポートしているか

### ❌ React 18の書き方

```tsx
import { useContext } from "react";

const ThemeContext = createContext("");

function ThemedButton() {
  const theme = useContext(ThemeContext);
  return <button className={theme}>Click me</button>;
}
```

### ✅ React 19の書き方

```tsx
import { use } from "react";

const ThemeContext = createContext("");

function ThemedButton() {
  const theme = use(ThemeContext);
  return <button className={theme}>Click me</button>;
}
```
