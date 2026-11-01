"""Gabarito do serviço de triagem de peso (regra + ficha da raça + LLM + registro)."""
from decimal import Decimal

import pytest

from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.peso import FaixaPeso, LeituraInvalidaError, Nivel
from dominio.recomendacao import Origem
from servicos.triagem_peso import AnimalNaoEncontradoError, TriagemPesoServico
from tests.dubles import AnimaisFalsos, CuidadosFalsos, LeiturasFalsas, LLMFalso, RecomendacoesFalsas

D = Decimal
LUNA = Animal(id=1, nome="Luna", especie="CAT", raca="Siamês", peso_cadastro=D("4.00"))
THOR = Animal(id=2, nome="Thor", especie="DOG", raca="Dálmata", peso_cadastro=D("25.00"))
FICHA_SIAMES = FichaCuidado(
    "CAT", "Siamês", FaixaPeso(D("3.00"), D("5.00")),
    "Polivalente felina anual.", "Predisposição a problemas dentários.",
)
FICHA_CAO_SRD = FichaCuidado("DOG", "SRD", None, "Polivalente anual.", "Acompanhe pelo escore corporal.")


def montar(historico, llm=None):
    recomendacoes = RecomendacoesFalsas()
    leituras = LeiturasFalsas(historico)
    llm = llm or LLMFalso()
    servico = TriagemPesoServico(
        animais=AnimaisFalsos(LUNA, THOR),
        leituras=leituras,
        cuidados=CuidadosFalsos(FICHA_SIAMES, FICHA_CAO_SRD),
        recomendacoes=recomendacoes,
        llm=llm,
    )
    return servico, recomendacoes, leituras, llm


def test_alerta_pede_recomendacao_ao_llm_com_regra_e_ficha_no_prompt():
    servico, recomendacoes, _, llm = montar([D("4.00")] * 5)

    resultado = servico.avaliar(animal_id=1, peso=D("2.90"))

    assert resultado.nivel == Nivel.ALERTA
    assert resultado.usou_llm is True
    prompt = llm.pedidos[0]["prompt"]
    assert "Luna" in prompt and "Siamês" in prompt
    assert "ALERTA" in prompt
    assert "abaixo da faixa da raça (3,00 a 5,00 kg)" in prompt
    assert "Perda de 27,5%" in prompt
    assert "Predisposição a problemas dentários." in prompt  # a ficha da raça (RAG)
    assert recomendacoes.salvas[0].origem == Origem.PESO
    assert recomendacoes.salvas[0].nivel == Nivel.ALERTA
    assert recomendacoes.salvas[0].texto == "Recomendação do LLM falso."
    assert resultado.recomendacao_id == 1


def test_normal_nao_gasta_llm_mas_registra_a_recomendacao():
    servico, recomendacoes, _, llm = montar([D("4.00")] * 5)

    resultado = servico.avaliar(animal_id=1, peso=D("4.05"))

    assert resultado.nivel == Nivel.NORMAL
    assert llm.pedidos == []
    assert resultado.usou_llm is False
    assert "dentro do esperado" in recomendacoes.salvas[0].texto


def test_llm_fora_do_ar_usa_texto_da_regra_e_registra_mesmo_assim():
    servico, recomendacoes, _, _ = montar([D("4.00")] * 5, llm=LLMFalso(falhar=True))

    resultado = servico.avaliar(animal_id=1, peso=D("2.90"))

    assert resultado.nivel == Nivel.ALERTA
    assert resultado.usou_llm is False
    assert "fora do ar" in resultado.motivo_sem_llm  # o motivo não some no plano B
    texto = recomendacoes.salvas[0].texto
    assert "abaixo da faixa da raça" in texto
    assert "veterinário" in texto


def test_raca_fora_da_base_usa_a_ficha_generica_da_especie():
    servico, _, _, llm = montar([D("25.00")])

    resultado = servico.avaliar(animal_id=2, peso=D("20.00"))

    assert resultado.ficha_usada == "SRD"
    assert "Acompanhe pelo escore corporal." in llm.pedidos[0]["prompt"]


def test_leitura_avaliada_fica_fora_da_propria_media():
    servico, _, leituras, _ = montar([D("4.00")])

    servico.avaliar(animal_id=1, peso=D("4.00"), leitura_id=99)

    assert leituras.chamadas[0]["antes_do_id"] == 99


def test_animal_inexistente_nao_registra_nada():
    servico, recomendacoes, _, llm = montar([])

    with pytest.raises(AnimalNaoEncontradoError):
        servico.avaliar(animal_id=404, peso=D("4.00"))

    assert recomendacoes.salvas == [] and llm.pedidos == []


def test_balanca_vazia_nao_registra_nada():
    servico, recomendacoes, _, _ = montar([D("4.00")])

    with pytest.raises(LeituraInvalidaError):
        servico.avaliar(animal_id=1, peso=D("0"))

    assert recomendacoes.salvas == []


def test_instrucoes_proibem_diagnostico_e_mudar_o_nivel():
    servico, _, _, llm = montar([D("4.00")] * 5)

    servico.avaliar(animal_id=1, peso=D("2.90"))

    instrucoes = llm.pedidos[0]["instrucoes"]
    assert "não faça diagnóstico" in instrucoes
    assert "não altere o nível" in instrucoes
    assert "atendimento imediato" in instrucoes  # sinal de emergência não vira "agende consulta"
    assert "relação com o problema" in instrucoes


def test_primeira_pesagem_compara_com_o_cadastro_e_chama_o_llm():
    # Thor tem 25 kg no cadastro e nenhuma leitura ainda; 18 kg é perda de 28%
    servico, recomendacoes, _, llm = montar([])

    resultado = servico.avaliar(animal_id=2, peso=D("18"))

    assert resultado.nivel == Nivel.ALERTA
    assert resultado.usou_llm is True
    assert "peso do cadastro" in llm.pedidos[0]["prompt"]
