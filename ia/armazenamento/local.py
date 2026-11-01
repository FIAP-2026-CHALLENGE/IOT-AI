"""Storage das fotos do relato: a imagem fica fora do Oracle, que guarda só a URL (Sprint 3).

Na demo, uma pasta local servida pela API em /uploads. Em produção, a mesma
interface seria um bucket (S3, Azure Blob), sem o serviço mudar.
"""
import uuid
from pathlib import Path

from llm.cliente import Imagem

EXTENSOES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class ArmazenamentoLocal:
    def __init__(self, pasta: Path, url_base: str):
        self._pasta = pasta
        self._url_base = url_base.rstrip("/")

    def salvar(self, imagem: Imagem) -> str:
        self._pasta.mkdir(parents=True, exist_ok=True)
        # nome aleatório: o tutor não escolhe o nome do arquivo no servidor
        nome = f"{uuid.uuid4().hex}{EXTENSOES[imagem.mime_type]}"
        (self._pasta / nome).write_bytes(imagem.dados)
        return f"{self._url_base}/{nome}"
