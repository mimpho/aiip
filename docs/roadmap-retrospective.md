# Retrospectiva final del roadmap — AIIP

## E-12 T-01 — Cierre del TFM

> Recorrido cronológico de cómo se fue construyendo y ajustando el plan de este proyecto, desde
> antes de que existiera el repositorio hasta el cierre de esta misma épica. No repite el qué
> (eso ya está en `backlog/epics.md` y `decisions.md`) — se centra en el porqué de cada cambio de
> rumbo, con su decisión de origen citada.

---

## 1. Antes del repositorio: de una idea de reparación genética a un asistente conversacional

El proyecto no arrancó como AIIP. La primera idea, explorada con Gemini como herramienta de
diseño, fue **XIAP-Precision-Repair (XPR)**: una herramienta para acelerar el diseño de
estrategias de reparación genética (Prime Editing/pegRNA) y estabilización proteica para
variantes concretas del gen XIAP, combinando predicción estructural (ESM-2/AlphaFold 3), diseño
de pegRNA (PRIDICT/DeepPrime) y un grafo de conocimiento que conectara cada mutación con terapias
ya existentes. Llegó a tener un mockup de producto (`XIAP-Rescue`) con flujo de usuario completo.

Quien vio inviable XPR como TFM fue Jacques Rivière (inmunólogo pediátrico colaborador) — no por
viabilidad técnica en sentido estricto, sino por la complejidad del tema y la cantidad de
perfiles científicos distintos (genética, biología estructural, farmacología) que habría exigido
incluir en la idea de producto para que fuera algo más que una maqueta. Fue también Jacques quien
propuso la alternativa: un asistente conversacional para ayudar a las familias que conviven con
una IDP — la idea que terminó siendo AIIP.

El vínculo entre XPR y AIIP no es casualidad ni curiosidad de nombres — ambas ideas nacen del
mismo propósito: usar el TFM para sentar la base de una herramienta que ayude de verdad a quien
convive con una Inmunodeficiencia Primaria, primero pensando en la comunidad científica (XPR) y,
al descartarse esa vía, en las familias (AIIP). Ese propósito no es abstracto para Marcos: dos de
sus hijos conviven con una IDP. Que XIAP reapareciera meses después como el caso real que motivó
la ampliación de la KB en E-13 (sección 2) no es entonces la coincidencia que parece a primera
vista, sino la misma motivación de origen resurgiendo en el trabajo técnico.

El PRD de lo que sí se construyó se fue puliendo con Gemini y con Jacques Rivière (inmunólogo
pediátrico colaborador) por correo y documentos compartidos, hasta llegar a la versión que sirvió
de base al proyecto. A partir de ahí se adoptaron Antigravity y Cowork como herramientas de
trabajo, y arrancó lo que sí está documentado en este repositorio.

El mismo patrón —herramienta de IA para explorar, criterio humano para decidir— se repitió en el
diseño visual (E-02): un prompt generado con Gemini se pasó a Lovable para obtener una primera
propuesta de UI, revisada con Jacques. Esa propuesta no se llevó a producción tal cual — sirvió
de referencia, no de constraint (`docs/design-brief.md`), para que Claude Design definiera la
guía real: logo, imagen corporativa y los tokens CSS que terminaron consumiendo Chainlit y las
páginas de Supabase Auth (D-013).

---

## 2. La base de conocimiento: de la propuesta inicial a MedlinePlus

Las primeras fuentes de la KB tampoco se decidieron durante el desarrollo — ya venían propuestas
por Jacques en el PRD (v1.9): IPOPI, IDF, upiip.com y guías clínicas validadas por su equipo, más
contenido específico de signos de alarma (AEDIP, Acadip) pensado desde el inicio para el módulo
de seguridad. E-06 organizó y validó ese primer conjunto (`docs/kb-sources.md`).

La KB se amplió dos veces más, cada vez con una razón distinta. En E-11 T-01, al investigar por
qué ciertos casos fallaban por falta de cobertura (no por retrieval), se añadieron nueve
documentos más de las mismas fuentes ya validadas (AEDIP, IPOPI) más SEICAP como fuente nueva —
acotados a seis huecos genuinos verificados contra `data/raw/manifest.json` antes de añadir nada
(sección 4, P-032). Solo después, en E-13, se incorporó una fuente completamente nueva —
MedlinePlus Genetics— para cerrar un hueco de profundidad por enfermedad concreta (el caso
"xiap") que ampliar las fuentes ya conocidas no podía resolver.

---

## 3. Primer ajuste: qué exige realmente el hito

El 7 de julio, con E-05 (interfaz Chainlit) y E-07 (RAGAS parcial) ambas pendientes, se decidió
adelantar E-05: el hito del 10 de julio ("código funcional") lo entregaba E-05, no E-07, y el
ciclo de mejora de RAGAS ya estaba asignado a Fase 1.5 desde el diseño original. Primer ejemplo
de un patrón que se repite en todo el proyecto: el roadmap se ajusta cuando hay una razón
concreta, no por conveniencia.

---

## 4. La calidad del RAG no llegó a lo esperado

El plan de evaluación fijaba objetivos claros (Faithfulness >95%, Context Precision >85%, etc.)
sin prever ninguna épica dedicada a *mejorar* el RAG — se esperaba que el pipeline se acercara a
esos números de forma razonable. No ocurrió: al cerrar E-09 (18 jul), cuatro de seis métricas
seguían por debajo de objetivo (Faithfulness 83.7%, Context Precision 52.1%, Hallucination Rate
93.75% frente a <2%). Se documenta sin maquillarlo, mismo criterio de transparencia que el
proyecto aplicó siempre en `docs/evaluation.md`.

La respuesta no fue un parche, fueron dos decisiones deliberadas:

- **E-11**, creada como gate de calidad antes de tocar memoria conversacional (D-059) — mezclar
  historial de chat con una generación de calidad no resuelta habría encarecido cualquier
  diagnóstico futuro. En la misma decisión se descartaron dos atajos: subir la temperatura (no es
  la palanca correcta, tiende a empeorar Faithfulness) y conectar búsqueda web en vivo (rompería
  trazabilidad de fuentes y el principio de Falso Negativo Cero). La palanca que sí funcionó fue
  ampliar la KB: +10.5pp de Context Precision y +8.4pp de Context Recall solo por contenido,
  antes de tocar el retriever (P-032).
- **E-15**, creada el 26 de julio (D-096) como ronda 2 del ciclo de mejora, sin fecha, para
  cuando se retome tras el TFM. Formaliza un gate explícito: la memoria conversacional de E-08 no
  se activa hasta que Faithfulness supere 95% y Context Precision 85% — cerrar épicas de producto
  no libera ese bloqueo por sí solo.

---

## 5. Un resultado mixto, investigado antes de cerrarlo

E-13 (ampliación de KB con MedlinePlus Genetics, nacida de un caso real de "xiap" mal respondido)
cerró con dos métricas mejor y dos peor que E-11: Context Precision cayó −3.7pp, justo la métrica
que más se esperaba mejorar. En vez de aceptar el número agregado, se investigó caso a caso
(D-086): la caída se concentraba en solo 5 de 32 casos, y 4 de ellos resultaron ruido del propio
evaluador LLM, no un efecto real del contenido nuevo.

Vale la pena señalar que el propio análisis se autocorrigió por el camino: una primera lectura
conectó esa caída con un hallazgo de retrieval real (BM25 no encuentra fichas de MedlinePlus para
preguntas de listado amplio en español, D-084) como si fueran la misma causa. Investigado con más
rigor, no lo eran — y la corrección se documentó el mismo día en vez de dejarla pasar.

---

## 6. E-08, replanteada bajo presión de calendario

Memoria de perfil e histórico nació con tres capas y cambió de alcance cuatro veces en ocho días:
bloqueo de la capa 1 por calidad de RAG (D-059) → aplazamiento completo de la épica para hacerle
sitio a E-13 (D-063) → extracción de la capa 2 como E-14, sustituyendo a E-10 (D-087) → el
bloqueo de la capa 1 formalizado como gate numérico explícito en vez de razón narrativa dispersa
(D-096). Cuatro decisiones, cada una trazable, ninguna arbitraria — la razón de fondo (no activar
memoria conversacional sobre un pipeline de calidad no resuelta) nunca cambió, solo se precisó.

---

## 7. El despliegue público: dos reversiones de plataforma en una tarde

El compromiso de una URL pública se fijó en junio (D-007) para el 10 de julio y quedó sin
ejecutar hasta el cierre de esta misma épica (T-03, 27-28 de julio). El plan inicial elegía
Fly.io por una razón técnica concreta: su build usa el filesystem local como contexto, evitando
el git-lfs que exigiría subir `data/chroma/` (gitignored a propósito, para GitHub) a un remoto
separado. Antes de implementarlo, se pidió verificar explícitamente que el tier gratuito de la
plataforma elegida seguía siendo real — no darlo por bueno solo porque el plan ya estaba escrito.
La verificación (contra documentación oficial, no contra los blogs de terceros que resultaron
poco fiables en varias búsquedas intermedias) encontró que Fly.io ya no ofrece tier gratuito a
cuentas nuevas desde 2024. Primera reversión: HF Spaces. Con el Dockerfile ya validado de punta a
punta en local, al ir a crear el Space se descubrió que su SDK Docker está tras un muro de pago
desde hacía ~3 semanas — cambio no anunciado oficialmente por Hugging Face, confirmado con una
captura de la propia interfaz. Segunda reversión, en la misma tarde: Google Cloud Run, con su
cuota Always Free verificada con el mismo criterio (D-098).

La ejecución sobre Cloud Run sacó a la luz varios problemas silenciosos que el plan no había
anticipado — ninguno bloqueante por separado, pero juntos impidieron que la app funcionara hasta
resolverlos: symlinks que no sobreviven a `gcloud run deploy --source .` (a diferencia de un
`docker build` local), una variable de entorno (`CHAINLIT_URL`) necesaria para que el login de
Google construya la URL de retorno correcta detrás del proxy de Cloud Run, y el hallazgo más
grave — `gcloud run deploy --source .` hereda `.gitignore` cuando no existe un `.gcloudignore`
explícito, dejando `data/chroma/` completamente fuera de la imagen sin lanzar ningún error: el
RAG respondía con normalidad, solo que sin ningún contexto real de la base de conocimiento.
Diagnosticado aislando la causa con un test dirigido sobre la imagen exacta desplegada, en vez de
asumir que era la condición de carrera entre instancias ya sospechada por el autoscaling de Cloud
Run (D-099).

---

## 8. Por qué existe este documento

La necesidad de esta retrospectiva surgió el 19 de julio, al pedir Marcos dejar constancia de un
caso de human-in-the-loop (sección 9) y preguntar dónde quedaba reflejada la evolución del
roadmap completo — no había ningún sitio para eso (D-062). Se creó E-12 como última épica de la
Fase 1.5, sin TDD pero con rama y PR, marcada desde el origen como innegociable: se ejecuta pase
lo que pase con el resto del roadmap (D-064).

---

## 9. Aprendizajes de proceso

**KB limitada, verificada antes de tocar código.** Ante peor Context Precision/Recall en varios
casos de E-09, la intuición de que faltaba cobertura documental (no un problema de ranking) se
verificó contra `data/raw/manifest.json` antes de tocar el retriever — confirmada con números,
no solo con intuición (P-032).

**Cowork y Antigravity no son intercambiables, aunque compartan modelo.** El valor está en el
contexto y el rol de cada superficie: Cowork como espacio de debate antes de ejecutar, dejando
planes sin ambigüedad para que el ciclo TDD no tenga que parar a decidir nada (P-042).

**Un hallazgo estructural, con autocorrección incluida.** Ya contado en la sección 5 — mostrar
que una explicación "limpia" que conecta varias piezas de evidencia merece la misma revisión
escéptica que cualquier otro resultado (P-043).

**Los límites de la herramienta elegida, aceptados y documentados.** Tras cerrar E-14 T-05,
reflexión de Marcos sobre Chainlit: *"está pensado para montar y tirar con lo que viene"* — buena
parte de la personalización del proyecto vive como parches sobre internals no documentados,
riesgo aceptado caso a caso, no ignorado (P-044).

**Verificar antes de comprometerse, incluso con la respuesta ya escrita en un plan.** Pedir
verificar el tier gratuito de una plataforma ya "decidida" reveló que ni Fly.io ni HF Spaces
ofrecían ya una ruta gratuita real, forzando dos reversiones en una tarde (P-045). El mismo
principio de escepticismo, aplicado a un fallo silencioso en producción en vez de a un plan:
aislar la causa con un test dirigido antes de asumir la hipótesis más plausible sobre la mesa
(P-046).

---

## 10. Lo que queda para después del TFM

AIIP se define como un TFM con vocación de herramienta real, no un ejercicio que termina el 29 de
julio. Eso se refleja en cómo queda documentado lo pendiente, no solo en lo que se construyó:
E-15 tiene alcance y candidatos de investigación propios, no es una nota suelta; las capas 1 y 3
de E-08 quedan condicionadas con un criterio explícito, no abandonadas sin más; y el backlog de
features opcionales (perfil profesional, multimodal, integración web) sigue ahí como horizonte de
producto. Nada de esto estaba en el plan de Fase 0 — se fue identificando a medida que el
proyecto avanzaba, que es exactamente lo que cabe esperar de una herramienta pensada para seguir
mejorando después de la entrega.

---

## 11. Cierre

El roadmap de AIIP cambió varias veces, y cada cambio tiene una decisión, un contexto y una
alternativa descartada que lo justifican — desde la idea original abandonada por viabilidad
técnica hasta el gate de métricas que hoy condiciona la memoria conversacional, pasando por la
propia plataforma de despliegue, revertida dos veces en una tarde por verificación explícita en
vez de confianza ciega en un plan ya escrito. Ningún ajuste fue
gratuito, y ninguno se cierra fingiendo un resultado mejor del que hay: Faithfulness y Context
Precision siguen por debajo de objetivo a fecha de este documento. Se documenta así, sin
suavizarlo, porque el valor de este roadmap no está en haber llegado a todos los números dentro
de un plazo de TFM, sino en haber medido antes de decidir en cada punto de inflexión.
