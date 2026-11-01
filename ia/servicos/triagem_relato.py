"""Triagem do relato do tutor: texto (NLP via LLM) e foto (LLM multimodal), como define a Sprint 3.

Fluxo: valida -> guarda a foto no storage -> T_TUTOR_REPORT -> ficha da raça -> sinais de emergência
-> LLM (texto + foto na mesma chamada) -> nível (LLM, mas nunca abaixo de ALERTA se houver emergência)
-> T_AI_RECOMMENDATION.
"""
from dataclasses import dataclass
from typing import Protocol

from dominio.cuidados import encontrar_ficha
from dominio.peso import Nivel
from dominio.recomendacao import NovaRecomendacao, Origem
from dominio.relato import separar_nivel, sinais_de_emergencia, validar_relato
from llm.cliente import ClienteLLM, Imagem, LLMIndisponivelError
from servicos.prompts import INSTRUCOES_RELATO, prompt_relato, texto_relato_sem_llm
from servicos.triagem_peso import AnimalNaoEncontradoError, Animais, Cuidados, Recomendacoes


class Relatos(Protocol):
    def salvar(self, animal_id: int, texto: str | None, imagem_url: str | None) -> int: ...


class ArmazenamentoDeFotos(Protocol):
    def salvar(self, imagem: Imagem) -> str:
        """Guarda a foto fora do Oracle e devolve a URL (vai para T_TUTOR_REPORT.IMAGE_URL)."""
        ...


@dataclass(frozen=True)
class ResultadoRelato:
    relato_id: int
    recomendacao_id: int
    nivel: Nivel
    texto: str
    imagem_url: str | None
    sinais_de_emergencia: tuple[str, ...]
    usou_llm: bool
    motivo_sem_llm: str | None


class TriagemRelatoServico:
    def __init__(
        self,
        animais: Animais,
        cuidados: Cuidados,
        relatos: Relatos,
        recomendacoes: Recomendacoes,
        fotos: ArmazenamentoDeFotos,
        llm: ClienteLLM,
    ):
        self._animais = animais
        self._cuidados = cuidados
        self._relatos = relatos
        self._recomendacoes = recomendacoes
        self._fotos = fotos
        self._llm = llm

    def avaliar(self, animal_id: int, texto: str | None, imagem: Imagem | None = None) -> ResultadoRelato:
        animal = self._animais.buscar_por_id(animal_id)
        if animal is None:
            raise AnimalNaoEncontradoError(f"Animal {animal_id} não encontrado.")
        texto = validar_relato(
            texto,
            imagem.mime_type if imagem else None,
            len(imagem.dados) if imagem else None,
        )

        imagem_url = self._fotos.salvar(imagem) if imagem else None
        relato_id = self._relatos.salvar(animal_id, texto, imagem_url)

        ficha = encontrar_ficha(animal.raca, self._cuidados.listar_por_especie(animal.especie))
        sinais = sinais_de_emergencia(texto)
        prompt = prompt_relato(animal, texto, imagem is not None, sinais, ficha)

        motivo_sem_llm = None
        try:
            nivel_llm, orientacao = separar_nivel(self._llm.gerar(INSTRUCOES_RELATO, prompt, imagem))
            # modelo fora do formato: na dúvida, ATENCAO (pede acompanhamento sem alarmar)
            nivel = nivel_llm if nivel_llm is not None else Nivel.ATENCAO
        except LLMIndisponivelError as erro:
            motivo_sem_llm = str(erro)
            nivel, orientacao = Nivel.ATENCAO, texto_relato_sem_llm(sinais)

        if sinais:
            # regra no código: sinal de emergência é sempre ALERTA, mesmo que o modelo diga outra coisa
            nivel = Nivel.ALERTA

        recomendacao_id = self._recomendacoes.salvar(
            NovaRecomendacao(animal.id, Origem.RELATO, nivel, orientacao)
        )
        return ResultadoRelato(
            relato_id=relato_id,
            recomendacao_id=recomendacao_id,
            nivel=nivel,
            texto=orientacao,
            imagem_url=imagem_url,
            sinais_de_emergencia=tuple(sinais),
            usou_llm=motivo_sem_llm is None,
            motivo_sem_llm=motivo_sem_llm,
        )
