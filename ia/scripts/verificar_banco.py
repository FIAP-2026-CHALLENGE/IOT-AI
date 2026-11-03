"""Confere a ligação com o Oracle e mostra o que a IA vai usar para um animal.

Uso (dentro de ia/):  .venv/Scripts/python -m scripts.verificar_banco <id_do_animal>
"""
import sys

from config import carregar_config_oracle
from dominio.cuidados import encontrar_ficha
from dominio.peso import LEITURAS_DE_REFERENCIA
from repositorios.oracle import (
    AnimalRepositorio,
    CuidadoRacaRepositorio,
    LeituraRepositorio,
    criar_pool,
)


def main(animal_id: int) -> None:
    pool = criar_pool(carregar_config_oracle())

    animal = AnimalRepositorio(pool).buscar_por_id(animal_id)
    if animal is None:
        print(f"Animal {animal_id} não existe em T_CP_ANIMAIS.")
        return
    print(f"Animal: {animal.nome} ({animal.especie}, {animal.raca}), {animal.peso_cadastro} kg no cadastro")

    fichas = CuidadoRacaRepositorio(pool).listar_por_especie(animal.especie)
    print(f"Fichas de {animal.especie} em T_BREED_CARE: {len(fichas)}")
    ficha = encontrar_ficha(animal.raca, fichas)
    if ficha is None:
        print("Nenhuma ficha encontrada (rodou o 02_seed_cuidados_racas.sql?).")
    else:
        faixa = f"{ficha.faixa.minimo} a {ficha.faixa.maximo} kg" if ficha.faixa else "sem faixa"
        print(f"Ficha usada: {ficha.raca} ({faixa})")

    historico = LeituraRepositorio(pool).historico(animal_id, LEITURAS_DE_REFERENCIA)
    print(f"Últimas leituras em T_EXAM_READING: {[str(p) for p in historico] or 'nenhuma'}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("Uso: python -m scripts.verificar_banco <id_do_animal>")
    main(int(sys.argv[1]))
