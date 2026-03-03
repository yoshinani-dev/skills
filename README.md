# Skills

AIコーディングアシスタント向けのスキル集です。

## インストール

プロジェクトで以下のコマンドを実行してスキルを有効化します。

```bash
npx skills add https://github.com/yoshinani-dev/skills
```

## 外部SKILLの取り込み

`external-skills.yaml` で外部リポジトリから取り込むSKILLを管理します。

```yaml
skills:
  - repo: https://github.com/anthropics/skills
    skill: frontend-design
```

追加・更新は次のコマンドで実行できます。

```bash
./scripts/update-external-skills.sh
```

GitHub Actions (`.github/workflows/update-external-skills.yml`) により、毎週月曜に自動同期し、差分がある場合はPRを作成します。
