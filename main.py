import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# --- FUNÇÕES DE APOIO ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Glicemia - BioCare Kids", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for i, row in df.iterrows():
        texto = f"{row['Data']} | {row['Momento']} | Glicemia: {row['Glicemia_Pre']} | Dose: {row['Dose']} U"
        pdf.cell(190, 8, texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAÇÃO VISUAL E TEMAS ---
st.set_page_config(page_title="BioCare Kids Pro", layout="wide")

TEMAS = {
    "Padrão BioCare (Vermelho)": {"primaria": "#FF4B4B", "fundo": "#FFFFFF", "texto": "#31333F"},
    "Azul Oceano": {"primaria": "#007BFF", "fundo": "#F0F2F6", "texto": "#1A1A1A"},
    "Verde Saúde": {"primaria": "#28A745", "fundo": "#F8FFF9", "texto": "#1E3924"},
    "Modo Noturno": {"primaria": "#BB86FC", "fundo": "#0E1117", "texto": "#FAFAFA"},
    "Rosa Suave": {"primaria": "#E83E8C", "fundo": "#FFF5F8", "texto": "#3D0A1B"}
}

if "tema_selecionado" not in st.session_state:
    st.session_state.tema_selecionado = "Padrão BioCare (Vermelho)"

cores = TEMAS[st.session_state.tema_selecionado]

# --- CSS REVISADO (FOCO APENAS NOS CÍRCULOS E DETALHES) ---
st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: {cores['fundo']}; color: {cores['texto']}; }}
    
    /* Botões: Apenas o fundo e o efeito de clique */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {cores['primaria']};
        color: white; border: none; font-weight: bold; transition: 0.3s;
    }}
    .stButton>button:hover {{ opacity: 0.8; transform: translateY(-2px); }}

    /* CORREÇÃO DOS CÍRCULOS (RADIO BUTTONS) */
    /* Isso garante que APENAS a bolinha interna mude de cor quando selecionada */
    div[data-testid="stRadio"] input[type="radio"]:checked + div {{
        background-color: {cores['primaria']} !important;
    }}
    
    /* Cor da borda da bolinha */
    div[data-testid="stRadio"] div[role="radiogroup"] div[data-baseweb="radio"] > div:first-child {{
        border-color: {cores['primaria']} !important;
    }}

    /* Cor da linha das Abas (Tabs) */
    button[data-baseweb="tab"]:hover {{ color: {cores['primaria']} !important; }}
    button[aria-selected="true"] {{ 
        color: {cores['primaria']} !important;
        border-bottom-color: {cores['primaria']} !important;
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
    df_alimentos = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz"], "Carboidratos por Porção": [28, 25], "Unidade": ["un", "colher"]})

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📟 BioCare Kids")
    aba_config = st.radio("Navegar para:", ["🏠 Home", "📌 Pendentes", "📜 Histórico", "⚙️ Perfil & Temas", "🍎 Alimentos"])
    st.divider()

# --- LÓGICA DE TELAS ---
if aba_config == "🏠 Home":
    st.title("📊 Painel de Controle")
    tab1, tab2 = st.tabs(["📝 Registrar", "📜 Histórico"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            g_pre = st.number_input("Glicemia Antes", value=110)
            alimento = st.selectbox("Escolha o Alimento", df_alimentos["Alimento"].tolist())
            info = df_alimentos[df_alimentos["Alimento"] == alimento].iloc[0]
        with col2:
            porcoes = st.number_input("Quantidade", min_value=0.1, value=1.0)
            momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche"])
            carbo_total = info['Carboidratos por Porção'] * porcoes
        
        if st.button("Calcular e Salvar Registro"):
            dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
            novo_dado = {
                "Data": datetime.now().strftime("%d/%m %H:%M"),
                "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, 
                "Momento": momento, "Glicemia_Pos": 0
            }
            df_historico = pd.concat([df_historico, pd.DataFrame([novo_dado])], ignore_index=True)
            df_historico.to_csv("dados_glicemia.csv", index=False)
            st.success(f"Dose sugerida: {dose} U. Salvo!")

    with tab2:
        st.dataframe(df_historico, use_container_width=True)
        if not df_historico.empty:
            st.download_button("📥 Baixar PDF", data=gerar_pdf(df_historico), file_name="glicemia.pdf")

elif aba_config == "📌 Pendentes":
    st.header("📌 Glicemia 2h Após")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Momento']} - {row['Data']}"):
                v_pos = st.number_input("Valor após 2h", key=f"p_{idx}")
                if st.button("Confirmar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()
    else:
        st.info("Nada pendente.")

elif aba_config == "👤 Perfil & Temas":
    st.header("👤 Perfil e Aparência")
    st.subheader("🎨 Escolha um Tema")
    escolha = st.selectbox("Selecione uma paleta de cores:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(st.session_state.tema_selecionado))
    if escolha != st.session_state.tema_selecionado:
        st.session_state.tema_selecionado = escolha
        st.rerun()

elif aba_config == "🍎 Alimentos":
    st.header("🍎 Gestão de Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)
    with st.expander("➕ Adicionar Novo"):
        n = st.text_input("Nome")
        c = st.number_input("Carbo (g)", min_value=0)
        u = st.text_input("Unidade")
        if st.button("Salvar"):
            novo = {"Alimento": n, "Carboidratos por Porção": c, "Unidade": u}
            df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo])], ignore_index=True)
            df_alimentos.to_csv("alimentos.csv", index=False)
            st.success("Adicionado!")
            st.rerun()