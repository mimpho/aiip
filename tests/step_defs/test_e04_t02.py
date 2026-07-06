"""Step definitions — E-04 T-02 Embeddings y retriever con ChromaDB."""

import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t02_embeddings_retriever.feature")

IDP_CHUNKS_ES = [
    "La inmunodeficiencia primaria es una enfermedad genética del sistema inmune.",
    "Los síntomas de inmunodeficiencia incluyen infecciones frecuentes y graves.",
    "El tratamiento puede incluir terapia de reemplazo con inmunoglobulinas.",
    "Las inmunodeficiencias primarias afectan al sistema inmunológico desde el nacimiento.",
    "La agammaglobulinemia de Bruton es un tipo de IDP ligada al cromosoma X.",
    "Los pacientes con IDP necesitan seguimiento médico especializado y continuo.",
    "La deficiencia selectiva de IgA es la inmunodeficiencia primaria más común.",
    "El diagnóstico precoz de la IDP mejora significativamente el pronóstico.",
    "Los trasplantes de médula ósea pueden curar algunas inmunodeficiencias primarias.",
    "Los niños con IDP tienen mayor riesgo de infecciones bacterianas recurrentes.",
]

IDP_CHUNKS_EN = [
    "Primary immunodeficiency is a genetic disorder affecting the immune system.",
    "Symptoms of immunodeficiency include frequent and severe infections.",
    "Treatment may include immunoglobulin replacement therapy.",
    "Primary immunodeficiencies affect the immune system from birth.",
    "Bruton's agammaglobulinemia is an X-linked type of primary immunodeficiency.",
]


@pytest.fixture(scope="session")
def embeddings_model():
    from rag.embeddings import get_embeddings

    return get_embeddings()


# ── Background ───────────────────────────────────────────────────────────────

@given('ChromaDB está inicializado con la colección "family_test"', target_fixture="ctx")
def chroma_inicializado(tmp_path, embeddings_model):
    from rag.retriever import get_retriever

    vs = get_retriever(embeddings_model, str(tmp_path), "family_test")
    return {"vectorstore": vs, "embeddings": embeddings_model}


# ── Scenario 1: Dimensión correcta del embedding bge-m3 ─────────────────────

@given("el modelo bge-m3 está cargado", target_fixture="emb_model")
def modelo_cargado(embeddings_model):
    return embeddings_model


@when(
    'genero el embedding del texto "¿Qué es una inmunodeficiencia primaria?"',
    target_fixture="embedding_result",
)
def genero_embedding(emb_model):
    return emb_model.embed_query("¿Qué es una inmunodeficiencia primaria?")


@then("el vector resultante tiene dimensión 1024")
def vector_dimension_1024(embedding_result):
    assert len(embedding_result) == 1024


# ── Scenario 2: Retrieval con documentos indexados devuelve resultados ───────

@given('la colección "family_test" contiene 10 chunks sobre IDP')
def coleccion_con_chunks_idp(ctx):
    ctx["vectorstore"].add_texts(IDP_CHUNKS_ES)


@when(
    'ejecuto el retriever con la query "síntomas de inmunodeficiencia"',
    target_fixture="retrieval_results",
)
def retriever_query_sintomas(ctx):
    from rag.retriever import distance_to_similarity

    vs = ctx["vectorstore"]
    try:
        raw = vs.similarity_search_with_score("síntomas de inmunodeficiencia", k=5)
        return {
            "results": [(doc, distance_to_similarity(score)) for doc, score in raw],
            "exception": None,
        }
    except Exception as exc:
        return {"results": None, "exception": exc}


@then("devuelve entre 1 y 5 chunks")
def devuelve_entre_1_y_5(retrieval_results):
    assert retrieval_results["exception"] is None, retrieval_results["exception"]
    assert 1 <= len(retrieval_results["results"]) <= 5


@then("cada chunk tiene un score de similitud mayor que 0.0")
def score_mayor_que_cero(retrieval_results):
    for _, score in retrieval_results["results"]:
        assert score > 0.0, f"Score inesperado: {score}"


# ── Scenario 3: Retrieval cross-lingual castellano sobre chunks en inglés ────

@given(
    'la colección "family_test" contiene chunks en inglés sobre primary immunodeficiency'
)
def coleccion_chunks_ingles(ctx):
    ctx["vectorstore"].add_texts(IDP_CHUNKS_EN)


@when(
    'ejecuto el retriever con la query en castellano "¿cuáles son los síntomas?"',
    target_fixture="retrieval_results",
)
def retriever_query_castellano(ctx):
    from rag.retriever import distance_to_similarity

    vs = ctx["vectorstore"]
    try:
        raw = vs.similarity_search_with_score("¿cuáles son los síntomas?", k=5)
        return {
            "results": [(doc, distance_to_similarity(score)) for doc, score in raw],
            "exception": None,
        }
    except Exception as exc:
        return {"results": None, "exception": exc}


@then("devuelve al menos 1 chunk relevante")
def devuelve_al_menos_1(retrieval_results):
    assert retrieval_results["exception"] is None, retrieval_results["exception"]
    assert len(retrieval_results["results"]) >= 1


# ── Scenario 4: Retrieval con colección vacía devuelve lista vacía ───────────

@given('la colección "family_test" está vacía')
def coleccion_vacia(ctx):
    pass  # Vectorstore created in Background without documents


@when("ejecuto el retriever con cualquier query", target_fixture="retrieval_results")
def retriever_query_cualquiera(ctx):
    from rag.retriever import distance_to_similarity

    vs = ctx["vectorstore"]
    try:
        raw = vs.similarity_search_with_score("cualquier consulta", k=5)
        return {
            "results": [(doc, distance_to_similarity(score)) for doc, score in raw],
            "exception": None,
        }
    except Exception as exc:
        return {"results": None, "exception": exc}


@then("devuelve una lista vacía")
def devuelve_lista_vacia(retrieval_results):
    assert retrieval_results["exception"] is None, retrieval_results["exception"]
    assert retrieval_results["results"] == []


@then("no se lanza ninguna excepción")
def no_excepcion(retrieval_results):
    assert retrieval_results["exception"] is None, (
        f"Se lanzó excepción inesperada: {retrieval_results['exception']}"
    )
