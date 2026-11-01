"""Dublês: peças falsas que substituem o Oracle e o Gemini nos testes.

Respondem sempre o que o teste combinou e anotam o que receberam, para o
teste conferir o que o serviço pediu (ex.: qual prompt foi para o LLM).
"""
from decimal import Decimal

from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.recomendacao import NovaRecomendacao
from llm.cliente import Imagem, LLMIndisponivelError


class AnimaisFalsos:
    def __init__(self, *animais: Animal):
        self._por_id = {a.id: a for a in animais}

    def buscar_por_id(self, animal_id: int) -> Animal | None:
        return self._por_id.get(animal_id)


class LeiturasFalsas:
    def __init__(self, historico: list[Decimal]):
        self._historico = historico
        self.chamadas: list[dict] = []

    def historico(self, animal_id: int, limite: int, antes_do_id: int | None = None) -> list[Decimal]:
        self.chamadas.append({"animal_id": animal_id, "limite": limite, "antes_do_id": antes_do_id})
        return self._historico[-limite:]


class CuidadosFalsos:
    def __init__(self, *fichas: FichaCuidado):
        self._fichas = fichas

    def listar_por_especie(self, especie: str) -> list[FichaCuidado]:
        return [f for f in self._fichas if f.especie == especie]


class RecomendacoesFalsas:
    def __init__(self):
        self.salvas: list[NovaRecomendacao] = []

    def salvar(self, recomendacao: NovaRecomendacao) -> int:
        self.salvas.append(recomendacao)
        return len(self.salvas)


class LLMFalso:
    def __init__(self, resposta: str = "Recomendação do LLM falso.", falhar: bool = False):
        self._resposta = resposta
        self._falhar = falhar
        self.pedidos: list[dict] = []

    def gerar(self, instrucoes: str, prompt: str, imagem: Imagem | None = None) -> str:
        self.pedidos.append({"instrucoes": instrucoes, "prompt": prompt, "imagem": imagem})
        if self._falhar:
            raise LLMIndisponivelError("Gemini fora do ar (simulado).")
        return self._resposta
