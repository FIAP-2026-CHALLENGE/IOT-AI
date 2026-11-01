"""Roda a triagem de peso de ponta a ponta, com o Oracle e o Gemini reais.

Uso (dentro de ia/):  .venv/Scripts/python -m scripts.triagem_peso <id_do_animal> <peso_em_kg>
Simula a balança: grava a leitura em T_EXAM_READING (como o Node-RED) e depois
a recomendação em T_AI_RECOMMENDATION. Rodar várias vezes monta o histórico.
"""
import sys
from decimal import Decimal, InvalidOperation

from config import carregar_config_gemini, carregar_config_oracle
from llm.gemini import ClienteGemini
from repositorios.oracle import (
    AnimalRepositorio,
    CuidadoRacaRepositorio,
    LeituraRepositorio,
    RecomendacaoRepositorio,
    criar_pool,
)
from servicos.triagem_peso import TriagemPesoServico


def main(animal_id: int, peso: Decimal) -> None:
    pool = criar_pool(carregar_config_oracle())
    gemini = carregar_config_gemini()
    servico = TriagemPesoServico(
        animais=AnimalRepositorio(pool),
        leituras=LeituraRepositorio(pool),
        cuidados=CuidadoRacaRepositorio(pool),
        recomendacoes=RecomendacaoRepositorio(pool),
        llm=ClienteGemini(gemini.chave_api, gemini.modelo),
    )

    leitura_id, r = servico.processar_leitura(animal_id, peso)

    print(f"Animal: {r.animal.nome} ({r.animal.especie}, {r.animal.raca}) | ficha usada: {r.ficha_usada}")
    origem_texto = "Gemini" if r.usou_llm else f"plano B (regra), motivo: {r.motivo_sem_llm}"
    print(f"Nível: {r.nivel.name} | texto do {origem_texto}")
    print(f"Leitura gravada em T_EXAM_READING com ID {leitura_id}.")
    for p in r.problemas:
        print(f"  - {p.codigo}: {p.descricao}")
    print(f"\n{r.texto}\n")
    print(f"Gravado em T_AI_RECOMMENDATION com ID {r.recomendacao_id}.")


if __name__ == "__main__":
    try:
        main(int(sys.argv[1]), Decimal(sys.argv[2]))
    except (IndexError, ValueError, InvalidOperation):
        sys.exit("Uso: python -m scripts.triagem_peso <id_do_animal> <peso_em_kg>  (ex.: 1 2.90)")
