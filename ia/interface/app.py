"""App do tutor (Streamlit): o ponto de entrada e de saída da IA, como no diagrama da Sprint 3.

A interface não acessa o banco nem o Gemini: tudo passa pela API (api/main.py).
Rodar (dentro de ia/, com a API no ar):  .venv/Scripts/python -m streamlit run interface/app.py
"""
import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
ESPECIES = {"DOG": "Cão", "CAT": "Gato"}
ORIGENS = {"PESO": "Balança", "RELATO": "Relato do tutor", "CUIDADO_RACA": "Plano de cuidados"}
ROTULOS = {"NORMAL": "🟢 NORMAL", "ATENCAO": "🟡 ATENÇÃO", "ALERTA": "🔴 ALERTA"}

st.set_page_config(page_title="CLYVO VET - Saúde do pet", page_icon="🐾", layout="wide")


def chamar(metodo: str, caminho: str, **kwargs):
    """Chama a API e mostra o erro de forma amigável, em vez de quebrar a tela."""
    try:
        # 60 s: a API espera até 30 s pelo Gemini antes do plano B
        resposta = httpx.request(metodo, f"{API_URL}{caminho}", timeout=60, **kwargs)
    except httpx.HTTPError:
        st.error(f"Não foi possível falar com a API em {API_URL}. Ela está rodando?")
        st.stop()
    if resposta.status_code >= 400:
        st.error(resposta.json().get("detail", "Erro na API."))
        return None
    return resposta.json()


def mostrar_resultado(nivel: str, texto: str, usou_llm: bool, motivo: str | None) -> None:
    caixa = {"NORMAL": st.success, "ATENCAO": st.warning, "ALERTA": st.error}[nivel]
    caixa(f"**{ROTULOS[nivel]}**\n\n{texto}")
    if usou_llm:
        st.caption("Orientação escrita pela IA (Gemini) a partir das regras e da ficha da raça.")
    else:
        st.caption(f"Orientação gerada pelas regras, sem o LLM ({motivo}).")


# ---------- escolha do animal ----------
st.title("🐾 CLYVO VET · Saúde do pet")
st.caption("Acompanhamento contínuo com IA: balança inteligente, relato de sintomas e plano de cuidados.")

animais = chamar("GET", "/animais") or []
if not animais:
    st.info("Nenhum animal cadastrado. Cadastre pela API da CLYVO VET (.NET).")
    st.stop()

with st.sidebar:
    st.header("Seu pet")
    animal = st.selectbox(
        "Animal",
        animais,
        format_func=lambda a: f"{a['nome']} · {a['raca']} (#{a['id']})",
    )
    st.metric("Peso no cadastro", f"{animal['peso_cadastro']} kg")
    st.write(f"**Espécie:** {ESPECIES.get(animal['especie'], animal['especie'])}")
    st.write(f"**Nascimento:** {animal['nascimento'] or 'não informado'}")
    st.caption(f"API: {API_URL}")

aba_peso, aba_relato, aba_cuidados, aba_historico = st.tabs(
    ["⚖️ Pesagens", "📝 Relatar sintoma", "💉 Plano de cuidados", "📋 Histórico da IA"]
)

# ---------- pesagens ----------
with aba_peso:
    leituras = chamar("GET", f"/animais/{animal['id']}/leituras") or []
    if leituras:
        tabela = pd.DataFrame(leituras)
        tabela["peso"] = tabela["peso"].astype(float)
        tabela["data"] = pd.to_datetime(tabela["data"])
        ultima = tabela.iloc[-1]
        st.metric("Última pesagem", f"{ultima['peso']:.2f} kg", f"{ultima['peso'] - float(animal['peso_cadastro']):+.2f} kg vs. cadastro")
        st.line_chart(tabela, x="data", y="peso", height=260)
    else:
        st.info("Ainda não há pesagens deste animal. Elas chegam pela balança (ESP32 → MQTT → Node-RED).")

    with st.form("pesagem"):
        st.write("**Simular uma pesagem** (o mesmo caminho da balança: `POST /leituras`)")
        peso = st.number_input("Peso (kg)", min_value=0.1, max_value=100.0, value=float(animal["peso_cadastro"]), step=0.1)
        if st.form_submit_button("Registrar pesagem"):
            r = chamar("POST", "/leituras", json={"animal_id": animal["id"], "peso": peso})
            if r:
                for p in r["problemas"]:
                    st.write(f"- `{p['codigo']}` {p['descricao']}")
                mostrar_resultado(r["nivel"], r["texto"], r["usou_llm"], r["motivo_sem_llm"])

# ---------- relato do tutor ----------
with aba_relato:
    st.write("Conte o que está acontecendo e, se quiser, envie uma foto do sintoma.")
    with st.form("relato", clear_on_submit=False):
        texto = st.text_area("O que você observou?", max_chars=2000, placeholder="Ex.: está coçando muito a orelha desde ontem")
        foto = st.file_uploader("Foto do sintoma (opcional)", type=["jpg", "jpeg", "png", "webp"])
        if st.form_submit_button("Enviar para a triagem"):
            arquivos = {"foto": (foto.name, foto.getvalue(), foto.type)} if foto else None
            with st.spinner("A IA está analisando o relato..."):
                r = chamar("POST", f"/animais/{animal['id']}/relatos", data={"texto": texto}, files=arquivos)
            if r:
                if r["sinais_de_emergencia"]:
                    st.error("Sinais de emergência identificados: " + ", ".join(r["sinais_de_emergencia"]))
                mostrar_resultado(r["nivel"], r["texto"], r["usou_llm"], r["motivo_sem_llm"])
                if r["imagem_url"]:
                    st.image(foto, caption="Foto registrada no relato", width=260)

# ---------- plano de cuidados ----------
with aba_cuidados:
    st.write("Plano preventivo montado a partir da base de cuidados da raça, da idade e do peso.")
    if st.button("Gerar plano de cuidados"):
        with st.spinner("Montando o plano..."):
            r = chamar("POST", f"/animais/{animal['id']}/plano-cuidados")
        if r:
            st.write(f"**Ficha usada:** {r['ficha_usada']} · **Idade:** {r['idade']}")
            st.info(r["texto"])
            st.caption("Escrito pela IA (Gemini)." if r["usou_llm"] else f"Ficha da base, sem o LLM ({r['motivo_sem_llm']}).")

# ---------- histórico ----------
with aba_historico:
    st.write("Toda orientação da IA fica registrada (`T_AI_RECOMMENDATION`), para o tutor e para a clínica.")
    recomendacoes = chamar("GET", f"/animais/{animal['id']}/recomendacoes") or []
    filtro = st.multiselect("Nível", list(ROTULOS), default=list(ROTULOS), format_func=ROTULOS.get)
    for r in recomendacoes:
        if r["nivel"] not in filtro:
            continue
        data = pd.to_datetime(r["data"]).strftime("%d/%m/%Y %H:%M")
        with st.expander(f"{ROTULOS[r['nivel']]} · {ORIGENS.get(r['origem'], r['origem'])} · {data}"):
            st.write(r["texto"])
    if not recomendacoes:
        st.info("Nenhuma orientação registrada ainda.")
