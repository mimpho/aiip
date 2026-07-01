# kb-sources.md — Fuentes de la Knowledge Base (E-06)

> Índice de fuentes candidatas para la KB de AIIP. Alimenta la épica E-06 (Ingesta y
> procesamiento de la KB), bloqueada por validación de Jacques Rivière (ver
> `backlog/epics.md`).
> Los documentos pesados (PDFs, exports) viven en Drive (`data/raw/`), no en este repo.
> Este fichero es el único índice — no se duplica contenido, solo se referencia.

**Leyenda de estado**
- `Validada` — confirmada explícitamente por Jacques (PRD v1.9 o comentarios)
- `Propuesta` — enlace aportado por Jacques o derivado de sus enlaces, pendiente de validación formal
- `Por explorar` — plataforma general, falta identificar las páginas/documentos concretos a indexar

---

## Perfil Familiar (Fase 1)

| Fuente | Tipo | Idioma | Estado | Origen | Notas |
|---|---|---|---|---|---|
| [IPOPI](https://ipopi.org/) | Plataforma / guías divulgativas | ES / EN | Validada (PRD) · plataforma general por explorar | PRD v1.9 §5 | Fuente ya validada en PRD. La plataforma general (`ipopi.org`) es amplia — pendiente localizar qué secciones/documentos indexar. |
| [IPOPI — What are PIDs](https://ipopi.org/pids/what-are-pids/) | Guía divulgativa | EN | Propuesta | Jacques (enlace) | Página concreta dentro de ipopi.org, ya identificada. |
| [IDF — Immune Deficiency Foundation](https://primaryimmune.org/resources) | Guías y recursos para familias | EN | Validada (PRD) | PRD v1.9 §5 | `primaryimmune.org` es el dominio de IDF. Página de recursos con varios artículos — revisar cuáles indexar. |
| Guías clínicas validadas por el equipo | Documentación interna validada | ES | Validada (PRD) | PRD v1.9 §5 | Pendiente de recibir los documentos concretos. |
| [upiip.com — Info al paciente](https://www.upiip.com/es/paciente/info-al-paciente) | Web de la fundación (protocolos + recursos) | ES | Validada (respuesta Jacques, PRD §11 P2) | Jacques | Documentos ya subidos a `data/raw/` sin organizar — ver nota abajo. |
| [Acadip — PIDs (signos de alerta)](https://www.acadip.org/ca/idps) | Guía divulgativa (incluye imagen con signos de alarma) | CA | Propuesta | Jacques | Relevante para el módulo de seguridad (Falso Negativo Cero) — signos de alarma. |
| [Acadip — Webinars](https://www.acadip.org/ca/webinars) | Webinars | CA | Propuesta | Jacques | Formato audiovisual — evaluar si aporta texto indexable o solo referencia. |
| [AEDIP — 10 señales de aviso](https://aedip.com/informacion-medica/10-senales-de-aviso/) | Guía divulgativa (signos de alarma) | ES | Propuesta | Jacques | Relevante para el módulo de seguridad, en línea con la anterior de Acadip. |
| [AEDIP — Clasificación de inmunodeficiencias](https://aedip.com/informacion-medica/clasificacion-de-inmunodeficiencias) | Guía divulgativa | ES | Propuesta | Jacques | |
| [AEDIP — Tratamiento con inmunoglobulinas](https://aedip.com/informacion-medica/tratamiento-con-inmunoglobulinas) | Guía divulgativa | ES | Propuesta | Jacques | Relacionado con CU-02 (medicación prescrita). |
| [AEDIP — Directorio de hospitales](https://aedip.com/informacion-medica/directorio-de-hospitales) | Directorio de contacto | ES | Propuesta | Jacques | Relacionado con CU-05 (canales de atención). |
| Protocolos del equipo de inmunología | Documentación interna | ES | Pendiente | PRD v1.9 §5 | Marcado como `[Pendiente]` en el PRD original. |

## Perfil Profesional (Fase 2B — condicional a decisión de alcance)

| Fuente | Tipo | Idioma | Estado | Origen | Notas |
|---|---|---|---|---|---|
| [Orphanet](https://www.orpha.net/) | BBDD de enfermedades raras | EN (principalmente) | Validada (PRD) | PRD v1.9 §5 | |
| [ESID](https://esid.org/) | Guías clínicas especializadas | EN | Validada (PRD) | PRD v1.9 §5 | |
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | Literatura científica peer-reviewed | EN | Validada (PRD) | PRD v1.9 §5 / Jacques | Confirmado por Marcos como perfil profesional (papers). |
| [HAS — PNDS Déficits immunitaires héréditaires 2023](https://afpa.org/content/uploads/2023/05/HAS_deficits-immunitaires-hereditaires_PNDS-2023.pdf) | Guía clínica oficial (Francia) | FR | Propuesta | Jacques | PDF — protocolo nacional de diagnóstico y cuidado. |
| [The 2024 update of IUIS phenotypic classification](https://rupress.org/jhi/article/1/1/e20250002/277374/The-2024-update-of-IUIS-phenotypic-classification) | Paper científico (clasificación) | EN | Propuesta | Jacques (vía IPOPI) | Clasificación de referencia del campo. |

---

## Nota abierta — idioma de la KB (D-011)

D-011 fija la KB interna en inglés (bge-m3 resuelve el cross-lingual retrieval), asumiendo que
las fuentes de referencia (IPOPI, IDF, Orphanet, ESID, PubMed) son nativamente en inglés. Varias
de las fuentes nuevas de Jacques son nativas en español/catalán/francés (upiip.com, Acadip,
AEDIP, PNDS de la HAS) y no tienen versión en inglés equivalente. Antes de cerrar la estrategia
de chunking de E-06 conviene decidir explícitamente si estas fuentes se indexan en su idioma
original (rompiendo la capa única en inglés de D-011) o si se traducen — impacta directamente en
D-011 y merece registrarse como decisión en `decisions.md` cuando se arranque E-06.

## Organización de `data/raw/`

Los documentos descargados están organizados en `data/raw/` por carpetas de fuente (upiip,
ipopi, etc.) — resuelto. Facilita trazar la procedencia de cada documento, en línea con el
checklist DAIMS mencionado en `backlog/epics.md` (E-06).
