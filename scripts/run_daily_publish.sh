#!/usr/bin/env bash
set -euo pipefail

cd /home/alfred/repos/The-Alfred-Report

# Load secrets from AWS Secrets Manager (same pattern as gateway wrapper)
eval "$(aws secretsmanager get-secret-value \
  --secret-id openclaw/prod/secrets \
  --query SecretString \
  --output text | python3 -c "
import json, sys
try:
    secrets = json.load(sys.stdin)
    for key, value in secrets.items():
        print(f'export {key}=\"{value}\"')
except Exception as e:
    print(f'# Error loading secrets: {e}', file=sys.stderr)
")"

# Stash any local changes before pulling
git stash --include-untracked || true

# Pull latest
git pull --rebase

# Generate report
./scripts/publish_report.py

# Stage report artifacts
git add public/alfred-report

# Only commit if there are actual changes
if git diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi

git commit -m "Publish Alfred Report $(date -I)"
git push
