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
    pdf.cell(190, 10, "Relatorio Mensal de Glicemia", ln=True, align='C')
    pdf.ln(5)
    if not df.empty:
        media = round(df['Glicemia_Pre'].mean(), 1)
        pdf.set_font("Arial", size=12)
        pdf.cell(190, 8, f"Media de Glicemia: {media} mg/dL", ln=True)
        pdf.ln(10)
    
    pdf.set_font("Arial", "B", 9)
    # Cabeçalho simples para evitar erros de caractere
    pdf.cell(40, 8, "Data", 1)
    pdf.cell(30, 8, "Glic. Pre", 1)
    pdf.cell(30, 8, "Carbo", 1)
    pdf.cell(30, 8, "Dose", 1)
    pdf.cell(30, 8, "Glic. Pos", 1)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        pdf.cell(40, 8, str(row['Data']), 1)
        pdf.cell(30, 8, str(row['Glicemia_Pre']), 1)
        pdf.cell(30, 8, str(row['Carbos']), 1)
        pdf.cell(30, 8, str(row['Dose']), 1)
        pdf.cell(30, 8, str(row['Glicemia_Pos']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- CARREGAR E PADRONIZAR DADOS ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

# Histórico
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

# Alimentos com tratamento de erro de coluna (KeyError)
try:
    df_alimentos = pd.read_csv("alimentos.csv")
    # Padroniza o nome da coluna para 'Carbos' independente de como foi salva
    if "Carboidratos por Porção" in df_alimentos.columns:
        df_alimentos = df_alimentos.rename(columns={"Carboidratos por Porção": "Carbos"})
    elif "Carboidratos" in df_alimentos.columns:
        df_alimentos = df_alimentos.rename(columns={"Carboidratos": "Carbos"})
except:
    df_alimentos = pd.DataFrame({
        "Alimento": ["Pão Francês", "Arroz Branco (colher)", "Feijão (concha)"],
        "Carbos": [28, 15, 14]
    })

# --- INTERFACE ---
with st.sidebar:
    st.title("📟 BioCare Kids")
    aba = st.radio("Ir para:", ["🏠 Registro", "📊 Histórico", "🍎 Alimentos"])

if aba == "🏠 Registro":
    st.header("📝 Novo Registro")
    
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual", min_value=20, value=110)
        if g_pre < 70:
            st.error("⚠️ HIPOGLICEMIA! Ofereça açúcar imediatamente.")
        elif g_pre > 250:
            st.warning("⚠️ Glicemia Elevada.")

    with col2:
        lista_nomes = df_alimentos["Alimento"].tolist()
        alimento_sel = st.selectbox("Alimento", lista_nomes)
        
        # Busca o carbo de forma segura
        carbo_unitario = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0, step=0.5)
        carbo_total = round(float(carbo_unitario) * qtd, 1)
        st.info(f"Total: **{carbo_total}g** de carboidratos")

    momento = st.selectbox("Refeição", ["Café", "Almoço", "Lanche", "Jantar", "Ceia"])

    if st.button("Salvar Registro"):
        dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
        novo = {
            "Data": datetime.now().strftime("%d/%m %H:%M"),
            "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, 
            "Momento": momento, "Glicemia_Pos": 0
        }
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose: {dose} U. Salvo!")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 Baixar PDF Mensal", data=gerar_pdf(df_historico), file_name="glicemia.pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Tabela de Alimentos")
    # Editor de dados para facilitar a vida
    df_alimentos = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Confirmar Alterações"):
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Tabela atualizada!")