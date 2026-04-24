import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- ESTADO DA SESSÃO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- DESIGN E LIMPEZA DE SELETORES ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* 1. REMOVE O TEXTO CHATO (O RÓTULO DO RADIO) */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
        display: none !important;
    }}

    /* 2. ESTILIZAÇÃO DOS BOTÕES DO MENU */
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease;
    }}
    
    /* GARANTE QUE O TEXTO DENTRO DO BOTÃO APAREÇA */
    div[data-testid="stRadio"] div[role="radiogroup"] label p {{
        color: #1F2937 !important;
        font-size: 16px !important;
        margin: 0px !important;
        display: block !important;
        opacity: 1 !important;
    }}

    /* 3. ESCONDE O CÍRCULO DO RADIO */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    /* 4. ESTILO DO BOTÃO SELECIONADO */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold !important;
    }}

    /* BOTÃO SALVAR REGISTRO */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE CARGA DE DADOS (ANTI-ERRO) ---
def carregar_dados_seguro():
    # Alimentos
    if os.path.exists("alimentos.csv"):
        df = pd.read_csv("alimentos.csv")
        if "Alimento" not in df.columns or "Carbos" not in df.columns:
            df = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz"], "Carbos": [28.0, 15.0]})
    else:
        df = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz"], "Carbos": [28.0, 15.0]})
    
    # Histórico
    if os.path.exists("dados_glicemia.csv"):
        hist = pd.read_csv("dados_glicemia.csv")
    else:
        hist = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento"])
    
    return df, hist

df_alimentos, df_historico = carregar_dados_seguro()

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 24px; color: #1F2937; margin-bottom: 25px;'>Menu</h1>", unsafe_allow_html=True)
    # label_visibility="collapsed" é nativo do Streamlit para o que você quer
    aba = st.radio("Menu_Principal", ["🏠 Início", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- TELAS ---
if aba == "🏠 Início":
    st.header("📝 Registrar")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual", min_value=20, value=110)
    with col2:
        lista = df_alimentos["Alimento"].tolist()
        alimento_sel = st.selectbox("Alimento", lista)
        
        # Busca segura para evitar KeyError
        carbo_linha = df_alimentos[df_alimentos["Alimento"] == alimento_sel]
        carbo_base = carbo_linha["Carbos"].values[0] if not carbo_linha.empty else 0.0
            
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        st.info(f"Total: {round(carbo_base * qtd, 1)}g de Carbo")

    if st.button("Salvar Registro"):
        dose = round(((g_pre - 100) / 50) + ((carbo_base * qtd) / 15), 1)
        st.success(f"Dose: {max(0.0, dose)} U. Salvo!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    novo_df = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Tabela"):
        novo_df.to_csv("alimentos.csv", index=False)
        st.success("Salvo!")

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    with st.expander("🎨 Temas"):
        st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        st.session_state.cor_botao = st.color_picker("Botão", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()