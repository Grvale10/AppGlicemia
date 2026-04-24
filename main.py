import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- FUNÇÕES DE APOIO ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Glicemia", ln=True, align='C')
    pdf.ln(5)
    if not df.empty:
        media = round(df['Glicemia_Pre'].mean(), 1)
        pdf.set_font("Arial", size=12)
        pdf.cell(190, 8, f"Media de Glicemia: {media} mg/dL", ln=True)
        pdf.ln(10)
    
    pdf.set_font("Arial", "B", 9)
    cols = ["Data", "Glic. Pre", "Carbo", "Dose", "Momento"]
    for col in cols: pdf.cell(38, 8, col, 1)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        pdf.cell(38, 8, str(row['Data']), 1)
        pdf.cell(38, 8, str(row['Glicemia_Pre']), 1)
        pdf.cell(38, 8, str(row['Carbos']), 1)
        pdf.cell(38, 8, str(row['Dose']), 1)
        pdf.cell(38, 8, str(row['Momento']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAÇÃO E DESIGN MODERNO ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

st.markdown(f"""
    <style>
    /* Fundo e Fonte Principal */
    .stApp {{ 
        background-color: {st.session_state.cor_fundo};
        font-family: 'Inter', -apple-system, sans-serif;
    }}

    /* Botões Modernos (Estilo Mobile Pro) */
    .stButton>button {{
        width: 100%;
        border-radius: 14px;
        height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important;
        border: none !important;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px {st.session_state.cor_botao}44;
        transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px {st.session_state.cor_botao}66;
    }}

    /* Barra Lateral Moderna */
    section[data-testid="stSidebar"] {{
        background-color: white !important;
        border-right: 1px solid #E5E7EB;
    }}
    
    /* Customização dos Itens do Menu (Radio) */
    div[data-testid="stRadio"] > div {{
        gap: 8px;
    }}
    div[data-testid="stRadio"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        border: 1px solid transparent !important;
        transition: 0.2s;
        margin-bottom: 4px;
    }}
    div[data-testid="stRadio"] label:hover {{
        border-color: {st.session_state.cor_botao}88 !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child {{
        display: none !important; /* Esconde o círculo antigo pra parecer botão de menu */
    }}
    div[data-testid="stRadio"] input[type="radio"]:checked + div {{
        background-color: {st.session_state.cor_botao} !important;
        color: white !important;
    }}
    /* Cor do texto quando selecionado */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold;
    }}

    /* Estilização de Containers (Cards) */
    div[data-testid="stMetric"], .stTabs {{
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
    if "Carboidratos por Porção" in df_alimentos.columns:
        df_alimentos = df_alimentos.rename(columns={"Carboidratos por Porção": "Carbos"})
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz (colher)"], "Carbos": [28, 15]})

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1F2937;'>📟 BioCare</h2>", unsafe_allow_html=True)
    st.write("")
    aba = st.radio("MENU", ["🏠 Registro", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- CONTEÚDO ---

if aba == "🏠 Registro":
    st.markdown("### 📝 Novo Registro")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual", min_value=20, value=110, help="Medida em mg/dL.")
        if g_pre < 70: st.error("⚠️ HIPOGLICEMIA!")
    with col2:
        alimento_sel = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        carbo_unit = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        carbo_total = round(float(carbo_unit) * qtd, 1)
        st.info(f"Total: {carbo_total}g de Carbo")

    if st.button("Salvar Registro"):
        dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
        novo = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, "Momento": "Refeição", "Glicemia_Pos": 0}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose: {dose} U. Salvo!")

elif aba == "📊 Histórico":
    st.markdown("### 📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 Exportar PDF", data=gerar_pdf(df_historico), file_name="glicemia.pdf")

elif aba == "🍎 Alimentos":
    st.markdown("### 🍎 Tabela de Alimentos")
    df_alimentos = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Tabela"):
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Tabela Atualizada!")

elif aba == "👤 Perfil":
    st.markdown("### 👤 Perfil e Aparência")
    st.subheader("🎨 Estilo")
    c1, c2 = st.columns(2)
    with c1: st.session_state.cor_fundo = st.color_picker("Cor de Fundo", st.session_state.cor_fundo)
    with c2: st.session_state.cor_botao = st.color_picker("Cor Principal (Botões)", st.session_state.cor_botao)
    
    if st.button("Aplicar Mudanças"):
        st.rerun()