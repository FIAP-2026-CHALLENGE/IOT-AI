"""Dublês: peças falsas que substituem o Oracle, o storage e o Gemini nos testes.

Respondem sempre o que o teste combinou e anotam o que receberam, para o
teste conferir o que o serviço pediu (ex.: qual prompt foi para o LLM).
"""
from datetime import datetime
from decimal import Decimal

from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.recomendacao import NovaRecomendacao
from dominio.registros import Leitura, RecomendacaoRegistrada
from llm.cliente import Imagem, LLMIndisponivelError


class AnimaisFalsos:
    def __init__(self, *animais: Animal):
        self._por_id = {a.id: a for a in animais}

    def buscar_por_id(self, animal_id: int) -> Animal | None:
        return self._por_id.get(animal_id)

    def listar(self) -> list[Animal]:
        return list(self._por_id.values())


class LeiturasFalsas:
    def __init__(self, historico: list[Decimal]):
        self._historico = list(historico)
        self.chamadas: list[dict] = []
        self.registradas: list[tuple[int, Decimal]] = []

    def historico(self, animal_id: int, limite: int, antes_do_id: int | None = None) -> list[Decimal]:
        self.chamadas.append({"animal_id": animal_id, "limite": limite, "antes_do_id": antes_do_id})
        return self._historico[-limite:]

    def registrar(self, animal_id: int, peso: Decimal) -> int:
        self.registradas.append((animal_id, peso))
        return 100 + len(self.registradas)

    def listar(self, animal_id: int, limite: int = 30) -> list[Leitura]:
        return [Leitura(i + 1, p, datetime(2026, 11, 1, 10, i)) for i, p in enumerate(self._historico)]


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

    def listar_por_animal(self, animal_id: int, limite: int = 20) -> list[RecomendacaoRegistrada]:
        return [
            RecomendacaoRegistrada(i + 1, r.origem.value, r.nivel.name, r.texto, datetime(2026, 11, 1))
            for i, r in enumerate(self.salvas) if r.animal_id == animal_id
        ]


class RelatosFalsos:
    def __init__(self):
        self.salvos: list[dict] = []

    def salvar(self, animal_id: int, texto: str | None, imagem_url: str | None) -> int:
        self.salvos.append({"animal_id": animal_id, "texto": texto, "imagem_url": imagem_url})
        return len(self.salvos)


class FotosFalsas:
    def __init__(self):
        self.salvas: list[Imagem] = []

    def salvar(self, imagem: Imagem) -> str:
        self.salvas.append(imagem)
        return f"http://localhost:8000/uploads/foto{len(self.salvas)}.jpg"


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
