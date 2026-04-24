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

# --- CONFIGURAÇÃO DE TEMA E DADOS ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#FFFFFF"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#FF4B4B"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    .stButton>button {{
        background-color: {st.session_state.cor_botao} !important;
        color: white !important;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

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
    st.title("📟 BioCare Kids")
    aba = st.radio("Navegar para:", ["🏠 Registro", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"])

# --- LÓGICA DAS ABAS ---

if aba == "🏠 Registro":
    st.header("📝 Novo Registro")
    col1, col2 = st.columns(2)
    with col1:
        # Adicionado o parâmetro 'help' para as explicações
        g_pre = st.number_input(
            "Glicemia Atual", 
            min_value=20, 
            value=110,
            help="Medida em mg/dL (miligramas por decilitro). Indica a concentração de glicose no sangue antes desta refeição."
        )
        if g_pre < 70: st.error("⚠️ HIPOGLICEMIA!")
    
    with col2:
        alimento_sel = st.selectbox(
            "Alimento", 
            df_alimentos["Alimento"].tolist(),
            help="Selecione o alimento principal. O sistema buscará automaticamente o valor de carboidratos cadastrado."
        )
        carbo_unit = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        qtd = st.number_input(
            "Quantidade", 
            min_value=0.1, 
            value=1.0,
            help="Multiplicador baseado na unidade (ex: 2 colheres, 1.5 pães)."
        )
        carbo_total = round(float(carbo_unit) * qtd, 1)
        st.info(f"Total: {carbo_total}g de Carbo")

    if st.button("Salvar Registro"):
        dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
        novo = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, "Momento": "Refeição", "Glicemia_Pos": 0}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose: {dose} U. Salvo!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button(
            "📥 Baixar PDF", 
            data=gerar_pdf(df_historico), 
            file_name="glicemia.pdf",
            help="Gera um arquivo PDF com todos os registros para enviar ao médico."
        )

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    st.info("💡 Dica: Clique duas vezes em uma célula para editar o valor do carboidrato.")
    df_alimentos = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Tabela"):
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Salvo!")

elif aba == "👤 Perfil":
    st.header("👤 Perfil e Customização")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        meta_glic = st.number_input(
            "Meta Glicêmica", 
            value=100,
            help="O valor de glicemia que o médico estabeleceu como ideal (objetivo)."
        )
    with col_p2:
        sensib = st.number_input(
            "Fator de Sensibilidade", 
            value=50,
            help="Quanto 1 unidade de insulina baixa a glicemia no sangue (ex: 1U baixa 50 mg/dL)."
        )
    
    st.divider()
    st.subheader("🎨 Cores do Aplicativo")
    c1, c2 = st.columns(2)
    with c1: nova_cor_fundo = st.color_picker("Cor do Fundo", st.session_state.cor_fundo)
    with c2: nova_cor_botao = st.color_picker("Cor dos Botões", st.session_state.cor_botao)
    
    if st.button("Aplicar Novas Cores"):
        st.session_state.cor_fundo = nova_cor_fundo
        st.session_state.cor_botao = nova_cor_botao
        st.rerun()