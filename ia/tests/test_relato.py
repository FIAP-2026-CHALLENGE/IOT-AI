"""Gabarito do relato do tutor: validação, sinais de emergência, leitura do nível e serviço."""
from decimal import Decimal

import pytest

from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.peso import Nivel
from dominio.recomendacao import Origem
from dominio.relato import RelatoInvalidoError, separar_nivel, sinais_de_emergencia, validar_relato
from llm.cliente import Imagem
from servicos.triagem_peso import AnimalNaoEncontradoError
from servicos.triagem_relato import TriagemRelatoServico
from tests.dubles import AnimaisFalsos, CuidadosFalsos, FotosFalsas, LLMFalso, RecomendacoesFalsas, RelatosFalsos

LUNA = Animal(id=1, nome="Luna", especie="CAT", raca="Siamês", peso_cadastro=Decimal("4.00"))
FICHA = FichaCuidado("CAT", "Siamês", None, "V4 anual.", "Predisposição a problemas dentários.")
FOTO = Imagem(b"\xff\xd8bytes-de-um-jpg", "image/jpeg")
RESPOSTA_ATENCAO = "Nível: ATENCAO\nResumo: coceira na orelha.\nO que fazer:\n- Observe.\nQuando procurar o veterinário: se piorar."


def montar(llm=None):
    relatos, recomendacoes, fotos = RelatosFalsos(), RecomendacoesFalsas(), FotosFalsas()
    llm = llm or LLMFalso(RESPOSTA_ATENCAO)
    servico = TriagemRelatoServico(
        AnimaisFalsos(LUNA), CuidadosFalsos(FICHA), relatos, recomendacoes, fotos, llm
    )
    return servico, relatos, recomendacoes, fotos, llm


# ---------- regras do domínio ----------

@pytest.mark.parametrize(
    "texto, tipo, tamanho, mensagem",
    [
        (None, None, None, "descrição, uma foto"),
        ("   ", None, None, "descrição, uma foto"),
        ("x" * 2001, None, None, "2000"),
        (None, "application/pdf", 10, "JPG, PNG ou WEBP"),
        (None, "image/png", 0, "vazia"),
        (None, "image/png", 5 * 1024 * 1024 + 1, "5 MB"),
    ],
)
def test_relato_invalido(texto, tipo, tamanho, mensagem):
    with pytest.raises(RelatoInvalidoError, match=mensagem):
        validar_relato(texto, tipo, tamanho)


def test_relato_so_com_foto_e_valido():
    assert validar_relato(None, "image/jpeg", 1000) is None


@pytest.mark.parametrize(
    "texto, esperados",
    [
        ("Ela teve uma CONVULSÃO hoje cedo", ["convulsão"]),
        ("não consegue respirar direito e a gengiva roxa", ["dificuldade para respirar", "gengiva arroxeada"]),
        ("acho que comeu veneno de rato", ["suspeita de envenenamento"]),
        ("está coçando a orelha", []),
        (None, []),
    ],
)
def test_sinais_de_emergencia(texto, esperados):
    assert sinais_de_emergencia(texto) == esperados


@pytest.mark.parametrize(
    "resposta, nivel, comeco_do_resto",
    [
        ("Nível: ALERTA\nResumo: x", Nivel.ALERTA, "Resumo"),
        ("nivel: atenção\nResumo: x", Nivel.ATENCAO, "Resumo"),
        ("Resumo: o modelo esqueceu a linha do nível", None, "Resumo"),
    ],
)
def test_separar_nivel(resposta, nivel, comeco_do_resto):
    lido, resto = separar_nivel(resposta)
    assert lido == nivel
    assert resto.startswith(comeco_do_resto)


# ---------- serviço ----------

def test_texto_e_foto_vao_juntos_para_o_llm_e_tudo_e_registrado():
    servico, relatos, recomendacoes, fotos, llm = montar()

    resultado = servico.avaliar(1, "Está coçando a orelha", FOTO)

    assert llm.pedidos[0]["imagem"] == FOTO  # multimodal: a foto vai na mesma chamada
    assert "Está coçando a orelha" in llm.pedidos[0]["prompt"]
    assert "Predisposição a problemas dentários." in llm.pedidos[0]["prompt"]  # ficha (RAG)
    assert relatos.salvos[0] == {"animal_id": 1, "texto": "Está coçando a orelha", "imagem_url": resultado.imagem_url}
    assert fotos.salvas == [FOTO]
    assert resultado.nivel == Nivel.ATENCAO
    assert resultado.texto.startswith("Resumo")  # a linha do nível não vai para o tutor
    assert recomendacoes.salvas[0].origem == Origem.RELATO
    assert recomendacoes.salvas[0].nivel == Nivel.ATENCAO


def test_emergencia_no_texto_sobe_para_alerta_mesmo_se_o_llm_disser_normal():
    llm = LLMFalso("Nível: NORMAL\nResumo: tudo bem.")
    servico, _, recomendacoes, _, _ = montar(llm)

    resultado = servico.avaliar(1, "Teve uma convulsão agora", None)

    assert resultado.nivel == Nivel.ALERTA
    assert resultado.sinais_de_emergencia == ("convulsão",)
    assert "convulsão" in llm.pedidos[0]["prompt"]
    assert recomendacoes.salvas[0].nivel == Nivel.ALERTA


def test_llm_fora_do_formato_vira_atencao():
    servico, _, _, _, _ = montar(LLMFalso("Resumo: sem a linha do nível."))

    assert servico.avaliar(1, "Comeu menos hoje", None).nivel == Nivel.ATENCAO


def test_llm_fora_do_ar_registra_com_plano_b():
    servico, relatos, recomendacoes, _, _ = montar(LLMFalso(falhar=True))

    resultado = servico.avaliar(1, "Comeu menos hoje", None)

    assert resultado.usou_llm is False
    assert "fora do ar" in resultado.motivo_sem_llm
    assert resultado.nivel == Nivel.ATENCAO
    assert len(relatos.salvos) == 1 and len(recomendacoes.salvas) == 1


def test_llm_fora_do_ar_com_emergencia_manda_ao_veterinario():
    servico, _, _, _, _ = montar(LLMFalso(falhar=True))

    resultado = servico.avaliar(1, "Está com sangue na urina", None)

    assert resultado.nivel == Nivel.ALERTA
    assert "atendimento veterinário imediato" in resultado.texto


def test_relato_invalido_nao_grava_nada():
    servico, relatos, recomendacoes, fotos, llm = montar()

    with pytest.raises(RelatoInvalidoError):
        servico.avaliar(1, "", Imagem(b"%PDF", "application/pdf"))

    assert relatos.salvos == [] and recomendacoes.salvas == [] and fotos.salvas == [] and llm.pedidos == []


def test_animal_inexistente():
    servico, _, _, _, _ = montar()

    with pytest.raises(AnimalNaoEncontradoError):
        servico.avaliar(404, "texto", None)
