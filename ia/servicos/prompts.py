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


# ---------- Relato do tutor (texto e/ou foto) ----------

INSTRUCOES_RELATO = """\
Você é o assistente de triagem da CLYVO VET e lê o relato do tutor de um cão ou gato (texto, foto ou os dois).
Classifique o nível:
- NORMAL: nada preocupante no relato; manter a rotina.
- ATENCAO: sinal que pede acompanhamento e consulta se continuar (ex.: comer menos por um dia, coceira, mancha pequena).
- ALERTA: precisa de veterinário em breve ou imediatamente.
Regras:
- Se o sistema informar sinais de emergência, o nível é ALERTA e a orientação é atendimento imediato.
- Na foto, descreva só o que é visível (cor, tamanho, local), sem afirmar qual é a doença. Se a foto não mostrar um animal ou o sintoma, diga isso.
- Use apenas o relato, a foto e a ficha da raça enviados; da ficha, só o que tiver relação com o relato.
- Você orienta, não faz diagnóstico: não faça diagnóstico nem indique remédios ou doses.
- Português simples, frases curtas, no máximo 130 palavras.
Formato (a primeira linha é obrigatória e exatamente assim):
Nível: <NORMAL, ATENCAO ou ALERTA>
Resumo: <uma frase sobre o que foi relatado ou visto na foto>
O que fazer: <2 ou 3 itens começando com "- ">
Quando procurar o veterinário: <uma frase>"""


def prompt_relato(
    animal: Animal, texto: str | None, tem_foto: bool, sinais: list[str], ficha: FichaCuidado | None
) -> str:
    linhas = [
        f"Animal: {animal.nome} ({ESPECIES.get(animal.especie, animal.especie)}, raça {animal.raca}).",
        f"Relato do tutor: {texto if texto else '(sem texto, só a foto)'}",
        f"Foto do sintoma: {'enviada junto' if tem_foto else 'não enviada'}.",
        "Sinais de emergência detectados pelo sistema: " + (", ".join(sinais) if sinais else "nenhum") + ".",
        "",
        _bloco_ficha(ficha),
        "",
        "Classifique o nível e escreva a orientação para o tutor.",
    ]
    return "\n".join(linhas)


def texto_relato_sem_llm(sinais: list[str]) -> str:
    """Plano B do relato: sem o LLM, o código não interpreta o texto, então orienta com cautela."""
    if sinais:
        return (
            f"Resumo: o relato cita {', '.join(sinais)}. "
            "O que fazer: procure atendimento veterinário imediato."
        )
    return (
        "Resumo: recebemos o relato, mas a análise automática não está disponível agora. "
        "O que fazer: observe o animal e agende uma consulta se o sinal continuar ou piorar."
    )


# ---------- Plano de cuidados por raça ----------

INSTRUCOES_CUIDADOS = """\
Você é o assistente da CLYVO VET e monta um plano de cuidados preventivos para o tutor de um cão ou gato.
Regras:
- Use apenas a ficha da raça, a idade e o peso enviados. Não invente vacinas, exames, datas ou valores.
- Filhote (menos de 1 ano): destaque o esquema de doses de filhote da ficha. Adulto: os reforços anuais.
- Você orienta, não faz diagnóstico nem indica remédios ou doses; o calendário final é definido pelo veterinário.
- Português simples, no máximo 150 palavras.
Formato:
Vacinas: <2 ou 3 itens começando com "- ">
Cuidados da raça: <2 ou 3 itens começando com "- ">
Próximo passo: <uma frase>"""


def prompt_cuidados(animal: Animal, idade: str, ficha: FichaCuidado) -> str:
    return "\n".join([
        f"Animal: {animal.nome} ({ESPECIES.get(animal.especie, animal.especie)}, raça {animal.raca}).",
        f"Idade: {idade}. Peso no cadastro: {animal.peso_cadastro} kg.",
        "",
        _bloco_ficha(ficha),
        "",
        "Monte o plano de cuidados.",
    ])


def texto_cuidados_sem_llm(ficha: FichaCuidado) -> str:
    """Plano B dos cuidados: a própria ficha da base, sem personalização."""
    return f"Vacinas: {ficha.vacinas}\nCuidados da raça: {ficha.cuidados}"
