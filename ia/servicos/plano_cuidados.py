"""Plano de cuidados por raça (origem CUIDADO_RACA): a ficha da base personalizada pelo LLM com a idade e o peso."""
from dataclasses import dataclass
from datetime import date

from dominio.animal import idade_em_texto
from dominio.cuidados import encontrar_ficha
from dominio.peso import Nivel
from dominio.recomendacao import NovaRecomendacao, Origem
from llm.cliente import ClienteLLM, LLMIndisponivelError
from servicos.prompts import INSTRUCOES_CUIDADOS, prompt_cuidados, texto_cuidados_sem_llm
from servicos.triagem_peso import AnimalNaoEncontradoError, Animais, Cuidados, Recomendacoes


class FichaNaoEncontradaError(LookupError):
    """Nem a raça nem a ficha genérica (SRD) da espécie estão na base."""


@dataclass(frozen=True)
class ResultadoPlano:
    recomendacao_id: int
    ficha_usada: str
    idade: str
    texto: str
    usou_llm: bool
    motivo_sem_llm: str | None


class PlanoCuidadosServico:
    def __init__(self, animais: Animais, cuidados: Cuidados, recomendacoes: Recomendacoes, llm: ClienteLLM):
        self._animais = animais
        self._cuidados = cuidados
        self._recomendacoes = recomendacoes
        self._llm = llm

    def gerar(self, animal_id: int, hoje: date | None = None) -> ResultadoPlano:
        animal = self._animais.buscar_por_id(animal_id)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {animal_id} não encontrado.")
        ficha = encontrar_ficha(animal.raca, self._cuidados.listar_por_especie(animal.especie))
        if ficha is None:
            raise FichaNaoEncontradaError(f"Sem ficha de cuidados para {animal.especie} na base.")

        idade = idade_em_texto(animal.nascimento, hoje or date.today())
        motivo_sem_llm = None
        try:
            texto = self._llm.gerar(INSTRUCOES_CUIDADOS, prompt_cuidados(animal, idade, ficha))
        except LLMIndisponivelError as erro:
            motivo_sem_llm = str(erro)
            texto = texto_cuidados_sem_llm(ficha)

        # plano preventivo é informativo: não é alerta
        recomendacao_id = self._recomendacoes.salvar(
            NovaRecomendacao(animal.id, Origem.CUIDADO_RACA, Nivel.NORMAL, texto)
        )
        return ResultadoPlano(recomendacao_id, ficha.raca, idade, texto, motivo_sem_llm is None, motivo_sem_llm)
