"""Triagem de peso: junta a regra, a ficha da raça (RAG) e o LLM, e registra o resultado.

Fluxo: animal -> ficha da raça -> histórico -> regra de peso -> texto (LLM ou regra) -> T_AI_RECOMMENDATION.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from dominio.animal import Animal
from dominio.cuidados import FichaCuidado, encontrar_ficha
from dominio.peso import LEITURAS_DE_REFERENCIA, LeituraInvalidaError, Nivel, Problema, avaliar_peso
from dominio.recomendacao import NovaRecomendacao, Origem
from llm.cliente import ClienteLLM, LLMIndisponivelError
from servicos.prompts import INSTRUCOES_TRIAGEM, prompt_peso, texto_sem_llm


class AnimalNaoEncontradoError(LookupError):
    pass


# O que o serviço precisa de cada repositório. Os do Oracle e os dublês dos testes cumprem isso.
class Animais(Protocol):
    def buscar_por_id(self, animal_id: int) -> Animal | None: ...


class Leituras(Protocol):
    def historico(self, animal_id: int, limite: int, antes_do_id: int | None = None) -> list[Decimal]: ...

    def registrar(self, animal_id: int, peso: Decimal) -> int: ...


class Cuidados(Protocol):
    def listar_por_especie(self, especie: str) -> list[FichaCuidado]: ...


class Recomendacoes(Protocol):
    def salvar(self, recomendacao: NovaRecomendacao) -> int: ...


@dataclass(frozen=True)
class ResultadoTriagem:
    recomendacao_id: int
    animal: Animal
    nivel: Nivel
    problemas: tuple[Problema, ...]
    texto: str
    ficha_usada: str | None
    usou_llm: bool
    motivo_sem_llm: str | None  # por que o texto saiu da regra (None quando o LLM respondeu)


class TriagemPesoServico:
    def __init__(
        self,
        animais: Animais,
        leituras: Leituras,
        cuidados: Cuidados,
        recomendacoes: Recomendacoes,
        llm: ClienteLLM,
    ):
        self._animais = animais
        self._leituras = leituras
        self._cuidados = cuidados
        self._recomendacoes = recomendacoes
        self._llm = llm

    def processar_leitura(self, animal_id: int, peso: Decimal) -> tuple[int, ResultadoTriagem]:
        """Caminho da balança: grava a leitura em T_EXAM_READING e avalia. Devolve (leitura_id, resultado).

        Confere o animal e o peso antes de gravar, para não deixar leitura inválida no banco.
        """
        if self._animais.buscar_por_id(animal_id) is None:
            raise AnimalNaoEncontradoError(f"Animal {animal_id} não encontrado.")
        if peso <= 0:
            raise LeituraInvalidaError(f"Peso inválido: {peso} kg.")
        leitura_id = self._leituras.registrar(animal_id, peso)
        # a leitura recém-gravada fica fora da própria média (antes_do_id)
        return leitura_id, self.avaliar(animal_id, peso, leitura_id=leitura_id)

    def avaliar(self, animal_id: int, peso: Decimal, leitura_id: int | None = None) -> ResultadoTriagem:
        animal = self._animais.buscar_por_id(animal_id)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {animal_id} não encontrado.")

        ficha = encontrar_ficha(animal.raca, self._cuidados.listar_por_especie(animal.especie))
        historico = self._leituras.historico(animal_id, LEITURAS_DE_REFERENCIA, antes_do_id=leitura_id)
        resultado = avaliar_peso(
            peso, ficha.faixa if ficha else None, historico, peso_cadastro=animal.peso_cadastro
        )

        texto, motivo_sem_llm = self._escrever_recomendacao(animal, resultado, ficha)
        recomendacao_id = self._recomendacoes.salvar(
            NovaRecomendacao(animal.id, Origem.PESO, resultado.nivel, texto)
        )
        return ResultadoTriagem(
            recomendacao_id=recomendacao_id,
            animal=animal,
            nivel=resultado.nivel,
            problemas=resultado.problemas,
            texto=texto,
            ficha_usada=ficha.raca if ficha else None,
            usou_llm=motivo_sem_llm is None,
            motivo_sem_llm=motivo_sem_llm,
        )

    def _escrever_recomendacao(self, animal, resultado, ficha) -> tuple[str, str | None]:
        """Devolve o texto e, quando ele não veio do LLM, o motivo."""
        # NORMAL não precisa de interpretação: economiza cota do LLM (a balança lê a cada poucos segundos)
        if resultado.nivel == Nivel.NORMAL:
            return texto_sem_llm(resultado), "nível NORMAL não usa o LLM"
        try:
            return self._llm.gerar(INSTRUCOES_TRIAGEM, prompt_peso(animal, resultado, ficha)), None
        except LLMIndisponivelError as erro:
            # plano B: o tutor ainda recebe a orientação baseada na regra, e o motivo não se perde
            return texto_sem_llm(resultado), str(erro)
