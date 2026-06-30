# E-04 T-01 — Setup de dependencias y estructura del módulo RAG
# Criterio: el entorno RAG arranca sin errores de importación ni de configuración

Feature: Setup del módulo RAG

  Como desarrollador
  Quiero tener instaladas y verificadas todas las dependencias del pipeline RAG
  Para poder arrancar el TDD sin problemas de entorno

  Scenario: Importación correcta de módulos RAG
    Given el entorno virtual tiene las dependencias instaladas
    When importo los módulos langchain, chromadb y sentence_transformers
    Then ningún módulo lanza ImportError

  Scenario: Variables de entorno requeridas presentes
    Given el fichero .env define GEMINI_API_KEY, HF_TOKEN y CHROMA_PATH
    When inicializo la configuración del pipeline RAG
    Then no se lanza EnvironmentError

  Scenario: Variable de entorno requerida ausente
    Given el fichero .env no define GEMINI_API_KEY
    When inicializo la configuración del pipeline RAG
    Then se lanza EnvironmentError con mensaje que menciona GEMINI_API_KEY

  Scenario: Estructura de módulo rag/ presente
    Given el repositorio está correctamente clonado
    When verifico la estructura de directorios
    Then existe el módulo rag/ con los ficheros __init__.py, pipeline.py, embeddings.py, retriever.py, generator.py y safety.py
