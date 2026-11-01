"""Contrato do LLM: o serviço conhece só esta interface, e não o Gemini.

Assim o Gemini real entra em produção e um dublê entra nos testes, sem o
serviço mudar uma linha.
"""
from dataclasses import dataclass
from typing import Protocol


class LLMIndisponivelError(RuntimeError):
    """O LLM não respondeu (rede, cota, chave inválida). O serviço tem um plano B."""


@dataclass(frozen=True)
class Imagem:
    dados: bytes
    mime_type: str  # ex.: image/jpeg


class ClienteLLM(Protocol):
    def gerar(self, instrucoes: str, prompt: str, imagem: Imagem | None = None) -> str:
        """`instrucoes` são as regras fixas do assistente; `prompt`, o caso da vez."""
        ...
