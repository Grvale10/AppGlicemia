import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE LOGIN ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Familia Valente",
            "password": "admin123" 
        }
    }
}

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
    st.warning("Por favor, faça login para acessar os dados.")
elif authentication_status:
    
    # --- 3. INICIALIZAÇÃO DE DADOS E TEMAS ---
    if "cor_primaria" not in st.session_state:
        st.session_state.cor_primaria = "#FF4B4B"
    if "cor_fundo" not in st.session_state:
        st.session_state.cor_fundo = "#FFFFFF"

    # Aplicar CSS Customizado
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
        menu = st.radio("Navegação", ["🏠 Painel Principal", "📌 Pendentes (2h Após)", "📜 Histórico Completo", "⚙️ Perfil e Temas", "🍎 Tabela de Alimentos"])
        st.divider()
        authenticator.logout("Sair do Sistema", "sidebar")

    # --- 5. LÓGICA DAS TELAS ---
    if menu == "🏠 Painel Principal":
        st.title("📊 Registro de Refeição")
        col1, col2 = st.columns(2)
        
        with col1:
            g_pre = st.number_input("Glicemia Antes (mg/dL)", value=110)
            lista_ali = df_alimentos["Alimento"].tolist()
            selecionado = st.selectbox("Selecione o Alimento", lista_ali)
            dado_ali = df_alimentos[df_alimentos["Alimento"] == selecionado].iloc[0]
            st.caption(f"Padrão: {dado_ali['Unidade']} possui {dado_ali['Carboidratos por Porção']}g de carbo.")
        
        with col2:
            qtd = st.number_input("Quantidade de porções", min_value=0.1, value=1.0)
            momento = st.selectbox("Refeição", ["Café", "Almoço", "Lanche", "Jantar", "Ceia"])
            carbo_total = dado_ali['Carboidratos por Porção'] * qtd

        if st.button("Calcular e Salvar"):
            dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
            novo = {
                "Data": datetime.now().strftime("%d/%m %H:%M"),
                "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, 
                "Momento": momento, "Glicemia_Pos": 0
            }
            df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
            df_historico.to_csv("dados_glicemia.csv", index=False)
            st.success(f"Dose calculada: {dose} U. Salvo!")
            st.balloons()

    elif menu == "📌 Pendentes (2h Após)":
        st.header("Glicemia Pós-Prandial")
        pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
        if not pendentes.empty:
            for idx, row in pendentes.iterrows():
                with st.expander(f"Refeição: {row['Momento']} - {row['Data']}"):
                    val = st.number_input(f"Glicemia 2h após", key=f"p_{idx}")
                    if st.button("Confirmar Medição", key=f"b_{idx}"):
                        df_historico.at[idx, "Glicemia_Pos"] = val
                        df_historico.to_csv("dados_glicemia.csv", index=False)
                        st.rerun()
        else:
            st.info("Nenhuma medição pendente.")

    elif menu == "📜 Histórico Completo":
        st.header("📜 Histórico de Registros")
        st.dataframe(df_historico, use_container_width=True)
        if not df_historico.empty:
            pdf_data = gerar_pdf(df_historico)
            st.download_button("📥 Baixar Relatório PDF", data=pdf_data, file_name="relatorio.pdf", mime="application/pdf")

    elif menu == "⚙️ Perfil e Temas":
        st.header("👤 Perfil e Customização")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Nome da Criança", "Sua Filha")
            st.number_input("Idade", 7)
        with c2:
            st.session_state.cor_primaria = st.color_picker("Cor dos Botões", st.session_state.cor_primaria)
            st.session_state.cor_fundo = st.color_picker("Cor do Fundo", st.session_state.cor_fundo)
        if st.button("Aplicar Alterações"):
            st.rerun()

    elif menu == "🍎 Tabela de Alimentos":
        st.header("🍎 Gerenciar Tabela")
        st.dataframe(df_alimentos, use_container_width=True)
        with st.expander("➕ Adicionar Novo Alimento"):
            n_n = st.text_input("Nome")
            n_c = st.number_input("Carbo (g)", min_value=0)
            n_u = st.text_input("Unidade (Ex: 1 concha)")
            if st.button("Salvar na Lista"):
                novo_al = {"Alimento": n_n, "Carboidratos por Porção": n_c, "Unidade": n_u}
                df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo_al])], ignore_index=True)
                df_alimentos.to_csv("alimentos.csv", index=False)
                st.success("Adicionado!")
                st.rerun()