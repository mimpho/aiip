"""Step definitions — E-11 T-02 Re-medición RAGAS + peso adaptativo de BM25 (D-061)."""

import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e11_t02_bm25_adaptive_weight.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]

_REMEDICION_SKIP_REASON = (
    "E-11 T-02: requiere ejecutar scripts/run_ragas_eval.py (dos veces, D-061) "
    "sobre los 32 casos con el LLM evaluador real y la revisión de Marcos — "
    "coste/tiempo no trivial, mismo patrón que E-09 T-05 (test_e09_t05.py)."
)


@pytest.fixture(scope="session")
def embeddings_model():
    from rag.embeddings import get_embeddings

    return get_embeddings()


# ── Señal léxica fuerte: escenario 1 (D-061, criterio determinista) ─────────────

_SIGNAL_CORPUS = [
    "El tratamiento con inmunoglobulinas requiere seguimiento periódico.",
    "La fiebre y el cansancio son síntomas frecuentes en infecciones respiratorias.",
    "El especialista revisa la analítica cada tres meses en consulta.",
    "Los antibióticos se prescriben tras confirmar la infección bacteriana.",
    "El Hospital Clínic de Barcelona tiene servicio de inmunología pediátrica.",
]


def _bm25_retriever_de_prueba():
    from langchain_community.retrievers import BM25Retriever

    return BM25Retriever.from_texts(_SIGNAL_CORPUS)


@given("una consulta de usuario", target_fixture="consultas_senal")
def consultas_senal():
    return {
        # (a) mayúscula no inicial de frase -> con señal
        "con_mayuscula": "¿Qué hospitales de Barcelona tienen inmunología?",
        # (b) palabra de baja frecuencia en el corpus (IDF > average_idf) -> con señal
        "con_rareza": "¿Qué pasa con la fiebre?",
        # ni mayúscula no inicial ni término raro -> sin señal
        "conceptual": "¿qué es una inmunodeficiencia primaria?",
    }


@when(
    "se evalúa si tiene señal léxica fuerte con has_lexical_signal",
    target_fixture="resultado_senal",
)
def resultado_senal(consultas_senal):
    from rag.retriever import has_lexical_signal

    bm25 = _bm25_retriever_de_prueba()
    return {
        etiqueta: has_lexical_signal(pregunta, bm25)
        for etiqueta, pregunta in consultas_senal.items()
    }


@then(
    parsers.parse(
        'la consulta se clasifica como "con señal" o "sin señal" de forma '
        "determinista, sin LLM de por medio"
    )
)
def la_consulta_se_clasifica(resultado_senal):
    assert resultado_senal["con_mayuscula"] is True
    assert resultado_senal["con_rareza"] is True
    assert resultado_senal["conceptual"] is False

    # Determinismo: repetir la misma llamada da el mismo resultado (sin LLM de por
    # medio, no hay variabilidad entre invocaciones).
    from rag.retriever import has_lexical_signal

    bm25 = _bm25_retriever_de_prueba()
    for etiqueta, pregunta in {
        "con_mayuscula": "¿Qué hospitales de Barcelona tienen inmunología?",
        "con_rareza": "¿Qué pasa con la fiebre?",
        "conceptual": "¿qué es una inmunodeficiencia primaria?",
    }.items():
        assert has_lexical_signal(pregunta, bm25) == resultado_senal[etiqueta]


# ── Recálculo por consulta: escenario 2 (D-061) ─────────────────────────────────

@given(
    "RAGPipeline con el retriever híbrido ya construido y cacheado",
    target_fixture="retriever_cacheado",
)
def retriever_cacheado(embeddings_model, tmp_path):
    from rag.retriever import get_hybrid_retriever, get_retriever

    vs = get_retriever(embeddings_model, str(tmp_path), "e11_t02_test")
    vs.add_texts(_SIGNAL_CORPUS)
    return get_hybrid_retriever(vs, top_k=3)


@when(
    "se invoca retrieve()/query() para una consulta concreta",
    target_fixture="pesos_por_consulta",
)
def pesos_por_consulta(retriever_cacheado):
    from rag.retriever import apply_adaptive_bm25_weight

    bm25_antes = retriever_cacheado.retrievers[0]

    apply_adaptive_bm25_weight(
        retriever_cacheado, "¿Qué hospitales de Barcelona tienen inmunología?"
    )
    pesos_con_senal = list(retriever_cacheado.weights)

    apply_adaptive_bm25_weight(
        retriever_cacheado, "¿qué es una inmunodeficiencia primaria?"
    )
    pesos_sin_senal = list(retriever_cacheado.weights)

    return {
        "bm25_antes": bm25_antes,
        "bm25_despues": retriever_cacheado.retrievers[0],
        "con_senal": pesos_con_senal,
        "sin_senal": pesos_sin_senal,
    }


@then(
    "el peso de EnsembleRetriever (weights) se actualiza para esa consulta antes "
    "de invocar el retriever, sin reconstruir el índice BM25 desde cero"
)
def el_peso_se_actualiza_sin_reconstruir(pesos_por_consulta):
    assert pesos_por_consulta["con_senal"] != pesos_por_consulta["sin_senal"], (
        "El peso no cambió entre una consulta con señal y otra sin señal"
    )
    assert pesos_por_consulta["bm25_antes"] is pesos_por_consulta["bm25_despues"], (
        "El objeto BM25Retriever cambió de identidad — se reconstruyó el índice "
        "en vez de mutar el peso"
    )


# ── BM25 se pondera solo ante señal léxica fuerte: escenario 3 (D-061) ──────────

@given(
    "get_hybrid_retriever en rag/retriever.py ya ajustado para aceptar un peso "
    "actualizable",
    target_fixture="retriever_ajustable",
)
def retriever_ajustable(embeddings_model, tmp_path):
    from rag.retriever import get_hybrid_retriever, get_retriever

    vs = get_retriever(embeddings_model, str(tmp_path), "e11_t02_test_2")
    vs.add_texts(_SIGNAL_CORPUS)
    return get_hybrid_retriever(vs, top_k=3)


@when(
    parsers.parse('se recupera contexto para una consulta "con señal"'),
    target_fixture="pesos_con_y_sin_senal",
)
def pesos_con_y_sin_senal(retriever_ajustable):
    from rag.retriever import apply_adaptive_bm25_weight

    apply_adaptive_bm25_weight(
        retriever_ajustable, "¿Qué hospitales de Barcelona tienen inmunología?"
    )
    peso_bm25_con_senal = retriever_ajustable.weights[0]

    apply_adaptive_bm25_weight(
        retriever_ajustable, "¿qué es una inmunodeficiencia primaria?"
    )
    peso_bm25_sin_senal = retriever_ajustable.weights[0]

    return peso_bm25_con_senal, peso_bm25_sin_senal


@then(
    parsers.parse(
        'el peso de BM25 aplicado es mayor que el de una consulta "sin señal" en '
        "la misma ejecución"
    )
)
def el_peso_bm25_es_mayor_con_senal(pesos_con_y_sin_senal):
    peso_con_senal, peso_sin_senal = pesos_con_y_sin_senal
    assert peso_con_senal > peso_sin_senal


# ── Escenarios sin TDD (script real, coste/tiempo no trivial) ───────────────────
#
# Mismo criterio que D-050/D-051/D-056 aplicó a scripts/run_ragas_eval.py y
# scripts/smoke_test_rag.py: sin asserts contra un LLM evaluador no determinista,
# verificación manual documentada. Se marcan explícitamente como skip (no pass
# falso) hasta ejecutar la re-medición real (ver "Procedimiento de las dos
# re-mediciones" en tasks/E11-T02-plan.md).

# --- Línea base ---


@given(
    "el fichero de resultados de E-09 T-05 (corpus sin ampliar, peso uniforme "
    "0.4/0.6) en tests/eval/results/e09_t02_ragas_full_scores.json",
    target_fixture="fichero_e09_t05",
)
def fichero_e09_t05():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when("se prepara la primera ejecución de scripts/run_ragas_eval.py de esta tarea")
def se_prepara_primera_ejecucion(fichero_e09_t05):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "el fichero se respalda como referencia de E-09 (peso uniforme, corpus sin "
    "ampliar) y se resetea a vacío"
)
def fichero_se_respalda_referencia_e09():
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "se documenta explícitamente que el reset es necesario porque la ejecución "
    "es incremental y sin resetear no mediría nada nuevo sobre el corpus ampliado"
)
def se_documenta_necesidad_reset():
    pytest.skip(_REMEDICION_SKIP_REASON)


@given(
    "el fichero de resultados reseteado y el retriever con el peso uniforme "
    "0.4/0.6 aún sin modificar",
    target_fixture="fichero_reseteado",
)
def fichero_reseteado():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when(
    parsers.parse(
        "se ejecuta scripts/run_ragas_eval.py sobre los 32 casos "
        "(informativo + otro_idioma)"
    )
)
def se_ejecuta_ragas_linea_base(fichero_reseteado):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then("se obtiene Context Precision y Context Recall de línea base post-ampliación")
def se_obtiene_cp_cr_linea_base():
    pytest.skip(_REMEDICION_SKIP_REASON)


@then("el resultado se respalda antes de tocar el peso de BM25")
def resultado_se_respalda_antes_de_bm25():
    pytest.skip(_REMEDICION_SKIP_REASON)


# --- Regresión / mejora ---


@given(
    parsers.parse(
        "los 6 casos que empeoraron en la retrospectiva de E-09 T-05 (eval_64, "
        "eval_17, eval_16, eval_19, eval_02, eval_04 — conceptuales, sin señal "
        "léxica fuerte)"
    ),
    target_fixture="casos_que_empeoraron",
)
def casos_que_empeoraron():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when("se recuperan con el retriever ajustado", target_fixture="recuperados_regresion")
def recuperados_con_retriever_ajustado_regresion(casos_que_empeoraron):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "su Context Precision no empeora frente a la línea base post-ampliación (peso "
    "BM25 ~0 en estos casos, al no tener señal léxica)"
)
def context_precision_no_empeora(recuperados_regresion):
    pytest.skip(_REMEDICION_SKIP_REASON)


@given(
    "los 4 casos que mejoraron en la retrospectiva de E-09 T-05 (eval_07, "
    "eval_11, eval_01, eval_21)",
    target_fixture="casos_que_mejoraron",
)
def casos_que_mejoraron():
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "su Context Precision se mantiene igual o mejor que con la línea base "
    "post-ampliación"
)
def context_precision_se_mantiene_o_mejora(casos_que_mejoraron):
    pytest.skip(_REMEDICION_SKIP_REASON)


# --- Fallback ---


@given(
    "que el peso adaptativo no llega a completarse dentro del margen de la tarea",
    target_fixture="fallback_necesario",
)
def fallback_necesario():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when(
    "se aplica la vía barata de bajar el peso fijo de BM25 para todas las "
    "consultas por igual"
)
def se_aplica_fallback(fallback_necesario):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then("se documenta explícitamente que se optó por el fallback y por qué")
def se_documenta_fallback():
    pytest.skip(_REMEDICION_SKIP_REASON)


@then("se re-mide igual que si fuera la solución adaptativa")
def se_remide_como_adaptativa():
    pytest.skip(_REMEDICION_SKIP_REASON)


# --- Cierre: re-medición final ---


@given(
    "el fichero de resultados con la línea base post-ampliación ya respaldado",
    target_fixture="fichero_baseline_respaldado",
)
def fichero_baseline_respaldado():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when("se prepara la segunda ejecución de scripts/run_ragas_eval.py de esta tarea")
def se_prepara_segunda_ejecucion(fichero_baseline_respaldado):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "el fichero se resetea a vacío antes de medir con el peso ya ajustado "
    "(adaptativo o fallback)"
)
def fichero_se_resetea_antes_de_medir():
    pytest.skip(_REMEDICION_SKIP_REASON)


@given(
    "el retriever ya ajustado (adaptativo o fallback) y el fichero de resultados "
    "reseteado",
    target_fixture="retriever_ajustado_y_fichero_reseteado",
)
def retriever_ajustado_y_fichero_reseteado():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when("se re-ejecuta scripts/run_ragas_eval.py sobre los 32 casos")
def se_reejecuta_ragas_final(retriever_ajustado_y_fichero_reseteado):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then("se obtiene Context Precision y Context Recall final")
def se_obtiene_cp_cr_final():
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "se documenta el triple antes/después separando el efecto de la KB del "
    "efecto del ajuste de BM25"
)
def se_documenta_triple_antes_despues():
    pytest.skip(_REMEDICION_SKIP_REASON)


@given("los resultados de la re-medición final", target_fixture="resultados_finales")
def resultados_finales():
    pytest.skip(_REMEDICION_SKIP_REASON)


@when("Marcos los revisa")
def marcos_los_revisa(resultados_finales):
    pytest.skip(_REMEDICION_SKIP_REASON)


@then(
    "confirma si el ajuste queda cerrado (adaptativo o fallback) o si hace falta "
    "iterar antes de pasar a las siguientes tareas de la épica"
)
def marcos_confirma_ajuste():
    pytest.skip(_REMEDICION_SKIP_REASON)
