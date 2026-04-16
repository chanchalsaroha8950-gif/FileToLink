#!/usr/bin/env bash
set -euo pipefail

pkill -f "python main.py( |$)" 2>/dev/null || true
pkill -f "python bot.py( |$)" 2>/dev/null || true

echo "Stopped main.py and bot.py (if running)."
