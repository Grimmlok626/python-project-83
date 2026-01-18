#!/usr/bin/env bash
set -e
# Устанавливаем uv (используется для запуска задач)
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
make install