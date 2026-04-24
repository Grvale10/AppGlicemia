import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

st.set_page_config(page_title="BioCare Kids", layout="wide")

# --- 2. FUNÇÕES TÉCNICAS ---
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

# --- 3. DESIGN CSS (PRECISÃO PARA O MENU) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* Remove rótulos chatos do menu lateral */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{ display: none !important; }}

    /* Botões do Menu Lateral Centrais */
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        background-color: #F3F4F6 !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border: 1px solid transparent !important;
    }}
    
    /* Texto dos botões */
    div[data-testid="stRadio"] div[role="radiogroup"] label p {{
        color: #1F2937 !important;
        font-size: 16px !important;
        margin: 0px !important;
    }}

    /* Esconde círculo do rádio */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{ display: none !important; }}

    /* Botão selecionado */
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important; font-weight: bold !important;
    }}

    /* Botão Salvar */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CARGA DE DADOS COM LIMPEZA DE COLUNAS ---
def iniciar_banco():
    # Carregar Alimentos
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        # Limpa nomes de colunas (tira espaços extras)
        df_a.columns = df_a.columns.str.strip()
        if "Alimento" not in df_a.columns or "Carbos" not in df_a.columns:
            df_a = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz"], "Carbos": [28.0, 15.0]})
    else:
        df_a = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz"], "Carbos": [28.0, 15.0]})
    
    # Carregar Histórico
    if os.path.exists("dados_glicemia.csv"):
        df_h = pd.read_csv("dados_glicemia.csv")
        df_h.columns = df_h.columns.str.strip()
    else:
        df_h = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    
    return df_a, df_h

df_alimentos, df_historico = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 24px; color: #1F2937; margin-bottom: 25px;'>Menu</h1>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("📝 Registrar Refeição")
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110, help="Valor antes de comer.")
        momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche"])
    with col2:
        alimento_sel = st.selectbox("Alimento Principal", df_alimentos["Alimento"].tolist())
        
        # Busca ultra-segura para evitar o KeyError
        try:
            carbo_val = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        except:
            carbo_val = 0.0
            
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0, help="Quantidade do alimento escolhido.")
        total_c = round(float(carbo_val) * qtd, 1)
        st.info(f"Carboidratos: {total_c}g")

    if st.button("Calcular e Salvar"):
        dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
        novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia_Pre": g_pre, "Carbos": total_c, "Dose": dose, "Momento": momento, "Glicemia_Pos": 0}])
        df_historico = pd.concat([df_historico, novo], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose sugerida: {dose} U.")

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós (2h)")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Momento']} - {row['Data']}"):
                v_pos = st.number_input("Valor 2h após", key=f"p_{idx}")
                if st.button("Salvar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()
    else:
        st.info("Nada pendente.")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 PDF", data=gerar_pdf(df_historico), file_name="relatorio.pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    # Mostra a tabela para edição e garante que ao salvar as colunas fiquem certas
    df_novo = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações"):
        df_novo.to_csv("alimentos.csv", index=False)
        st.success("Tabela salva!")

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    with st.expander("🎨 Aparência (Submenu Temas)"):
        c1, c2 = st.columns(2)
        with c1: st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        with c2: st.session_state.cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()