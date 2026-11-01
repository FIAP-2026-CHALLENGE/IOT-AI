from dataclasses import dataclass
from enum import Enum

from dominio.peso import Nivel


class Origem(Enum):
    # mesmos valores do CHECK de T_AI_RECOMMENDATION.SOURCE
    PESO = "PESO"
    RELATO = "RELATO"
    CUIDADO_RACA = "CUIDADO_RACA"


@dataclass(frozen=True)
class NovaRecomendacao:
    animal_id: int
    origem: Origem
    nivel: Nivel
    texto: str
