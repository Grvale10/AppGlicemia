import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE LOGIN (ESTRUTURA FINAL) ---
if 'credentials' not in st.session_state:
    st.session_state['credentials'] = {
        "usernames": {
            "admin": {
                "name": "Familia Valente",
                "password": "admin123" 
            }
        }
    }

# Inicializa o autenticador sem firulas
authenticator = stauth.Authenticate(
    st.session_state['credentials'],
    "glicemia_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# LOGIN CORRIGIDO: Agora os parâmetros devem ser vazios ou nomeados
# A biblioteca nova não aceita mais o texto direto aqui
authenticator.login()

# Pegamos o status direto da sessão do Streamlit
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")

# --- 2. VERIFICAÇÃO DE STATUS ---
if authentication_status == False:
    st.error("Usuário ou senha incorretos")
elif authentication_status == None:
    st.warning("Área Restrita: Por favor, identifique-se.")
elif authentication_status:
    
    # --- 3. INICIALIZAÇÃO DE DADOS E TEMAS ---
    if "cor_primaria" not in st.session_state:
        st.session_state.cor_primaria = "#FF4B4B"
    if "cor_fundo" not in st.session_state:
        st.session_state.cor_fundo = "#FFFFFF"

    # Aplicar Estilo Visual
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

    # Carregar Dados
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
        menu = st.radio("Navegação", ["🏠 Painel Principal", "📌 Pendentes (2h Após)", "📜 Histórico Completo", "⚙️ Perfil e Temas", "🍎 Alimentos"])
        st.divider()
        authenticator.logout("Sair do Sistema", "sidebar")

    # --- 5. TELAS ---
    if menu == "🏠 Painel Principal":
        st.title("📊 Registro de Refeição")
        c1, c2 = st.columns(2)
        with c1:
            g_pre = st.number_input("Glicemia Antes", value=110)
            selecionado = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
            dado_ali = df_alimentos[df_alimentos["Alimento"] == selecionado].iloc[0]
        with c2:
            qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
            mom = st.selectbox("Momento", ["Café", "Almoço", "Lanche", "Jantar"])
            carbo_t = dado_ali['Carboidratos por Porção'] * qtd

        if st.button("Salvar Registro"):
            dose = calcular_insulina(g_pre, 100, 50, carbo_t, 15)
            novo = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": carbo_t, "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}
            df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
            df_historico.to_csv("dados_glicemia.csv", index=False)
            st.success("Salvo!")

    elif menu == "📌 Pendentes (2h Após)":
        st.header("📌 Glicemia Pós-Prandial")
        pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
        if not pendentes.empty:
            for idx, row in pendentes.iterrows():
                with st.expander(f"{row['Momento']} - {row['Data']}"):
                    val = st.number_input(f"Valor após 2h", key=f"pos_{idx}")
                    if st.button("Salvar", key=f"btn_{idx}"):
                        df_historico.at[idx, "Glicemia_Pos"] = val
                        df_historico.to_csv("dados_glicemia.csv", index=False)
                        st.rerun()
        else:
            st.info("Nada pendente!")

    elif menu == "📜 Histórico Completo":
        st.header("📜 Histórico")
        st.dataframe(df_historico, use_container_width=True)

    elif menu == "⚙️ Perfil e Temas":
        st.header("⚙️ Personalizar")
        st.session_state.cor_primaria = st.color_picker("Cor dos Botões", st.session_state.cor_primaria)
        if st.button("Aplicar"): st.rerun()

    elif menu == "🍎 Alimentos":
        st.header("🍎 Nova Comida")
        # (Cadastro de alimentos simplificado aqui)