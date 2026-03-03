#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-external-skills.yaml}"

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config file not found: $CONFIG_PATH" >&2
  exit 1
fi

while IFS=$'\t' read -r repo skill; do
  [[ -z "$repo" || -z "$skill" ]] && continue

  echo "Syncing $skill from $repo"
  npx -y skills add "$repo" --skill "$skill" --copy -y

done < <(yq -r '.skills[] | [.repo, .skill] | @tsv' "$CONFIG_PATH")
