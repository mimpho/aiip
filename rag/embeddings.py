from typing import List

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class BGEEmbeddings(Embeddings):
    def __init__(self) -> None:
        self._model = SentenceTransformer("BAAI/bge-m3")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._model.encode(text).tolist()


def get_embeddings() -> Embeddings:
    return BGEEmbeddings()
