import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# --- CONFIGURAÇÃO DE LOGIN (SIMPLIFICADA) ---
# Aqui definimos quem pode entrar no app
nomes = ["Família Valente"]
usuarios = ["admin"]
senhas = ["admin123"] # Depois troque por uma de sua preferência

# Criptografia da senha (necessário para segurança)
hashed_passwords = stauth.Hasher(senhas).generate()

authenticator = stauth.Authenticate(
    {'usernames': {usuarios[0]: {'name': nomes[0], 'password': hashed_passwords[0]}}},
    "glicemia_cookie", "signature_key", cookie_expiry_days=30
)

# Renderiza a tela de login
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Usuário ou senha incorretos")
elif authentication_status == None:
    st.warning("Por favor, insira seu usuário e senha")
elif authentication_status:
    # --- SE O LOGIN DER CERTO, RODA O APP ABAIXO ---

    if "cor_primaria" not in st.session_state:
        st.session_state.cor_primaria = "#007BFF"
    if "cor_fundo" not in st.session_state:
        st.session_state.cor_fundo = "#F8F9FA"

    # Estilo Visual (CSS)
    st.markdown(f"""
        <style>
        .stButton>button {{
            width: 100%;
            border-radius: 12px;
            background: linear-gradient(135deg, {st.session_state.cor_primaria}, #00c6ff);
            color: white; font-weight: bold; border: none; height: 3.5em;
        }}
        </style>
        """, unsafe_allow_html=True)

    # BARRA LATERAL
    with st.sidebar:
        st.title(f"Bem-vindo, {name}")
        aba = st.radio("Menu principal", ["🏠 Painel", "⚙️ Perfil e Temas", "🍎 Alimentos"])
        st.divider()
        authenticator.logout("Sair do Sistema", "sidebar")

    # TELAS DO APP
    if aba == "🏠 Painel":
        st.title("📊 Controle de Glicemia")
        # (Aqui entra o código das abas de registro que já fizemos)
        t1, t2 = st.tabs(["📝 Registrar", "📜 Histórico"])
        with t1:
            st.info("Área de registro pronta para uso.")
        with t2:
            st.info("O histórico aparecerá aqui.")

    elif aba == "⚙️ Perfil e Temas":
        st.header("👤 Configurações de Perfil")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nome da Criança", "Filha")
            st.number_input("Idade", 7)
        with col2:
            st.session_state.cor_primaria = st.color_picker("Cor dos Botões", st.session_state.cor_primaria)
            if st.button("Salvar Preferências"):
                st.rerun()

    elif aba == "🍎 Alimentos":
        st.header("🍎 Banco de Alimentos")
        st.write("Gerencie aqui os carboidratos da dieta.")