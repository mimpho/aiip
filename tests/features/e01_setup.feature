# E-01 — Setup del entorno de desarrollo
# Épica: configuración de todos los servicios, credenciales y estructura necesarios
# para arrancar el desarrollo de AIIP.
#
# Metodología: BDD + Gherkin — ver D-006 en decisions.md
# Estas tareas son de configuración de entorno, no de código de producción.
# Los criterios de aceptación son verificables manualmente o mediante script de smoke test.

# ─────────────────────────────────────────────────────────────
# T-01 — Proyecto Supabase creado y configurado
# ─────────────────────────────────────────────────────────────

@done
Feature: T-01 Proyecto Supabase operativo

  Como desarrollador del proyecto AIIP
  Quiero tener un proyecto Supabase creado y configurado correctamente
  Para poder usar autenticación y persistencia desde el primer día de desarrollo

  Scenario: Proyecto creado en la región correcta
    Given que accedo al panel de Supabase con mi cuenta
    When creo un nuevo proyecto con nombre "aiip"
    Then el proyecto se crea en la región EU (Frankfurt)
    And el proyecto tiene estado "Active"

  Scenario: Credenciales disponibles y anotadas
    Given que el proyecto Supabase está activo
    When accedo a Settings > API
    Then obtengo la URL del proyecto (SUPABASE_URL)
    And obtengo la anon/public key (SUPABASE_ANON_KEY)
    And obtengo la service_role key (SUPABASE_SERVICE_KEY)
    And las tres credenciales están registradas en .env.example

  Scenario: Conexión verificada desde entorno local
    Given que las credenciales están en el fichero .env
    When ejecuto el script de smoke test de conexión
    Then la conexión a Supabase responde con status 200
    And no hay errores de autenticación ni de red


# ─────────────────────────────────────────────────────────────
# T-02 — API key de Google AI obtenida y verificada
# ─────────────────────────────────────────────────────────────

@done
Feature: T-02 Google AI API key operativa

  Como desarrollador del proyecto AIIP
  Quiero tener una API key de Google AI válida para Gemini Flash
  Para poder hacer llamadas al LLM desde el pipeline RAG

  Scenario: API key obtenida en Google AI Studio
    Given que accedo a aistudio.google.com con mi cuenta Google
    When creo una nueva API key
    Then la key tiene acceso al modelo "gemini-2.5-flash"
    And la key está registrada como GOOGLE_API_KEY en .env.example

  Scenario: Llamada de verificación al modelo
    Given que la API key está en el fichero .env
    When ejecuto el script de smoke test con un prompt mínimo
    Then el modelo devuelve una respuesta válida en menos de 10 segundos
    And no hay errores de cuota ni de autenticación

  Scenario: Modelo configurado como variable de entorno, no hardcodeado
    Given que el smoke test funciona
    When reviso el código del test
    Then el nombre del modelo se lee de la variable LLM_MODEL en .env
    And no aparece la cadena "gemini" hardcodeada en ningún fichero .py


# ─────────────────────────────────────────────────────────────
# T-03 — Token de Hugging Face configurado
# ─────────────────────────────────────────────────────────────

@done
Feature: T-03 Token de Hugging Face operativo

  Como desarrollador del proyecto AIIP
  Quiero tener un token de Hugging Face con permisos de lectura
  Para poder descargar el modelo de embeddings BAAI/bge-m3

  Scenario: Token creado con permisos correctos
    Given que accedo a huggingface.co/settings/tokens con mi cuenta
    When creo un token de tipo "Read"
    Then el token tiene acceso a modelos públicos
    And está registrado como HF_TOKEN en .env.example

  Scenario: Descarga del modelo verificada
    Given que el token está en el fichero .env
    When ejecuto el script de smoke test de embeddings
    Then el modelo BAAI/bge-m3 se descarga o carga desde caché correctamente
    And genera un vector de embeddings para la frase de prueba "inmunodeficiencia primaria"
    And el vector tiene dimensión 1024


# ─────────────────────────────────────────────────────────────
# T-04 — Estructura de carpetas en Google Drive
# ─────────────────────────────────────────────────────────────

@done
Feature: T-04 Google Drive estructurado para Colab

  Como desarrollador del proyecto AIIP
  Quiero tener una estructura de carpetas clara en Google Drive
  Para que los notebooks de Colab tengan rutas consistentes y reproducibles

  Scenario: Estructura de carpetas creada
    Given que accedo a Google Drive con mi cuenta
    When creo la estructura de carpetas del proyecto
    Then existe la carpeta raíz "AIIP/"
    And dentro existe "AIIP/notebooks/" para los notebooks de desarrollo
    And dentro existe "AIIP/data/raw/" para fuentes originales de la KB
    And dentro existe "AIIP/data/processed/" para chunks procesados
    And dentro existe "AIIP/chroma_db/" para la persistencia de ChromaDB

  Scenario: Ruta base documentada y accesible desde Colab
    Given que la estructura existe en Drive
    When monto Drive en un notebook de Colab con drive.mount('/content/drive')
    Then la ruta base DRIVE_BASE_PATH = '/content/drive/MyDrive/AIIP' es accesible
    And la ruta está registrada en .env.example como variable DRIVE_BASE_PATH


# ─────────────────────────────────────────────────────────────
# T-05 — .env.example y .gitignore configurados en el repo
# ─────────────────────────────────────────────────────────────

@done
Feature: T-05 Gestión segura de credenciales en el repositorio

  Como desarrollador del proyecto AIIP
  Quiero que el repositorio tenga .env.example y .gitignore correctos
  Para que ninguna credencial llegue a commits y cualquier colaborador pueda arrancar el entorno

  Scenario: .env.example creado con todas las variables necesarias
    Given que el repositorio está inicializado
    When creo el fichero .env.example en la raíz del repo
    Then contiene SUPABASE_URL con valor de ejemplo
    And contiene SUPABASE_ANON_KEY con valor de ejemplo
    And contiene SUPABASE_SERVICE_KEY con valor de ejemplo
    And contiene GOOGLE_API_KEY con valor de ejemplo
    And contiene LLM_MODEL con valor por defecto "gemini-2.5-flash"
    And contiene HF_TOKEN con valor de ejemplo
    And contiene DRIVE_BASE_PATH con valor por defecto "/content/drive/MyDrive/AIIP"
    And ningún valor real aparece en el fichero — solo placeholders

  Scenario: .gitignore excluye el fichero .env
    Given que existe un fichero .env con credenciales reales
    When ejecuto "git status" en el repositorio
    Then el fichero .env no aparece como fichero a commitear
    And el fichero .env.example sí aparece como fichero trackeado

  Scenario: Nuevo colaborador puede arrancar el entorno desde cero
    Given que un colaborador clona el repositorio
    When copia .env.example a .env y rellena sus propias credenciales
    Then puede ejecutar el smoke test de conexión a Supabase sin errores
    And puede ejecutar el smoke test de Google AI sin errores
    And puede ejecutar el smoke test de embeddings sin errores


# ─────────────────────────────────────────────────────────────
# T-06 — Script de smoke test del entorno completo
# ─────────────────────────────────────────────────────────────

@done
Feature: T-06 Smoke test de verificación del entorno

  Como desarrollador del proyecto AIIP
  Quiero un script que verifique todos los servicios de una sola vez
  Para confirmar que el entorno está listo antes de arrancar E-02 y E-03

  Scenario: Smoke test ejecuta todas las verificaciones
    Given que el fichero .env tiene credenciales válidas
    When ejecuto "python tests/smoke_test_env.py"
    Then el script verifica la conexión a Supabase
    And verifica la llamada a Gemini Flash
    And verifica la carga del modelo bge-m3
    And verifica que las rutas de Drive existen (si se ejecuta en Colab)
    And imprime un resumen con el estado de cada verificación

  Scenario: Smoke test falla con mensaje claro si falta una variable
    Given que el fichero .env no tiene definida GOOGLE_API_KEY
    When ejecuto "python tests/smoke_test_env.py"
    Then el script imprime "ERROR: GOOGLE_API_KEY no definida en .env"
    And termina con código de salida 1
    And no lanza una excepción no controlada
