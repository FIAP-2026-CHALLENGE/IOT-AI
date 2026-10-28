"""Gabarito das regras de peso, escrito antes da implementação.

Regras (decididas em código, nunca pelo LLM):
- Faixa da raça: peso dentro de [mínimo, máximo] é normal; os limites contam como dentro.
  Fora da faixa -> ATENCAO.
- Variação: comparada com a média das últimas 5 leituras anteriores.
  Até 5% (inclusive) -> normal; acima de 5% até 10% (inclusive) -> ATENCAO; acima de 10% -> ALERTA.
- O nível final é o mais grave entre os problemas encontrados.
- Peso zero ou negativo (balança vazia) não é avaliado.
"""
from decimal import Decimal

import pytest

from dominio.peso import FaixaPeso, LeituraInvalidaError, Nivel, avaliar_peso

D = Decimal
FAIXA_GATO = FaixaPeso(minimo=D("3.50"), maximo=D("5.50"))
FAIXA_LABRADOR = FaixaPeso(minimo=D("25.00"), maximo=D("36.00"))


# (cenário, peso, faixa, histórico, nível esperado, códigos esperados)
GABARITO = [
    ("normal, dentro da faixa e estável", "4.50", FAIXA_GATO, ["4.50", "4.48"], Nivel.NORMAL, []),
    ("exatamente no mínimo da faixa", "3.50", FAIXA_GATO, ["3.50"], Nivel.NORMAL, []),
    ("exatamente no máximo da faixa", "5.50", FAIXA_GATO, ["5.50"], Nivel.NORMAL, []),
    ("um centésimo abaixo da faixa", "3.49", FAIXA_GATO, ["3.49"], Nivel.ATENCAO, ["ABAIXO_DA_FAIXA"]),
    ("um centésimo acima da faixa", "5.51", FAIXA_GATO, ["5.51"], Nivel.ATENCAO, ["ACIMA_DA_FAIXA"]),
    ("perda de exatamente 5%", "28.50", FAIXA_LABRADOR, ["30.00"], Nivel.NORMAL, []),
    ("ganho logo acima de 5%", "31.51", FAIXA_LABRADOR, ["30.00"], Nivel.ATENCAO, ["GANHO_DE_PESO"]),
    ("perda de exatamente 10%", "27.00", FAIXA_LABRADOR, ["30.00"], Nivel.ATENCAO, ["PERDA_DE_PESO"]),
    ("perda acima de 10%", "26.99", FAIXA_LABRADOR, ["30.00"], Nivel.ALERTA, ["PERDA_DE_PESO"]),
    ("ganho acima de 10%", "33.01", FAIXA_LABRADOR, ["30.00"], Nivel.ALERTA, ["GANHO_DE_PESO"]),
    (
        "fora da faixa e perda acima de 10%",
        "3.00", FAIXA_GATO, ["4.00", "4.00"],
        Nivel.ALERTA, ["ABAIXO_DA_FAIXA", "PERDA_DE_PESO"],
    ),
    (
        "referência é a média das 5 últimas, não do histórico todo",
        "30.00", FAIXA_LABRADOR, ["10.00", "10.00", "30.00", "30.00", "30.00", "30.00", "30.00"],
        Nivel.NORMAL, [],
    ),
]


@pytest.mark.parametrize(
    "peso, faixa, historico, nivel, codigos",
    [caso[1:] for caso in GABARITO],
    ids=[caso[0] for caso in GABARITO],
)
def test_gabarito(peso, faixa, historico, nivel, codigos):
    resultado = avaliar_peso(D(peso), faixa, [D(h) for h in historico])

    assert resultado.nivel == nivel
    assert [p.codigo for p in resultado.problemas] == codigos


def test_primeira_leitura_sem_historico_nao_calcula_variacao():
    resultado = avaliar_peso(D("4.50"), FAIXA_GATO, [])

    assert resultado.nivel == Nivel.NORMAL
    assert resultado.variacao_percentual is None
    assert any("Primeira leitura" in o for o in resultado.observacoes)


def test_raca_sem_faixa_avalia_so_a_variacao():
    resultado = avaliar_peso(D("8.00"), None, [D("10.00")])

    assert resultado.nivel == Nivel.ALERTA
    assert [p.codigo for p in resultado.problemas] == ["PERDA_DE_PESO"]
    assert any("sem faixa" in o for o in resultado.observacoes)


def test_variacao_nao_e_arredondada_antes_de_comparar():
    # 21,01 sobre 20,00 é 5,05%: arredondar para 5% antes da regra esconderia a atenção
    resultado = avaliar_peso(D("21.01"), None, [D("20.00")])

    assert resultado.variacao_percentual == D("5.05")
    assert resultado.nivel == Nivel.ATENCAO


@pytest.mark.parametrize("peso", ["0", "-0.30"])
def test_balanca_vazia_nao_e_avaliada(peso):
    with pytest.raises(LeituraInvalidaError):
        avaliar_peso(D(peso), FAIXA_GATO, [])


def test_descricao_do_problema_traz_os_numeros_para_o_llm():
    resultado = avaliar_peso(D("3.00"), FAIXA_GATO, [D("4.00")])

    descricoes = " | ".join(p.descricao for p in resultado.problemas)
    assert "3,00 kg" in descricoes
    assert "3,50 a 5,50 kg" in descricoes
    assert "25,0%" in descricoes
