import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- ESTADO DA SESSÃO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- CONFIGURAÇÃO E DESIGN ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* 🛠️ A MARRETA PARA SUMIR COM O TEXTO SOBRANDO 🛠️ */
    /* Isso remove o primeiro elemento (o label) de qualquer rádio na barra lateral */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
        display: none !important;
        height: 0px !important;
        overflow: hidden !important;
        margin: 0px !important;
        padding: 0px !important;
    }}

    /* Botões Modernos do Menu */
    div[data-testid="stRadio"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 0px !important;
        margin-bottom: 10px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        cursor: pointer;
        border: 1px solid transparent !important;
    }}
    
    /* Esconde o círculo do rádio */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    /* Estilo Ativo */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold !important;
    }}

    /* Botões Gerais */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.2em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: 600; border: none;
        box-shadow: 0 4px 12px {st.session_state.cor_botao}44;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco"], "Carbos": [28, 15]})

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 26px; color: #1F2937; margin-bottom: 30px; margin-top: 20px;'>Menu</h1>", unsafe_allow_html=True)
    # Mesmo com o texto aqui, o CSS acima vai matá-lo na exibição
    aba = st.radio("SUMIR_COM_ISSO", ["🏠 Início", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- LÓGICA DAS TELAS ---
if aba == "🏠 Início":
    st.header("📝 Registrar")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110)
    with col2:
        alimento_sel = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        carbo_total = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        st.info(f"Carboidratos: {carbo_total}g")

    if st.button("Salvar Registro"):
        st.success("Salvo!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    with st.expander("🎨 Aparência e Temas"):
        c1, c2 = st.columns(2)
        with c1: st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        with c2: st.session_state.cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        if st.button("Aplicar Cores"): st.rerun()