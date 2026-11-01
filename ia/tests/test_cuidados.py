"""Gabarito da escolha da ficha de cuidados (o "retrieval" do RAG)."""
from decimal import Decimal

import pytest

from dominio.cuidados import FichaCuidado, encontrar_ficha, normalizar
from dominio.peso import FaixaPeso
from repositorios.oracle import _animal_da_linha, _ficha_da_linha


def ficha(raca: str) -> FichaCuidado:
    return FichaCuidado("DOG", raca, None, "vacinas", "cuidados")


FICHAS_CAES = [
    ficha("SRD"),
    ficha("Labrador Retriever"),
    ficha("Golden Retriever"),
    ficha("Shih Tzu"),
    ficha("Bulldog Francês"),
]


@pytest.mark.parametrize(
    "digitado, esperada",
    [
        ("Shih Tzu", "Shih Tzu"),
        ("  shih   tzu ", "Shih Tzu"),
        ("bulldog frances", "Bulldog Francês"),
        ("Labrador", "Labrador Retriever"),
        ("vira-lata", "SRD"),
        ("Sem raça definida", "SRD"),
        ("Dálmata", "SRD"),
        # "Retriever" serve para duas fichas: na dúvida, a ficha genérica
        ("Retriever", "SRD"),
    ],
)
def test_escolhe_a_ficha_certa(digitado, esperada):
    assert encontrar_ficha(digitado, FICHAS_CAES).raca == esperada


def test_sem_ficha_generica_e_sem_raca_devolve_none():
    assert encontrar_ficha("Dálmata", [ficha("Shih Tzu")]) is None


def test_normalizar_tira_acento_e_espacos():
    assert normalizar("  Siamês  ") == "SIAMES"


def test_linha_com_limites_vira_faixa():
    linha = ("CAT", "SRD", Decimal("3.50"), Decimal("5.50"), "V4", "água")

    resultado = _ficha_da_linha(linha)

    assert resultado.faixa == FaixaPeso(Decimal("3.50"), Decimal("5.50"))


def test_linha_sem_limites_fica_sem_faixa_e_clob_nulo_vira_texto_vazio():
    linha = ("DOG", "SRD", None, None, None, None)

    resultado = _ficha_da_linha(linha)

    assert resultado.faixa is None
    assert resultado.vacinas == ""


def test_linha_do_animal():
    animal = _animal_da_linha((Decimal("7"), "Thor", "DOG", "Labrador", Decimal("30.5")))

    assert animal.id == 7
    assert animal.especie == "DOG"
