#!/bin/bash
# Mikoshi Gear — Catalog Studio (macOS launcher)
# Double-click in Finder, or run:  bash start-studio.command
cd "$(dirname "$0")/.." || exit 1
echo "Starting Mikoshi Catalog Studio…"
python3 studio/server.py
