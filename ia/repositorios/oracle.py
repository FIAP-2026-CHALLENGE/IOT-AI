"""Acesso ao Oracle da FIAP: só leitura e gravação, sem regra de negócio.

Cada repositório recebe o pool de conexões e pega uma conexão por operação.
As funções `_..._da_linha` convertem a linha do banco no objeto do domínio
e são testadas sem banco.
"""
from datetime import datetime
from decimal import Decimal

import oracledb

from config import ConfigOracle
from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.peso import FaixaPeso
from dominio.recomendacao import NovaRecomendacao
from dominio.registros import Leitura, RecomendacaoRegistrada

# NUMBER vira Decimal (e não float) e CLOB vira str
oracledb.defaults.fetch_decimals = True
oracledb.defaults.fetch_lobs = False


def criar_pool(config: ConfigOracle) -> oracledb.ConnectionPool:
    # modo thin: não precisa instalar o Oracle Client
    return oracledb.create_pool(
        user=config.usuario, password=config.senha, dsn=config.dsn, min=1, max=4
    )


class AnimalRepositorio:
    def __init__(self, pool: oracledb.ConnectionPool):
        self._pool = pool

    _COLUNAS = "ID, NAME, SPECIES, BREED, WEIGHT, BIRTH_DATE"

    def buscar_por_id(self, animal_id: int) -> Animal | None:
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(f"SELECT {self._COLUNAS} FROM T_CP_ANIMAIS WHERE ID = :id", id=animal_id)
            linha = cursor.fetchone()
        return _animal_da_linha(linha) if linha else None

    def listar(self) -> list[Animal]:
        """Animais ativos no cadastro da API .NET, para a interface do tutor."""
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(f"SELECT {self._COLUNAS} FROM T_CP_ANIMAIS WHERE IS_ACTIVE = 1 ORDER BY NAME, ID")
            return [_animal_da_linha(linha) for linha in cursor.fetchall()]


class LeituraRepositorio:
    def __init__(self, pool: oracledb.ConnectionPool):
        self._pool = pool

    def registrar(self, animal_id: int, peso: Decimal) -> int:
        """Grava uma leitura da balança, como o Node-RED faz, e devolve o ID."""
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            novo_id = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO T_EXAM_READING (ANIMAL_ID, READING)
                VALUES (:animal_id, :peso)
                RETURNING ID INTO :novo_id
                """,
                animal_id=animal_id, peso=peso, novo_id=novo_id,
            )
            conexao.commit()
        return novo_id.getvalue()[0]

    def listar(self, animal_id: int, limite: int = 30) -> list[Leitura]:
        """Últimas leituras com data, da mais antiga para a mais recente (gráfico da interface)."""
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT ID, READING, DATETIME FROM T_EXAM_READING
                 WHERE ANIMAL_ID = :animal_id
                 ORDER BY DATETIME DESC, ID DESC
                 FETCH FIRST :limite ROWS ONLY
                """,
                animal_id=animal_id, limite=limite,
            )
            linhas = cursor.fetchall()
        return [Leitura(int(i), peso, data) for i, peso, data in reversed(linhas)]

    def historico(self, animal_id: int, limite: int, antes_do_id: int | None = None) -> list[Decimal]:
        """Últimas leituras do animal, da mais antiga para a mais recente.

        `antes_do_id` exclui a leitura que está sendo avaliada (e as posteriores),
        para ela não entrar na própria média de referência.
        """
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT READING FROM T_EXAM_READING
                 WHERE ANIMAL_ID = :animal_id
                   AND READING > 0
                   AND (:antes_do_id IS NULL OR ID < :antes_do_id)
                 ORDER BY DATETIME DESC, ID DESC
                 FETCH FIRST :limite ROWS ONLY
                """,
                animal_id=animal_id, antes_do_id=antes_do_id, limite=limite,
            )
            mais_recentes_primeiro = [linha[0] for linha in cursor.fetchall()]
        return list(reversed(mais_recentes_primeiro))


class CuidadoRacaRepositorio:
    def __init__(self, pool: oracledb.ConnectionPool):
        self._pool = pool

    def listar_por_especie(self, especie: str) -> list[FichaCuidado]:
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT SPECIES, BREED, MIN_WEIGHT, MAX_WEIGHT, VACCINE_SCHEDULE, CARE_NOTES
                  FROM T_BREED_CARE
                 WHERE SPECIES = :especie
                """,
                especie=especie.strip().upper(),
            )
            return [_ficha_da_linha(linha) for linha in cursor.fetchall()]


class RecomendacaoRepositorio:
    def __init__(self, pool: oracledb.ConnectionPool):
        self._pool = pool

    def salvar(self, recomendacao: NovaRecomendacao) -> int:
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            novo_id = cursor.var(int)
            cursor.setinputsizes(texto=oracledb.DB_TYPE_CLOB)
            cursor.execute(
                """
                INSERT INTO T_AI_RECOMMENDATION (ANIMAL_ID, SOURCE, ALERT_LEVEL, RECOMMENDATION_TEXT)
                VALUES (:animal_id, :origem, :nivel, :texto)
                RETURNING ID INTO :novo_id
                """,
                animal_id=recomendacao.animal_id,
                origem=recomendacao.origem.value,
                nivel=recomendacao.nivel.name,
                texto=recomendacao.texto,
                novo_id=novo_id,
            )
            conexao.commit()
        return novo_id.getvalue()[0]

    def listar_por_animal(self, animal_id: int, limite: int = 20) -> list[RecomendacaoRegistrada]:
        """Histórico da IA para o animal, da mais recente para a mais antiga."""
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT ID, SOURCE, ALERT_LEVEL, RECOMMENDATION_TEXT, CREATED_AT
                  FROM T_AI_RECOMMENDATION
                 WHERE ANIMAL_ID = :animal_id
                 ORDER BY CREATED_AT DESC, ID DESC
                 FETCH FIRST :limite ROWS ONLY
                """,
                animal_id=animal_id, limite=limite,
            )
            return [RecomendacaoRegistrada(int(i), o, n, t, d) for i, o, n, t, d in cursor.fetchall()]


class RelatoRepositorio:
    def __init__(self, pool: oracledb.ConnectionPool):
        self._pool = pool

    def salvar(self, animal_id: int, texto: str | None, imagem_url: str | None) -> int:
        with self._pool.acquire() as conexao, conexao.cursor() as cursor:
            novo_id = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO T_TUTOR_REPORT (ANIMAL_ID, REPORT_TEXT, IMAGE_URL)
                VALUES (:animal_id, :texto, :imagem_url)
                RETURNING ID INTO :novo_id
                """,
                animal_id=animal_id, texto=texto, imagem_url=imagem_url, novo_id=novo_id,
            )
            conexao.commit()
        return novo_id.getvalue()[0]


def _animal_da_linha(linha: tuple) -> Animal:
    animal_id, nome, especie, raca, peso, nascimento = linha
    return Animal(
        id=int(animal_id), nome=nome, especie=especie, raca=raca, peso_cadastro=peso,
        nascimento=nascimento.date() if isinstance(nascimento, datetime) else nascimento,
    )


def _ficha_da_linha(linha: tuple) -> FichaCuidado:
    especie, raca, minimo, maximo, vacinas, cuidados = linha
    # ficha sem os dois limites (ex.: cão SRD) não tem faixa de peso
    faixa = FaixaPeso(minimo, maximo) if minimo is not None and maximo is not None else None
    return FichaCuidado(
        especie=especie, raca=raca, faixa=faixa, vacinas=vacinas or "", cuidados=cuidados or ""
    )
