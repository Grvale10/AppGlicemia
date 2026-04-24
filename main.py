import streamlit as st
import pandas as pd
from st_google_auth import add_auth
from fpdf import FPDF
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BioCare Kids - Gestão Familiar", layout="wide")

# --- FUNÇÕES INTERNAS (CÁLCULOS E PDF) ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Glicemia e Insulina", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for i, row in df.iterrows():
        texto = f"{row['Data']} | {row['Momento']} | Glicemia: {row['Glicemia_Pre']} | Dose: {row['Dose']} U"
        pdf.cell(190, 8, texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- SISTEMA DE LOGIN DO GOOGLE ---
# Isso lê automaticamente as chaves que você colocou nos Secrets do Streamlit
add_auth()

if not st.session_state.get("connected"):
    st.title("🔐 Acesso Restrito")
    st.warning("Por favor, faça login com sua conta Google para acessar os dados da família.")
    st.stop()

# --- SE CHEGOU AQUI, ESTÁ LOGADO ---
user_info = st.session_state.get("user_info")

# Inicializar Temas e Dados
if "cor_primaria" not in st.session_state:
    st.session_state.cor_primaria = "#007BFF"

# Aplicar CSS
st.markdown(f"""
    <style>
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(45deg, {st.session_state.cor_primaria}, #77aaff);
        color: white; border: none; font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# Carregar Arquivos
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Manual"], "Carboidratos por Porção": [0], "Unidade": ["g"]})

# --- INTERFACE ---
with st.sidebar:
    st.image(user_info.get("picture"), width=70)
    st.title(f"Olá, {user_info.get('given_name')}")
    menu = st.radio("Menu", ["🏠 Painel", "📌 Pendentes", "📜 Histórico", "⚙️ Perfil", "🍎 Alimentos"])
    st.divider()
    if st.button("Sair"):
        st.session_state.connected = False
        st.rerun()

if menu == "🏠 Painel":
    st.header("📝 Novo Registro")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Antes", value=110)
        selecionado = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        dado_ali = df_alimentos[df_alimentos["Alimento"] == selecionado].iloc[0]
    with col2:
        qtd = st.number_input("Porções", min_value=0.1, value=1.0)
        mom = st.selectbox("Refeição", ["Café", "Almoço", "Lanche", "Jantar"])
        carbo_t = dado_ali['Carboidratos por Porção'] * qtd

    if st.button("Salvar Registro"):
        dose = calcular_insulina(g_pre, 100, 50, carbo_t, 15)
        novo = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": carbo_t, "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose: {dose} U. Salvo com sucesso!")
        st.balloons()

elif menu == "📌 Pendentes":
    st.header("📌 Glicemia 2h Após")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Momento']} em {row['Data']}"):
                v = st.number_input("Valor da Glicemia", key=f"v_{idx}")
                if st.button("Confirmar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()
    else:
        st.info("Nada pendente.")

elif menu == "📜 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        pdf_bytes = gerar_pdf(df_historico)
        st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name="glicemia.pdf")

elif menu == "⚙️ Perfil":
    st.header("⚙️ Personalização")
    st.session_state.cor_primaria = st.color_picker("Cor dos Botões", st.session_state.cor_primaria)
    if st.button("Aplicar Tema"):
        st.rerun()

elif menu == "🍎 Alimentos":
    st.header("🍎 Cadastrar Alimentos")
    n = st.text_input("Nome")
    c = st.number_input("Carbo (g)", min_value=0)
    u = st.text_input("Unidade (Ex: 1 fatia)")
    if st.button("Salvar Alimento"):
        novo_a = {"Alimento": n, "Carboidratos por Porção": c, "Unidade": u}
        df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo_a])], ignore_index=True)
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Adicionado!")