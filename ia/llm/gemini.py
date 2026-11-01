"""Implementação do ClienteLLM com o Gemini (Google AI Studio), multimodal."""
import httpx
from google import genai
from google.genai import errors, types

from llm.cliente import Imagem, LLMIndisponivelError

# 2.5 foi descontinuado para chaves novas (404); o 3.8 respondeu em mais de 60 s e o 3.5 em ~1,5 s
MODELO_PADRAO = "gemini-3.5-flash"
# a balança não pode ficar presa esperando: passou disso, entra o plano B
TEMPO_LIMITE_MS = 30_000


class ClienteGemini:
    def __init__(self, chave_api: str, modelo: str = MODELO_PADRAO):
        self._cliente = genai.Client(
            api_key=chave_api, http_options=types.HttpOptions(timeout=TEMPO_LIMITE_MS)
        )
        self._modelo = modelo

    def gerar(self, instrucoes: str, prompt: str, imagem: Imagem | None = None) -> str:
        conteudo: list = [prompt]
        if imagem is not None:
            # a foto vai na mesma chamada: o modelo lê texto e imagem juntos
            conteudo.append(types.Part.from_bytes(data=imagem.dados, mime_type=imagem.mime_type))

        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=conteudo,
                config=types.GenerateContentConfig(
                    system_instruction=instrucoes,
                    # baixa: queremos orientação consistente, não criatividade
                    temperature=0.2,
                ),
            )
        except errors.APIError as erro:
            # a mensagem do Google diz o motivo (chave inválida, cota, modelo inexistente)
            raise LLMIndisponivelError(f"Gemini respondeu com erro {erro.code}: {erro.message}") from erro
        except httpx.HTTPError as erro:  # sem rede, timeout
            raise LLMIndisponivelError("Sem conexão com o Gemini.") from erro

        texto = (resposta.text or "").strip()
        if not texto:
            raise LLMIndisponivelError("Gemini devolveu uma resposta vazia.")
        return texto
