"""Gabarito do plano de cuidados por raça e da idade."""
from datetime import date
from decimal import Decimal

import pytest

from dominio.animal import Animal, idade_em_texto
from dominio.cuidados import FichaCuidado
from dominio.peso import Nivel
from dominio.recomendacao import Origem
from servicos.plano_cuidados import FichaNaoEncontradaError, PlanoCuidadosServico
from tests.dubles import AnimaisFalsos, CuidadosFalsos, LLMFalso, RecomendacoesFalsas

HOJE = date(2026, 11, 1)
MEL = Animal(3, "Mel", "DOG", "Shih Tzu", Decimal("5.20"), nascimento=date(2026, 6, 15))
FICHA = FichaCuidado("DOG", "Shih Tzu", None, "Polivalente: 3 doses de filhote.", "Olhos proeminentes.")


@pytest.mark.parametrize(
    "nascimento, esperado",
    [
        (date(2024, 8, 1), "2 anos e 3 meses"),
        (date(2025, 11, 1), "1 ano"),
        (date(2026, 6, 15), "4 meses"),
        (date(2026, 10, 2), "0 meses"),
        (None, "idade não informada"),
        (date(2027, 1, 1), "idade não informada"),
    ],
)
def test_idade_em_texto(nascimento, esperado):
    assert idade_em_texto(nascimento, HOJE) == esperado


def test_plano_usa_ficha_e_idade_e_registra_como_cuidado_raca():
    recomendacoes, llm = RecomendacoesFalsas(), LLMFalso("Vacinas:\n- dose 3")
    servico = PlanoCuidadosServico(AnimaisFalsos(MEL), CuidadosFalsos(FICHA), recomendacoes, llm)

    resultado = servico.gerar(3, hoje=HOJE)

    prompt = llm.pedidos[0]["prompt"]
    assert "Idade: 4 meses" in prompt
    assert "Polivalente: 3 doses de filhote." in prompt
    assert resultado.ficha_usada == "Shih Tzu"
    assert recomendacoes.salvas[0].origem == Origem.CUIDADO_RACA
    assert recomendacoes.salvas[0].nivel == Nivel.NORMAL


def test_plano_sem_llm_devolve_a_propria_ficha():
    servico = PlanoCuidadosServico(
        AnimaisFalsos(MEL), CuidadosFalsos(FICHA), RecomendacoesFalsas(), LLMFalso(falhar=True)
    )

    resultado = servico.gerar(3, hoje=HOJE)

    assert resultado.usou_llm is False
    assert "Polivalente: 3 doses de filhote." in resultado.texto


def test_sem_ficha_da_especie():
    servico = PlanoCuidadosServico(AnimaisFalsos(MEL), CuidadosFalsos(), RecomendacoesFalsas(), LLMFalso())

    with pytest.raises(FichaNaoEncontradaError):
        servico.gerar(3, hoje=HOJE)
