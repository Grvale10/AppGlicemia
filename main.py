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

# Dicionário de Temas Profissionais
TEMAS = {
    "Padrão BioCare (Vermelho)": {"primaria": "#FF4B4B", "fundo": "#FFFFFF", "texto": "#31333F"},
    "Azul Oceano": {"primaria": "#007BFF", "fundo": "#F0F2F6", "texto": "#1A1A1A"},
    "Verde Saúde": {"primaria": "#28A745", "fundo": "#F8FFF9", "texto": "#1E3924"},
    "Modo Noturno": {"primaria": "#BB86FC", "fundo": "#0E1117", "texto": "#FAFAFA"},
    "Rosa Suave": {"primaria": "#E83E8C", "fundo": "#FFF5F8", "texto": "#3D0A1B"}
}

if "tema_selecionado" not in st.session_state:
    st.session_state.tema_selecionado = "Padrão BioCare (Vermelho)"

# Atalhos para facilitar o uso no código
cores = TEMAS[st.session_state.tema_selecionado]

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {cores['fundo']};
        color: {cores['texto']};
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(45deg, {cores['primaria']}, #7a7a7a33);
        color: white; border: none; font-weight: bold; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 4px 15px {cores['primaria']}44; }}
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
    aba_config = st.radio("Navegar para:", ["🏠 Home", "📌 Pendentes", "👤 Perfil & Temas", "🍎 Alimentos"])
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
            df_historico.to_csv("dados_glicemia