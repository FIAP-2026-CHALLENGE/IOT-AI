"""API da IA de triagem: o ponto de integração entre a balança (Node-RED), a interface do tutor e a IA.

Rodar (dentro de ia/):  .venv/Scripts/python -m uvicorn api.main:app --reload
Documentação interativa: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.esquemas import (
    AnimalSaida,
    LeituraEntrada,
    LeituraSaida,
    PlanoSaida,
    ProblemaSaida,
    RecomendacaoSaida,
    RelatoSaida,
    TriagemPesoSaida,
)
from dominio.peso import LeituraInvalidaError
from dominio.relato import RelatoInvalidoError
from llm.cliente import Imagem
from servicos.plano_cuidados import FichaNaoEncontradaError, PlanoCuidadosServico
from servicos.triagem_peso import AnimalNaoEncontradoError, TriagemPesoServico
from servicos.triagem_relato import TriagemRelatoServico

PASTA_UPLOADS = Path(__file__).resolve().parent.parent / "uploads"


@dataclass
class Servicos:
    """Tudo que as rotas usam. Em produção vem do Oracle e do Gemini; nos testes, dos dublês."""

    animais: object  # buscar_por_id, listar
    leituras: object  # listar
    recomendacoes: object  # listar_por_animal
    triagem_peso: TriagemPesoServico
    triagem_relato: TriagemRelatoServico
    plano_cuidados: PlanoCuidadosServico


def criar_app(montar_servicos: Callable[[], Servicos], pasta_uploads: Path = PASTA_UPLOADS) -> FastAPI:
    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        # monta (e conecta) só quando o servidor sobe, e não ao importar o módulo
        app.state.servicos = montar_servicos()
        yield

    app = FastAPI(
        title="CLYVO VET - IA de triagem",
        version="1.0.0",
        description="Triagem de peso (balança IoT), relato do tutor (texto e foto) e plano de cuidados por raça.",
        lifespan=ciclo_de_vida,
    )
    pasta_uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=pasta_uploads), name="uploads")

    # erros do domínio viram respostas HTTP, sem try/except em cada rota
    @app.exception_handler(AnimalNaoEncontradoError)
    @app.exception_handler(FichaNaoEncontradaError)
    async def nao_encontrado(_: Request, erro: LookupError):
        return JSONResponse(status_code=404, content={"detail": str(erro)})

    @app.exception_handler(LeituraInvalidaError)
    @app.exception_handler(RelatoInvalidoError)
    async def invalido(_: Request, erro: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(erro)})

    def servicos(request: Request) -> Servicos:
        return request.app.state.servicos

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/animais", response_model=list[AnimalSaida])
    def listar_animais(request: Request):
        return [AnimalSaida(**vars(a)) for a in servicos(request).animais.listar()]

    @app.get("/animais/{animal_id}/leituras", response_model=list[LeituraSaida])
    def listar_leituras(animal_id: int, request: Request):
        _garantir_animal(servicos(request), animal_id)
        return [LeituraSaida(**vars(l)) for l in servicos(request).leituras.listar(animal_id)]

    @app.get("/animais/{animal_id}/recomendacoes", response_model=list[RecomendacaoSaida])
    def listar_recomendacoes(animal_id: int, request: Request):
        _garantir_animal(servicos(request), animal_id)
        return [RecomendacaoSaida(**vars(r)) for r in servicos(request).recomendacoes.listar_por_animal(animal_id)]

    @app.post("/leituras", response_model=TriagemPesoSaida, status_code=status.HTTP_201_CREATED)
    def registrar_leitura(entrada: LeituraEntrada, request: Request):
        """Chamada pelo Node-RED a cada pesagem: grava a leitura e devolve a triagem da IA."""
        leitura_id, r = servicos(request).triagem_peso.processar_leitura(entrada.animal_id, entrada.peso)
        return TriagemPesoSaida(
            leitura_id=leitura_id,
            recomendacao_id=r.recomendacao_id,
            animal=r.animal.nome,
            nivel=r.nivel.name,
            problemas=[ProblemaSaida(codigo=p.codigo, descricao=p.descricao) for p in r.problemas],
            texto=r.texto,
            ficha_usada=r.ficha_usada,
            usou_llm=r.usou_llm,
            motivo_sem_llm=r.motivo_sem_llm,
        )

    @app.post("/animais/{animal_id}/relatos", response_model=RelatoSaida, status_code=status.HTTP_201_CREATED)
    async def enviar_relato(
        animal_id: int,
        request: Request,
        texto: str | None = Form(default=None),
        foto: UploadFile | None = File(default=None),
    ):
        """Relato do tutor: texto, foto do sintoma ou os dois (multipart/form-data)."""
        imagem = None
        if foto is not None and foto.filename:
            imagem = Imagem(await foto.read(), foto.content_type or "")
        r = servicos(request).triagem_relato.avaliar(animal_id, texto, imagem)
        return RelatoSaida(
            relato_id=r.relato_id,
            recomendacao_id=r.recomendacao_id,
            nivel=r.nivel.name,
            texto=r.texto,
            imagem_url=r.imagem_url,
            sinais_de_emergencia=list(r.sinais_de_emergencia),
            usou_llm=r.usou_llm,
            motivo_sem_llm=r.motivo_sem_llm,
        )

    @app.post("/animais/{animal_id}/plano-cuidados", response_model=PlanoSaida, status_code=status.HTTP_201_CREATED)
    def gerar_plano(animal_id: int, request: Request):
        r = servicos(request).plano_cuidados.gerar(animal_id)
        return PlanoSaida(**vars(r))

    return app


def _garantir_animal(s: Servicos, animal_id: int) -> None:
    if s.animais.buscar_por_id(animal_id) is None:
        raise HTTPException(status_code=404, detail=f"Animal {animal_id} não encontrado.")


def montar_servicos_reais() -> Servicos:
    # imports aqui: os testes da API não precisam do Oracle nem do Gemini instalados e configurados
    from armazenamento.local import ArmazenamentoLocal
    from config import carregar_config_api, carregar_config_gemini, carregar_config_oracle
    from llm.gemini import ClienteGemini
    from repositorios.oracle import (
        AnimalRepositorio,
        CuidadoRacaRepositorio,
        LeituraRepositorio,
        RecomendacaoRepositorio,
        RelatoRepositorio,
        criar_pool,
    )

    pool = criar_pool(carregar_config_oracle())
    gemini = carregar_config_gemini()
    llm = ClienteGemini(gemini.chave_api, gemini.modelo)
    animais, leituras = AnimalRepositorio(pool), LeituraRepositorio(pool)
    cuidados, recomendacoes = CuidadoRacaRepositorio(pool), RecomendacaoRepositorio(pool)
    fotos = ArmazenamentoLocal(PASTA_UPLOADS, f"{carregar_config_api().url_publica}/uploads")

    return Servicos(
        animais=animais,
        leituras=leituras,
        recomendacoes=recomendacoes,
        triagem_peso=TriagemPesoServico(animais, leituras, cuidados, recomendacoes, llm),
        triagem_relato=TriagemRelatoServico(animais, cuidados, RelatoRepositorio(pool), recomendacoes, fotos, llm),
        plano_cuidados=PlanoCuidadosServico(animais, cuidados, recomendacoes, llm),
    )


app = criar_app(montar_servicos_reais)
