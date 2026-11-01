"""Ficha de cuidados por raça: o trecho da base de conhecimento que vai para o LLM (RAG).

A escolha da ficha é feita aqui, em código, e não pelo modelo: o LLM recebe
só a ficha certa, e não a base inteira, para não misturar raças nem inventar.
"""
import unicodedata
from dataclasses import dataclass

from dominio.peso import FaixaPeso

RACA_GENERICA = "SRD"
# nomes que o tutor costuma digitar para "sem raça definida"
SINONIMOS_SRD = {"SRD", "SEM RACA DEFINIDA", "SEM RACA", "VIRA-LATA", "VIRA LATA", "MESTICO"}


@dataclass(frozen=True)
class FichaCuidado:
    especie: str
    raca: str
    faixa: FaixaPeso | None
    vacinas: str
    cuidados: str


def normalizar(texto: str) -> str:
    """'  shih  tzú ' -> 'SHIH TZU': sem acento, maiúsculo e com espaços simples."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().split())


def encontrar_ficha(raca: str, fichas: list[FichaCuidado]) -> FichaCuidado | None:
    """Escolhe a ficha da raça entre as fichas da espécie do animal.

    Ordem: nome igual; nome contido no outro ("Labrador" acha "Labrador Retriever");
    por último, a ficha genérica (SRD) da espécie.
    """
    procurada = normalizar(raca)
    por_nome = {normalizar(f.raca): f for f in fichas}

    if procurada in SINONIMOS_SRD:
        return por_nome.get(RACA_GENERICA)
    if procurada in por_nome:
        return por_nome[procurada]

    parecidas = [
        f for nome, f in por_nome.items()
        if nome != RACA_GENERICA and (procurada in nome or nome in procurada)
    ]
    if len(parecidas) == 1:
        return parecidas[0]

    # nenhuma ou mais de uma parecida: não dá para escolher com segurança
    return por_nome.get(RACA_GENERICA)
