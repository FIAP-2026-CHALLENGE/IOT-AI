"""Textos enviados ao LLM. Ficam separados do serviço para serem lidos e ajustados num lugar só."""
from dominio.animal import Animal
from dominio.cuidados import FichaCuidado
from dominio.peso import Nivel, ResultadoPeso

ESPECIES = {"DOG": "cão", "CAT": "gato"}

INSTRUCOES_TRIAGEM = """\
Você é o assistente de triagem da CLYVO VET e escreve para o tutor de um cão ou gato.
Regras:
- O nível (NORMAL, ATENCAO ou ALERTA) já foi decidido pelo sistema: não altere o nível.
- Use apenas os dados e a ficha da raça enviados. Não invente valores, unidades, causas ou exames.
- Da ficha, use só o que tiver relação com o problema encontrado (ex.: peso, obesidade, respiração).
- Sinal de emergência citado na ficha (ex.: gengiva arroxeada, dificuldade para respirar) é atendimento imediato, nunca "agendar consulta".
- Você orienta, não faz diagnóstico: não faça diagnóstico nem indique remédios ou doses.
- Em ALERTA, recomende procurar o veterinário em breve; em ATENCAO, acompanhar e agendar consulta se continuar.
- Português simples, frases curtas, no máximo 120 palavras.
Formato:
Resumo: <uma frase sobre o que foi observado>
O que fazer: <2 ou 3 itens começando com "- ">
Quando procurar o veterinário: <uma frase>"""


def prompt_peso(animal: Animal, resultado: ResultadoPeso, ficha: FichaCuidado | None) -> str:
    linhas = [
        f"Animal: {animal.nome} ({ESPECIES.get(animal.especie, animal.especie)}, raça {animal.raca}).",
        f"Peso medido agora pela balança: {resultado.peso} kg.",
        f"Nível decidido pelo sistema: {resultado.nivel.name}.",
        "Problemas encontrados pelas regras:",
        *[f"- {p.descricao}" for p in resultado.problemas],
        *[f"Observação: {o}" for o in resultado.observacoes],
        "",
        _bloco_ficha(ficha),
        "",
        "Escreva a recomendação para o tutor.",
    ]
    return "\n".join(linhas)


def texto_sem_llm(resultado: ResultadoPeso) -> str:
    """Recomendação montada só com a regra: para NORMAL e quando o LLM está fora do ar."""
    if resultado.nivel == Nivel.NORMAL:
        return f"Resumo: peso de {resultado.peso} kg dentro do esperado. Continue com as pesagens de rotina."

    problemas = " ".join(p.descricao for p in resultado.problemas)
    if resultado.nivel == Nivel.ALERTA:
        conduta = "Procure o veterinário em breve e leve o histórico de pesagens."
    else:
        conduta = "Acompanhe as próximas pesagens e agende uma consulta com o veterinário se continuar."
    return f"Resumo: {problemas} O que fazer: {conduta}"


def _bloco_ficha(ficha: FichaCuidado | None) -> str:
    if ficha is None:
        return "Ficha da raça: nenhuma ficha disponível."
    return (
        f"Ficha da raça ({ficha.raca}), base de cuidados da clínica:\n"
        f"Cuidados: {ficha.cuidados}\n"
        f"Vacinas: {ficha.vacinas}"
    )
