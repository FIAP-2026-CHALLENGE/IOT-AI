"""Regras objetivas de peso.

Ficam em código, e não no LLM, para o resultado ser reproduzível e testável:
o modelo recebe a classificação pronta e só explica e recomenda.
"""
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum

LIMITE_ATENCAO = Decimal("5")  # variação acima de 5% pede atenção
LIMITE_ALERTA = Decimal("10")  # variação acima de 10% é alerta
LEITURAS_DE_REFERENCIA = 5  # a referência é a média das últimas 5 leituras


class Nivel(IntEnum):
    # IntEnum permite comparar a gravidade: max() devolve o nível mais grave
    NORMAL = 0
    ATENCAO = 1
    ALERTA = 2


class LeituraInvalidaError(ValueError):
    """Peso zero ou negativo: balança vazia ou erro do sensor."""


@dataclass(frozen=True)
class FaixaPeso:
    minimo: Decimal
    maximo: Decimal


@dataclass(frozen=True)
class Problema:
    codigo: str
    descricao: str
    nivel: Nivel


@dataclass(frozen=True)
class ResultadoPeso:
    peso: Decimal
    nivel: Nivel
    problemas: tuple[Problema, ...]
    variacao_percentual: Decimal | None
    observacoes: tuple[str, ...]


def avaliar_peso(
    peso: Decimal,
    faixa: FaixaPeso | None,
    historico: list[Decimal],
) -> ResultadoPeso:
    """Classifica uma leitura de peso.

    `historico` traz as leituras anteriores do animal, da mais antiga para a mais recente.
    `faixa` é None quando a raça não está na base de cuidados.
    """
    if peso <= 0:
        raise LeituraInvalidaError(f"Peso inválido: {peso} kg.")

    problemas: list[Problema] = []
    observacoes: list[str] = []

    if faixa is None:
        observacoes.append("Raça sem faixa de peso cadastrada: avaliada só a variação.")
    else:
        problemas.extend(_checar_faixa(peso, faixa))

    variacao = _variacao_percentual(peso, historico)
    if variacao is None:
        observacoes.append("Primeira leitura: sem histórico para comparar.")
    else:
        problemas.extend(_checar_variacao(variacao))

    nivel = max((p.nivel for p in problemas), default=Nivel.NORMAL)
    return ResultadoPeso(peso, nivel, tuple(problemas), variacao, tuple(observacoes))


def _checar_faixa(peso: Decimal, faixa: FaixaPeso) -> list[Problema]:
    faixa_texto = f"{_kg(faixa.minimo)} a {_kg(faixa.maximo)} kg"
    if peso < faixa.minimo:
        return [Problema(
            "ABAIXO_DA_FAIXA",
            f"Peso de {_kg(peso)} kg abaixo da faixa da raça ({faixa_texto}).",
            Nivel.ATENCAO,
        )]
    if peso > faixa.maximo:
        return [Problema(
            "ACIMA_DA_FAIXA",
            f"Peso de {_kg(peso)} kg acima da faixa da raça ({faixa_texto}).",
            Nivel.ATENCAO,
        )]
    return []


def _variacao_percentual(peso: Decimal, historico: list[Decimal]) -> Decimal | None:
    recentes = historico[-LEITURAS_DE_REFERENCIA:]
    if not recentes:
        return None
    referencia = sum(recentes) / len(recentes)
    # sem arredondar: 5,05% arredondado para 5% passaria como normal
    return (peso - referencia) / referencia * 100


def _checar_variacao(variacao: Decimal) -> list[Problema]:
    intensidade = abs(variacao)
    if intensidade <= LIMITE_ATENCAO:
        return []

    nivel = Nivel.ALERTA if intensidade > LIMITE_ALERTA else Nivel.ATENCAO
    if variacao < 0:
        codigo, verbo = "PERDA_DE_PESO", "Perda"
    else:
        codigo, verbo = "GANHO_DE_PESO", "Ganho"
    descricao = (
        f"{verbo} de {_percentual(intensidade)} em relação à média "
        f"das últimas {LEITURAS_DE_REFERENCIA} leituras."
    )
    return [Problema(codigo, descricao, nivel)]


def _kg(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")


def _percentual(valor: Decimal) -> str:
    # o arredondamento acontece só aqui, na hora de mostrar
    return f"{valor:.1f}%".replace(".", ",")
