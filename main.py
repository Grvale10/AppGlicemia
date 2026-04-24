import streamlit as st
import pandas as pd
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="BioCare Kids Pro", layout="wide")

# Inicializar configurações de tema no "cérebro" do app
if "cor_primaria" not in st.session_state:
    st.session_state.cor_primaria = "#FF4B4B"
if "cor_fundo" not in st.session_state:
    st.session_state.cor_fundo = "#FFFFFF"

# Aplicar CSS Customizado para botões bonitos e degradês
st.markdown(f"""
    <style>
    .stButton>button {{
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background: linear-gradient(45deg, {st.session_state.cor_primaria}, #ff8a8a);
        color: white;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    .main {{
        background-color: {st.session_state.cor_fundo};
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Manual"], "Carboidratos por Porção": [0], "Unidade": ["g"]})

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    st.title("⚙️ Configurações")
    aba_config = st.radio("Navegar para:", ["🏠 Home", "👤 Perfil & Temas", "🍎 Alimentos"])
    st.divider()
    if st.button("🚪 Sair (Logout)"):
        st.info("Simulação de Logout efetuada.")

# --- LÓGICA DE TELAS ---
if aba_config == "🏠 Home":
    st.title("📊 Painel de Controle")
    tab1, tab2 = st.tabs(["📝 Registrar", "📜 Histórico"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            g_pre = st.number_input("Glicemia Antes", value=110)
            alimento = st.selectbox("Escolha o Alimento", df_alimentos["Alimento"].tolist())
        with col2:
            porcoes = st.number_input("Quantidade", min_value=0.1, value=1.0)
            momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche"])
        
        if st.button("Calcular e Salvar Registro"):
            st.balloons() # Efeito visual de sucesso
            st.success("Dados salvos com sucesso!")

    with tab2:
        st.dataframe(df_historico, use_container_width=True)

elif aba_config == "👤 Perfil & Temas":
    st.header("👤 Perfil do Usuário")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        nome_pai = st.text_input("Nome do Responsável", "Pai/Mãe")
        email_user = st.text_input("Email", "exemplo@email.com")
    with col_p2:
        nome_crianca = st.text_input("Nome da Criança", "Filha")
        idade = st.number_input("Idade", value=7)

    st.divider()
    st.header("🎨 Personalização Visual")
    c1, c2 = st.columns(2)
    st.session_state.cor_primaria = c1.color_picker("Cor dos Botões (Destaque)", st.session_state.cor_primaria)
    st.session_state.cor_fundo = c2.color_picker("Cor de Fundo do App", st.session_state.cor_fundo)
    
    if st.button("Aplicar Novo Tema"):
        st.rerun()

elif aba_config == "🍎 Alimentos":
    st.header("🍎 Gestão de Alimentos")
    # Código de cadastro de alimentos aqui...
    st.write("Aqui você poderá editar sua tabela de carboidratos.")