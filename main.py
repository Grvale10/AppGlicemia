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
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        texto = f"{row['Data']} | Glic: {row['Glicemia_Pre']} | Dose: {row['Dose']} U"
        pdf.cell(190, 8, texto.encode('latin-1', 'replace').decode('latin-1'), ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- ESTADO DA SESSÃO (CORES) ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- CONFIGURAÇÃO E DESIGN MODERNO ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* Botões Modernos Centrais */
    .stButton>button {{
        width: 100%;
        border-radius: 12px;
        height: 3.2em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px {st.session_state.cor_botao}44;
        transition: all 0.3s ease;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 18px {st.session_state.cor_botao}66;
    }}

    /* Barra Lateral */
    section[data-testid="stSidebar"] {{
        background-color: white !important;
        border-right: 1px solid #E5E7EB;
    }}
    
    /* MENU LATERAL: ALINHAMENTO E TAMANHO IGUAL */
    div[data-testid="stRadio"] {{
        width: 100%;
    }}
    div[data-testid="stRadio"] > div {{
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }}
    div[data-testid="stRadio"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 0px !important; /* Ajuste no padding */
        margin-bottom: 8px;
        width: 100% !important; /* Força largura igual */
        display: flex !important;
        justify-content: center !important; /* Centraliza texto */
        align-items: center !important;
        cursor: pointer;
        border: 1px solid transparent;
    }}
    
    /* Esconde o círculo original do rádio */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] {{
        width: 100%;
        text-align: center;
    }}
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    /* Item Selecionado */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
        box-shadow: 0 4px 10px {st.session_state.cor_botao}44;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important;
        font-weight: bold;
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
    df_alimentos = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco"], "Carbos": [28, 15]})

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 24px; color: #1F2937; margin-bottom: 20px;'>Menu</h1>", unsafe_allow_html=True)
    aba = st.radio("Navegar", ["🏠 Início", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- CONTEÚDO ---
if aba == "🏠 Início":
    st.header("📝 Registrar")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110, help="Valor medido no glicômetro.")
    with col2:
        alimento_sel = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        carbo_unit = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        carbo_total = round(float(carbo_unit) * qtd, 1)
        st.info(f"Total: {carbo_total}g de Carboidratos")

    if st.button("Salvar Registro"):
        dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
        novo = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, "Momento": "Refeição", "Glicemia_Pos": 0}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose calculada: {dose} U")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 Exportar PDF", data=gerar_pdf(df_historico), file_name="glicemia.pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    df_alimentos = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Tabela"):
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Tabela Atualizada!")

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    
    with st.expander("🎨 Aparência e Temas"):
        c1, c2 = st.columns(2)
        with c1:
            nova_cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        with c2:
            nova_cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        
        if st.button("Aplicar Cores"):
            st.session_state.cor_fundo = nova_cor_fundo
            st.session_state.cor_botao = nova_cor_botao
            st.rerun()

    st.divider()
    st.subheader("Configurações")
    st.text_input("Nome da Criança", "Minha Filha")
    st.number_input("Idade", value=5)