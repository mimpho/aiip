---
name: kb-maintenance
description: >
  Mantenimiento de las fuentes de la Knowledge Base de AIIP (data/raw/). Úsala
  cuando Marcos quiera añadir, actualizar, renombrar/reestructurar o eliminar
  una fuente o documento de la KB, o rellenar/actualizar URLs en el manifest.
  Se apoya en docs/kb-maintenance.md (runbook de referencia) y guía paso a
  paso, incluida la limpieza de chunks huérfanos en ChromaDB cuando aplica.
  Actívala cuando Marcos diga "añado una fuente nueva a la KB", "he renombrado
  una carpeta de data/raw", "quiero actualizar el manifest", "hay que limpiar
  huérfanos de ChromaDB" o similar.
---

# kb-maintenance

Workflow guiado para operaciones de mantenimiento sobre las fuentes de la KB
(`data/raw/`). Se apoya en `docs/kb-maintenance.md` como fuente de verdad del
procedimiento — esta skill no duplica los pasos, los orquesta.

## Paso 0 — Identifica el escenario

Pregunta a Marcos (o infiere de su mensaje) cuál de los escenarios de
`docs/kb-maintenance.md` aplica:

1. Añadir una fuente nueva
2. Añadir un documento a una fuente existente (incluye páginas web sin PDF)
3. Actualizar el contenido de un documento existente
4. Renombrar o reestructurar una fuente
5. Eliminar un documento o una fuente completa
6. Rellenar o actualizar la URL de un documento en el manifest

Si no está claro, pregúntalo explícitamente antes de continuar — cada
escenario tiene pasos distintos y algunos (4 y 5) requieren limpieza de
ChromaDB que los otros no.

## Paso 1 — Lee docs/kb-maintenance.md

Lee la sección correspondiente al escenario identificado antes de dar
cualquier instrucción — no cites de memoria, el runbook es la fuente de
verdad y puede haberse actualizado desde la última vez que se usó esta skill.

## Paso 2 — Pasos manuales de Marcos

Presenta los pasos manuales del escenario (mover/crear ficheros en
`data/raw/`, editar `manifest.json`, actualizar `docs/kb-sources.md` si
aplica). Si el cambio es sobre `manifest.json` y tienes acceso al fichero,
puedes hacer la edición directamente (no es una acción reservada a Marcos —
ver AGENTS.md "Reparto git": editar ficheros no es un comando git). Verifica
siempre el JSON resultante antes de darlo por bueno (checksums vacíos en
entradas nuevas son esperados hasta el próximo reindex, ver D-021).

## Paso 3 — Comandos a ejecutar [GATE: Marcos ejecuta]

Nunca ejecutes tú los comandos que tocan la KB real o ChromaDB — ni el
reindex (`python scripts/smoke_test_rag.py --force-reingest`) ni el borrado
explícito de chunks huérfanos (`delete_document_chunks`, escenarios 4 y 5).
Preséntaselos a Marcos igual que los comandos de git — están fuera del
sandbox de Cowork.

## Paso 4 — Verificación

Recuerda el paso de verificación del escenario correspondiente en
`docs/kb-maintenance.md` (recuento de chunks, ausencia de huérfanos, etc.).

## Si el escenario no está cubierto en el runbook

Si surge un caso nuevo no documentado en `docs/kb-maintenance.md`, resuélvelo
con Marcos y **añádelo al runbook** antes de cerrar — el objetivo de esta
skill es que el runbook nunca quede desactualizado respecto a los casos
reales que aparecen.
