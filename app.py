import streamlit as st
import pandas as pd
import pickle
import os

# =====================================================
# CONFIGURAÇÕES
# =====================================================
CONTRIBUICAO_MENSAL = 4000
GESTOR_PASSWORD = "assembleia123"
FICHEIRO_DADOS = "dados.pkl"

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]

MEMBROS = [
    "Hélvio Silva",
    "Domingos Capitão",
    "Feliciano Teca",
    "João Nguinamau",
    "Ageu Viegas",
    "José Caetano",
    "Edmilson Zambo",
    "Cristovão José",
    "Belarmino Cuca",
    "Domingos Nambuazão",
    "Matondo Panzo",
    "Edmamar Paulo",
    "Nkuna Nkumbo Gomez",
    "Fernando Bragança"
]

# =====================================================
# FUNÇÕES DE DADOS
# =====================================================
def carregar_dados():
    if os.path.exists(FICHEIRO_DADOS):
        with open(FICHEIRO_DADOS, "rb") as f:
            dados = pickle.load(f)
    else:
        dados = {}

    dados.setdefault("saldo_base", 0)
    dados.setdefault("saldo_acumulado", 0)
    dados.setdefault("mes_atual", MESES[0])
    dados.setdefault("historico", {})

    return dados


def guardar_dados(dados):
    with open(FICHEIRO_DADOS, "wb") as f:
        pickle.dump(dados, f)

# =====================================================
# FUNÇÕES DE NEGÓCIO
# =====================================================
def criar_mes(nome_mes):
    df = pd.DataFrame({
        "Nome": MEMBROS,
        "Valor_Pago": [0] * len(MEMBROS),
        "Estado": ["Não contribuiu"] * len(MEMBROS),
        "Observações": [f"Faltam {CONTRIBUICAO_MENSAL} Kz"] * len(MEMBROS)
    })

    dados["historico"][nome_mes] = {
        "tabela": df,
        "fechado": False,
        "total_mes": 0
    }


def recalcular_tabela(df):
    df["Valor_Pago"] = pd.to_numeric(
        df["Valor_Pago"], errors="coerce"
    ).fillna(0).astype(int)

    estados = []
    observacoes = []

    for valor in df["Valor_Pago"]:
        if valor >= CONTRIBUICAO_MENSAL:
            estados.append("Fechado")
            observacoes.append("Pago completo")
        elif valor > 0:
            estados.append("Faltou")
            observacoes.append(f"Faltam {CONTRIBUICAO_MENSAL - valor} Kz")
        else:
            estados.append("Não contribuiu")
            observacoes.append(f"Faltam {CONTRIBUICAO_MENSAL} Kz")

    df["Estado"] = estados
    df["Observações"] = observacoes
    return df

# =====================================================
# APP
# =====================================================
st.set_page_config(page_title="Assembleia", page_icon="logo.png", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0f172a, #1e293b);
}
h1,h2,h3,label,p {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# LOGOTIPO CENTRALIZADO
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", width=160)

st.title("Assembleia – Cotização Mensal")
st.divider()

# =====================================================
# ESTADO GLOBAL
# =====================================================
if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()

dados = st.session_state.dados

if "is_gestor" not in st.session_state:
    st.session_state.is_gestor = False

# =====================================================
# LOGIN DO GESTOR
# =====================================================
st.sidebar.title("🔐 Acesso do Gestor")

if not st.session_state.is_gestor:
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if senha == GESTOR_PASSWORD:
            st.session_state.is_gestor = True
            st.sidebar.success("Gestor autenticado")
            st.rerun()
        else:
            st.sidebar.error("Senha incorreta")
else:
    st.sidebar.success("Modo Gestor ativo")
    if st.sidebar.button("Sair"):
        st.session_state.is_gestor = False
        st.rerun()

# =====================================================
# SALDO BASE (GESTOR)
# =====================================================
if st.session_state.is_gestor:
    dados["saldo_base"] = st.sidebar.number_input(
        "Saldo acumulado anterior",
        min_value=0,
        value=int(dados["saldo_base"]),
        step=1000
    )

# =====================================================
# SELEÇÃO DE MÊS
# =====================================================
meses = list(dados["historico"].keys())
if dados["mes_atual"] not in meses:
    meses.append(dados["mes_atual"])

mes_selecionado = st.selectbox("📅 Selecionar mês", meses)

if mes_selecionado not in dados["historico"]:
    criar_mes(mes_selecionado)

mes_data = dados["historico"][mes_selecionado]

st.subheader(f"Mês: {mes_selecionado}")

# =====================================================
# TABELA + APLICAR ALTERAÇÕES
# =====================================================
if st.session_state.is_gestor and not mes_data["fechado"]:
    df_temp = st.data_editor(
        mes_data["tabela"],
        num_rows="fixed",
        use_container_width=True,
        key=f"editor_{mes_selecionado}"
    )

    if st.button("✅ Aplicar alterações"):
        mes_data["tabela"] = recalcular_tabela(df_temp)
        st.success("Alterações aplicadas")
        st.rerun()
else:
    st.dataframe(mes_data["tabela"], use_container_width=True)

# =====================================================
# TOTAIS
# =====================================================
total_mes = int(mes_data["tabela"]["Valor_Pago"].sum())
mes_data["total_mes"] = total_mes

saldo_total = dados["saldo_base"] + dados["saldo_acumulado"]

st.metric("💰 Total do mês", f"{total_mes} Kz")
st.metric("📦 Saldo acumulado", f"{saldo_total} Kz")

# =====================================================
# FECHAR / REABRIR MÊS
# =====================================================
if st.session_state.is_gestor:
    if not mes_data["fechado"]:
        if st.button("🔒 Fechar mês"):
            mes_data["fechado"] = True
            dados["saldo_acumulado"] += mes_data["total_mes"]

            idx = MESES.index(mes_selecionado)
            if idx + 1 < len(MESES):
                dados["mes_atual"] = MESES[idx + 1]

            guardar_dados(dados)
            st.success("Mês fechado com sucesso")
            st.rerun()
    else:
        if st.button("🔓 Reabrir mês"):
            mes_data["fechado"] = False
            dados["saldo_acumulado"] -= mes_data["total_mes"]
            guardar_dados(dados)
            st.warning("Mês reaberto para correção")
            st.rerun()

# =====================================================
# GUARDAR
# =====================================================
guardar_dados(dados)
