"""Gabarito da API: rotas, códigos HTTP e formato do JSON, com os serviços montados sobre dublês."""
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import Servicos, criar_app
from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.peso import FaixaPeso
from servicos.plano_cuidados import PlanoCuidadosServico
from servicos.triagem_peso import TriagemPesoServico
from servicos.triagem_relato import TriagemRelatoServico
from tests.dubles import (
    AnimaisFalsos,
    CuidadosFalsos,
    FotosFalsas,
    LeiturasFalsas,
    LLMFalso,
    RecomendacoesFalsas,
    RelatosFalsos,
)

THOR = Animal(1, "Thor", "DOG", "Pug", Decimal("8.50"), nascimento=date(2023, 3, 1))
FICHA_PUG = FichaCuidado("DOG", "Pug", FaixaPeso(Decimal("6"), Decimal("9")), "V10 anual.", "Braquicefálico.")


@pytest.fixture
def cliente(tmp_path):
    animais, leituras = AnimaisFalsos(THOR), LeiturasFalsas([])
    cuidados, recomendacoes = CuidadosFalsos(FICHA_PUG), RecomendacoesFalsas()
    llm = LLMFalso("Nível: ATENCAO\nResumo: texto do LLM falso.")

    def montar():
        return Servicos(
            animais=animais,
            leituras=leituras,
            recomendacoes=recomendacoes,
            triagem_peso=TriagemPesoServico(animais, leituras, cuidados, recomendacoes, llm),
            triagem_relato=TriagemRelatoServico(animais, cuidados, RelatosFalsos(), recomendacoes, FotosFalsas(), llm),
            plano_cuidados=PlanoCuidadosServico(animais, cuidados, recomendacoes, llm),
        )

    with TestClient(criar_app(montar, pasta_uploads=tmp_path)) as c:
        yield c


def test_health(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}


def test_lista_animais(cliente):
    corpo = cliente.get("/animais").json()

    assert corpo[0]["nome"] == "Thor" and corpo[0]["raca"] == "Pug"


def test_leitura_da_balanca_devolve_a_triagem(cliente):
    resposta = cliente.post("/leituras", json={"animal_id": 1, "peso": 18})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nivel"] == "ALERTA"
    assert [p["codigo"] for p in corpo["problemas"]] == ["ACIMA_DA_FAIXA", "GANHO_DE_PESO"]
    assert corpo["ficha_usada"] == "Pug"
    assert corpo["leitura_id"] > 0


@pytest.mark.parametrize(
    "corpo, codigo",
    [
        ({"animal_id": 404, "peso": 8}, 404),
        ({"animal_id": 1, "peso": 0}, 422),
        ({"animal_id": 1}, 422),
    ],
)
def test_leitura_invalida(cliente, corpo, codigo):
    assert cliente.post("/leituras", json=corpo).status_code == codigo


def test_relato_com_texto_e_foto(cliente):
    resposta = cliente.post(
        "/animais/1/relatos",
        data={"texto": "Apareceu uma mancha na barriga"},
        files={"foto": ("mancha.jpg", b"\xff\xd8bytes", "image/jpeg")},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nivel"] == "ATENCAO"
    assert corpo["imagem_url"].startswith("http://localhost:8000/uploads/")
    assert corpo["texto"].startswith("Resumo")


def test_relato_vazio_e_recusado(cliente):
    resposta = cliente.post("/animais/1/relatos", data={"texto": "  "})

    assert resposta.status_code == 422
    assert "descrição, uma foto" in resposta.json()["detail"]


def test_relato_com_arquivo_que_nao_e_imagem(cliente):
    resposta = cliente.post("/animais/1/relatos", files={"foto": ("exame.pdf", b"%PDF", "application/pdf")})

    assert resposta.status_code == 422


def test_plano_de_cuidados_e_historico(cliente):
    assert cliente.post("/animais/1/plano-cuidados").status_code == 201

    historico = cliente.get("/animais/1/recomendacoes").json()

    assert historico[0]["origem"] == "CUIDADO_RACA"


def test_rotas_do_animal_inexistente(cliente):
    assert cliente.get("/animais/404/leituras").status_code == 404
    assert cliente.post("/animais/404/plano-cuidados").status_code == 404
