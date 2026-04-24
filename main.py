import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- ESTADO DA SESSÃO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- DESIGN MODERNO E LIMPEZA DE SELETORES ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* 🛠️ REMOÇÃO TOTAL DE QUALQUER TEXTO SOBRANTE NO MENU 🛠️ */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {{
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }}

    /* Botões do Menu Lateral */
    div[data-testid="stRadio"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 0px !important;
        margin-bottom: 10px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border: 1px solid transparent !important;
    }}
    
    /* Esconde o círculo do rádio */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    /* Estilo Ativo do Menu */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold !important;
    }}

    /* Botões de Ação */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.2em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: 600; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS COM PROTEÇÃO ---
def carregar_alimentos():
    try:
        df = pd.read_csv("alimentos.csv")
        # Garante que as colunas necessárias existam
        if "Alimento" not in df.columns: df["Alimento"] = ["Pão"]
        if "Carbos" not in df.columns: df["Carbos"] = [28]
        return df
    except:
        return pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco"], "Carbos": [28, 15]})

df_alimentos = carregar_alimentos()

try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento"])

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 26px; color: #1F2937; margin-bottom: 30px; margin-top: 20px;'>Menu</h1>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- LÓGICA DAS TELAS ---
if aba == "🏠 Início":
    st.header("📝 Registrar")
    col1, col2 = st.columns(2)
    
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110)
        
    with col2:
        lista_nomes = df_alimentos["Alimento"].tolist()
        alimento_sel = st.selectbox("Escolha o Alimento", lista_nomes)
        
        # 🛡️ PROTEÇÃO CONTRA KEYERROR 🛡️
        try:
            valor_carbo = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        except:
            valor_carbo = 0
            
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        total_carbo = round(float(valor_carbo) * qtd, 1)
        st.info(f"Carboidratos Totais: {total_carbo}g")

    if st.button("Salvar Registro"):
        # Cálculo simples para exemplo (Meta 100, Sensibilidade 50, Relação 15)
        dose = round(((g_pre - 100) / 50) + (total_carbo / 15), 1)
        st.success(f"Dose Calculada: {max(0.0, dose)} U. Salvo!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Gerenciar Alimentos")
    st.write("Edite os valores abaixo e clique em Salvar.")
    df_editado = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Tabela"):
        df_editado.to_csv("alimentos.csv", index=False)
        st.success("Tabela atualizada!")

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    with st.expander("🎨 Aparência e Temas"):
        c1, c2 = st.columns(2)
        with c1: st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        with c2: st.session_state.cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        if st.button("Aplicar Cores"): st.rerun()