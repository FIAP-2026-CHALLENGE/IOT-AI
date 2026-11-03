"""Formatos de entrada e saída da API (o que vira JSON). Os objetos do domínio não saem direto."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AnimalSaida(BaseModel):
    id: int
    nome: str
    especie: str
    raca: str
    peso_cadastro: Decimal
    nascimento: date | None


class LeituraEntrada(BaseModel):
    animal_id: int = Field(gt=0)
    peso: Decimal = Field(gt=0, description="Peso em kg medido pela balança")


class LeituraSaida(BaseModel):
    id: int
    peso: Decimal
    data: datetime


class ProblemaSaida(BaseModel):
    codigo: str
    descricao: str


class TriagemPesoSaida(BaseModel):
    leitura_id: int
    recomendacao_id: int
    animal: str
    nivel: str
    problemas: list[ProblemaSaida]
    texto: str
    ficha_usada: str | None
    usou_llm: bool
    motivo_sem_llm: str | None


class RelatoSaida(BaseModel):
    relato_id: int
    recomendacao_id: int
    nivel: str
    texto: str
    imagem_url: str | None
    sinais_de_emergencia: list[str]
    usou_llm: bool
    motivo_sem_llm: str | None


class PlanoSaida(BaseModel):
    recomendacao_id: int
    ficha_usada: str
    idade: str
    texto: str
    usou_llm: bool
    motivo_sem_llm: str | None


class RecomendacaoSaida(BaseModel):
    id: int
    origem: str
    nivel: str
    texto: str
    data: datetime
