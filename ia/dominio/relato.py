"""Regras objetivas do relato do tutor (texto livre e/ou foto do sintoma).

O LLM interpreta o relato e sugere o nível, mas o código:
- valida o que entra (texto ou foto, tamanho e tipo da imagem);
- detecta sinais de emergência por palavra-chave e, se houver, garante ALERTA,
  mesmo que o modelo tenha subestimado (o código só pode subir o nível, nunca baixar);
- lê o nível da resposta do modelo, em vez de confiar no texto livre.
"""
import re

from dominio.cuidados import normalizar
from dominio.peso import Nivel

TAMANHO_MAXIMO_TEXTO = 2000  # VARCHAR2(2000) de T_TUTOR_REPORT.REPORT_TEXT
TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB
TIPOS_DE_FOTO = {"image/jpeg", "image/png", "image/webp"}

# (trecho procurado no texto normalizado, como aparece para o tutor)
SINAIS_DE_EMERGENCIA = [
    ("CONVULS", "convulsão"),
    ("NAO CONSEGUE RESPIRAR", "dificuldade para respirar"),
    ("DIFICULDADE PARA RESPIRAR", "dificuldade para respirar"),
    ("FALTA DE AR", "dificuldade para respirar"),
    ("GENGIVA ROXA", "gengiva arroxeada"),
    ("GENGIVA ARROXEADA", "gengiva arroxeada"),
    ("DESMAI", "desmaio"),
    ("SANGRA", "sangramento"),
    ("SANGUE", "sangramento"),
    ("ENVENEN", "suspeita de envenenamento"),
    ("VENENO", "suspeita de envenenamento"),
    ("ATROPEL", "atropelamento"),
    ("NAO CONSEGUE FAZER XIXI", "não consegue urinar"),
    ("NAO CONSEGUE URINAR", "não consegue urinar"),
    ("BARRIGA INCHADA", "barriga inchada"),
]

_LINHA_DO_NIVEL = re.compile(r"^\s*n[ií]vel\s*:\s*(normal|aten[cç][aã]o|alerta)\b", re.IGNORECASE)


class RelatoInvalidoError(ValueError):
    pass


def validar_relato(texto: str | None, tipo_foto: str | None, tamanho_foto: int | None) -> str | None:
    """Confere o relato e devolve o texto limpo (ou None, quando o relato é só a foto)."""
    texto = (texto or "").strip() or None
    tem_foto = tipo_foto is not None

    if texto is None and not tem_foto:
        raise RelatoInvalidoError("Envie uma descrição, uma foto ou os dois.")
    if texto is not None and len(texto) > TAMANHO_MAXIMO_TEXTO:
        raise RelatoInvalidoError(f"A descrição passa de {TAMANHO_MAXIMO_TEXTO} caracteres.")
    if tem_foto:
        if tipo_foto not in TIPOS_DE_FOTO:
            raise RelatoInvalidoError("A foto precisa ser JPG, PNG ou WEBP.")
        if not tamanho_foto:
            raise RelatoInvalidoError("A foto está vazia.")
        if tamanho_foto > TAMANHO_MAXIMO_FOTO:
            raise RelatoInvalidoError("A foto passa de 5 MB.")
    return texto


def sinais_de_emergencia(texto: str | None) -> list[str]:
    """Sinais de emergência citados no relato, sem repetição, na ordem da lista."""
    if not texto:
        return []
    procurado = normalizar(texto)
    encontrados: list[str] = []
    for trecho, descricao in SINAIS_DE_EMERGENCIA:
        if trecho in procurado and descricao not in encontrados:
            encontrados.append(descricao)
    return encontrados


def separar_nivel(resposta: str) -> tuple[Nivel | None, str]:
    """Lê a primeira linha 'Nível: X' da resposta do LLM e devolve (nível, resto do texto).

    Se o modelo não seguir o formato, o nível vem None e o serviço decide.
    """
    primeira, _, resto = resposta.strip().partition("\n")
    encontrado = _LINHA_DO_NIVEL.match(primeira)
    if not encontrado:
        return None, resposta.strip()
    nome = normalizar(encontrado.group(1))  # "ATENÇÃO" -> "ATENCAO"
    return Nivel[nome], resto.strip()
