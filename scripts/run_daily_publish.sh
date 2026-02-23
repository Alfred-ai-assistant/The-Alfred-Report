#!/usr/bin/env bash
set -euo pipefail

cd /home/alfred/repos/The-Alfred-Report

git pull --rebase

./scripts/publish_report.py

git add public/alfred-report

if git diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi

git commit -m "Publish Alfred Report $(date -I)"
git push
