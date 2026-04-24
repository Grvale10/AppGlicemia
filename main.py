import streamlit as st
import pandas as pd
from st_google_auth import add_auth
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="BioCare Kids - Google Login", layout="wide")

# ESTA LINHA É A QUE CRIA O BOTÃO DO GOOGLE
# Ela vai ler o 'google_client_id' que você colou nos Secrets do site
add_auth() 

if st.session_state.get("connected"):
    # --- SE ESTIVER LOGADO PELO GOOGLE ---
    user_info = st.session_state.get("user_info")
    st.sidebar.image(user_info.get("picture"), width=70)
    st.sidebar.write(f"Olá, {user_info.get('name')}")
    
    st.title("📊 Bem-vindo ao Controle de Glicemia")
    st.write("Você está logado com segurança via Google.")
    
    if st.sidebar.button("Log out"):
        st.session_state.connected = False
        st.rerun()

else:
    # --- SE NÃO ESTIVER LOGADO ---
    st.title("🔐 Acesso Restrito")
    st.info("Por favor, use o botão 'Sign in with Google' acima para acessar o app da família.")