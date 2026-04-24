import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- ESTADO DA SESSÃO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- DESIGN E REMOÇÃO TOTAL DE RÓTULOS ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* 🛠️ A SOLUÇÃO DEFINITIVA PARA O TEXTO SOBRANDO 🛠️ */
    /* Remove qualquer label, div de legenda ou texto explicativo dentro do rádio lateral */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stRadio"] caption {{
        display: none !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        visibility: hidden !important;
    }}

    /* Estilo dos Botões do Menu */
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
    
    /* Esconde o círculo do rádio original */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    /* Botão Selecionado */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold !important;
    }}

    /* Botões de Ação no Conteúdo */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS COM AUTO-CORREÇÃO ---
def iniciar_dados():
    # Garantir que alimentos.csv seja válido
    try:
        if os.path.exists("alimentos.csv"):
            df = pd.read_csv("alimentos.csv")
            if "Alimento" not in df.columns or "Carbos" not in df.columns:
                raise ValueError("Colunas incorretas")
        else:
            raise FileNotFoundError
    except:
        df = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco"], "Carbos": [28.0, 15.0]})
        df.to_csv("alimentos.csv", index=False)
    
    # Garantir que dados_glicemia.csv seja válido
    try:
        if os.path.exists("dados_glicemia.csv"):
            hist = pd.read_csv("dados_glicemia.csv")
        else:
            raise FileNotFoundError
    except:
        hist = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento"])
        hist.to_csv("dados_glicemia.csv", index=False)
    
    return df, hist

df_alimentos, df_historico = iniciar_dados()

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 26px; color: #1F2937; margin-bottom: 30px; margin-top: 20px;'>Menu</h1>", unsafe_allow_html=True)
    # O CSS acima vai garantir que o nome "Seletor" nunca apareça
    aba = st.radio("Seletor", ["🏠 Início", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- TELAS ---
if aba == "🏠 Início":
    st.header("📝 Registrar")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110)
    with col2:
        lista_alimentos = df_alimentos["Alimento"].tolist()
        alimento_sel = st.selectbox("Escolha o Alimento", lista_alimentos)
        
        # Proteção contra erro de busca
        try:
            carbo_base = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        except:
            carbo_base = 0.0
            
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        total_c = round(float(carbo_base) * qtd, 1)
        st.info(f"Carboidratos Totais: {total_c}g")

    if st.button("Salvar Registro"):
        # Cálculo: (Glicemia - Meta) / Sensibilidade + (Carbo / Relação)
        dose = round(((g_pre - 100) / 50) + (total_c / 15), 1)
        novo_reg = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": total_c, "Dose": max(0.0, dose), "Momento": "Refeição"}])
        df_historico = pd.concat([df_historico, novo_reg], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose sugerida: {max(0.0, dose)} U. Salvo com sucesso!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Gerenciar Tabela")
    df_novo = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações"):
        df_novo.to_csv("alimentos.csv", index=False)
        st.success("Tabela atualizada!")

elif aba == "👤 Perfil":
    st.header("👤 Configurações")
    with st.expander("🎨 Temas e Cores"):
        c1, c2 = st.columns(2)
        with c1: st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        with c2: st.session_state.cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()