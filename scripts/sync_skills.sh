#!/usr/bin/env bash
# sync_skills.sh — Sincroniza las skills del repo con el plugin instalado en Cowork.
#
# Uso: bash scripts/sync_skills.sh
#
# Ejecutar cada vez que se modifique un fichero en skills/.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="/var/folders/zd/4_sj3_6s7kz_hrf4pblnv3jr0000gq/T/claude-hostloop-plugins/4b7d92a336802ee8/skills"

if [ ! -d "$PLUGIN_DIR" ]; then
  echo "❌ Plugin dir no encontrado: $PLUGIN_DIR"
  echo "   Asegúrate de que Cowork está abierto y el plugin está instalado."
  exit 1
fi

SKILLS=("epic-start" "epic-close" "task-start" "task-close" "kb-maintenance")

for skill in "${SKILLS[@]}"; do
  src="$REPO_DIR/skills/$skill/SKILL.md"
  dst="$PLUGIN_DIR/$skill/SKILL.md"

  if [ ! -f "$src" ]; then
    echo "⚠️  Skill no encontrada en repo: $src — saltando"
    continue
  fi

  if [ ! -f "$dst" ]; then
    echo "🆕 Skill nueva, creando destino en el plugin: $dst"
    mkdir -p "$(dirname "$dst")"
  fi

  cp "$src" "$dst"
  echo "✅ $skill sincronizada"
done

echo ""
echo "Sync completado. Recarga Cowork si tienes una sesión abierta."
