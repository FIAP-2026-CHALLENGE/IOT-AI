from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Animal:
    """Animal cadastrado na aplicação da CLYVO VET (T_CP_ANIMAIS, mantida pela API .NET)."""

    id: int
    nome: str
    especie: str  # DOG | CAT
    raca: str
    peso_cadastro: Decimal
    nascimento: date | None = None


def idade_em_texto(nascimento: date | None, hoje: date) -> str:
    """'2 anos e 3 meses', '5 meses' ou 'idade não informada'."""
    if nascimento is None or nascimento > hoje:
        return "idade não informada"
    meses = (hoje.year - nascimento.year) * 12 + (hoje.month - nascimento.month)
    if hoje.day < nascimento.day:
        meses -= 1
    anos, meses = divmod(meses, 12)
    if anos == 0:
        return f"{meses} {'mês' if meses == 1 else 'meses'}"
    texto = f"{anos} {'ano' if anos == 1 else 'anos'}"
    if meses:
        texto += f" e {meses} {'mês' if meses == 1 else 'meses'}"
    return texto
