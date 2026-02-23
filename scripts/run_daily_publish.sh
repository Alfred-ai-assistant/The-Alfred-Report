#!/usr/bin/env bash
set -euo pipefail

cd /home/alfred/repos/The-Alfred-Report

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
