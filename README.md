# Skills

AIコーディングアシスタント向けのスキル集です。

## インストール

プロジェクトで以下のコマンドを実行してスキルを有効化します。

```bash
npx skills add https://github.com/yoshinani-dev/skills
```

## 外部 SKILL の取り込み

外部リポジトリで管理されている SKILL は `external-skills.yaml` で管理します。

```yaml
skills:
  - repo: https://github.com/anthropics/skills
    skill: frontend-design
```

`.github/workflows/update-external-skills.yml` が毎週この一覧をもとに
`npx skills add <repo> --skill <name>` を実行し、差分があれば自動で PR を作成します。
