from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Animal:
    """Animal cadastrado na aplicação da CLYVO VET (T_CP_ANIMAIS, mantida pela API .NET)."""

    id: int
    nome: str
    especie: str  # DOG | CAT
    raca: str
    peso_cadastro: Decimal
