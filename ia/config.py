"""Configuração lida do .env (nunca versionado; o modelo é o .env.example)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfiguracaoAusenteError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConfigOracle:
    usuario: str
    senha: str
    dsn: str


def carregar_config_oracle() -> ConfigOracle:
    load_dotenv()
    nomes = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
    faltando = [nome for nome in nomes if not os.getenv(nome)]
    if faltando:
        raise ConfiguracaoAusenteError(
            f"Variáveis ausentes no .env: {', '.join(faltando)} (veja o .env.example)."
        )
    return ConfigOracle(
        usuario=os.environ["ORACLE_USER"],
        senha=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    )


@dataclass(frozen=True)
class ConfigGemini:
    chave_api: str
    modelo: str


def carregar_config_gemini() -> ConfigGemini:
    load_dotenv()
    if os.getenv("GEMINI_API_KEY", "sua_chave") == "sua_chave":
        raise ConfiguracaoAusenteError(
            "GEMINI_API_KEY ausente ou com o valor de exemplo no .env (crie a chave no Google AI Studio)."
        )
    return ConfigGemini(
        chave_api=os.environ["GEMINI_API_KEY"],
        modelo=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    )


@dataclass(frozen=True)
class ConfigApi:
    url_publica: str  # onde a API é acessada; entra na URL das fotos gravada no Oracle


def carregar_config_api() -> ConfigApi:
    load_dotenv()
    return ConfigApi(url_publica=os.getenv("API_URL", "http://localhost:8000").rstrip("/"))
