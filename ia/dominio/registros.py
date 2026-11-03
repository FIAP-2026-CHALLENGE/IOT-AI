"""O que já está gravado no Oracle e volta para a interface (histórico)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Leitura:
    id: int
    peso: Decimal
    data: datetime


@dataclass(frozen=True)
class RecomendacaoRegistrada:
    id: int
    origem: str  # PESO | RELATO | CUIDADO_RACA
    nivel: str  # NORMAL | ATENCAO | ALERTA
    texto: str
    data: datetime
