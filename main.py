import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE LOGIN ---
# Definindo usuário e senha de forma simples para a versão mais nova da biblioteca
credentials = {
    "usernames": {
        "admin": {
            "name": "Familia Valente",
            "password": "admin123"  # Você pode mudar sua senha aqui
        }
    }
}

# Inicializa o autenticador
authenticator = stauth.Authenticate(
    credentials,
    "glicemia_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# Renderiza a tela de login
name, authentication_status, username = authenticator.login("Acesso Restrito", "main")

# --- 2. VERIFICAÇÃO DE STATUS DE LOGIN ---
if authentication_status == False:
    st.error("Usuário ou senha incorretos")
elif authentication_status == None:
    st.warning("Por favor, faça login para acessar os dados da sua filha.")
elif authentication_status:
    
    # --- 3. INICIALIZAÇÃO DE DADOS E TEMAS (SÓ RODA SE LOGADO) ---
    if "cor_primaria" not in st.session_state:
        st.session_state.cor_primaria = "#FF4B4B"
    if "cor_fundo" not in st.session_state:
        st.session_state.cor_fundo = "#FFFFFF"

    # Aplicar CSS para botões e visual
    st.markdown(f"""
        <style>
        .stButton>button {{
            width: 100%; border-radius: 12px; height: 3.5em;
            background: linear-gradient(45deg, {st.session_state.cor_primaria}, #ff8a8a);
            color: white; border: none; font-weight: bold;
        }}
        .main {{ background-color: {st.session_state.cor_fundo}; }}
        </style>
        """, unsafe_allow_html=True)

    # Carregar Bancos de Dados
    try:
        df_historico = pd.read_csv("dados_glicemia.csv")
    except:
        df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

    try:
        df_alimentos = pd.read_csv("alimentos.csv")
    except:
        df_alimentos = pd.DataFrame({"Alimento": ["Manual"], "Carboidratos por Porção": [0], "Unidade": ["g"]})

    # --- 4. BARRA LATERAL ---
    with st.sidebar:
        st.title(f"Olá, {name}")
        menu = st.radio("Navegação", ["🏠 Painel Principal", "📌 Pendentes (2h Após)", "⚙️ Perfil e Temas", "🍎 Tabela de Alimentos"])
        st.divider()
        authenticator.logout("Sair do Sistema", "sidebar")

    # --- 5. LOGICA DAS TELAS ---
    if menu