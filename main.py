import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- FUNÇÕES DE APOIO ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    # Regra de correção + Regra de carboidratos
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatório Mensal de Glicemia", ln=True, align='C')
    pdf.ln(5)
    
    # Resumo Estatístico
    if not df.empty:
        media = round(df['Glicemia_Pre'].mean(), 1)
        total_carbo = df['Carbos'].sum()
        pdf.set_font("Arial", size=12)
        pdf.cell(190, 8, f"Média de Glicemia Pré: {media} mg/dL", ln=True)
        pdf.cell(190, 8, f"Total de Carboidratos consumidos: {total_carbo}g", ln=True)
        pdf.ln(10)

    # Tabela
    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 8, "Data/Hora", 1)
    pdf.cell(30, 8, "Momento", 1)
    pdf.cell(30, 8, "Glic. Pré", 1)
    pdf.cell(30, 8, "Carbos(g)", 1)
    pdf.cell(30, 8, "Dose (U)", 1)
    pdf.cell(30, 8, "Glic. Pós", 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(35, 8, str(row['Data']), 1)
        pdf.cell(30, 8, str(row['Momento']), 1)
        pdf.cell(30, 8, str(row['Glicemia_Pre']), 1)
        pdf.cell(30, 8, str(row['Carbos']), 1)
        pdf.cell(30, 8, str(row['Dose']), 1)
        pdf.cell(30, 8, str(row['Glicemia_Pos']), 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAÇÃO E DADOS ---
st.set_page_config(page_title="BioCare Kids", layout="wide")

try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
    if df_alimentos.empty: raise Exception
except:
    df_alimentos = pd.DataFrame({
        "Alimento": ["Pão Francês", "Arroz Branco (colher)", "Feijão (concha)", "Maçã (un)"],
        "Carbos": [28, 15, 14, 15]
    })

# --- INTERFACE ---
with st.sidebar:
    st.title("📟 BioCare Kids")
    aba = st.radio("Ir para:", ["🏠 Registro", "📊 Histórico & PDF", "🍎 Lista Alimentos"])

if aba == "🏠 Registro":
    st.header("📝 Novo Registro")
    
    col1, col2 = st.columns(2)
    with col1:
        g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, max_value=600, value=110)
        
        # --- ALERTA DE HIPOGLICEMIA ---
        if g_pre < 70:
            st.error("⚠️ ALERTA: HIPOGLICEMIA! Ofereça 15g de carboidrato simples imediatamente.")
        elif g_pre > 250:
            st.warning("⚠️ Atenção: Glicemia Elevada.")

    with col2:
        alimento_sel = st.selectbox("Alimento consumido", df_alimentos["Alimento"].tolist())
        carbo_unitario = df_alimentos[df_alimentos["Alimento"] == alimento_sel]["Carbos"].values[0]
        quantidade = st.number_input("Quantidade (porções/un)", min_value=0.1, value=1.0, step=0.5)
        
        # --- CÁLCULO AUTOMÁTICO ---
        carbo_total = round(carbo_unitario * quantidade, 1)
        st.info(f"Carboidratos Totais: **{carbo_total}g**")

    momento = st.selectbox("Refeição", ["Café da Manhã", "Almoço", "Lanche", "Jantar", "Ceia"])

    if st.button("Calcular Insulina e Salvar"):
        # Usando valores padrão: Meta 100, Sensibilidade 50, Relação Carbo 15
        dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
        
        novo = {
            "Data": datetime.now().strftime("%d/%m %H:%M"),
            "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, 
            "Momento": momento, "Glicemia_Pos": 0
        }
        df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success(f"Dose Recomendada: {dose} Unidades. Registro salvo com sucesso!")

elif aba == "📊 Histórico & PDF":
    st.header("📜 Histórico de Registros")
    
    # Filtro rápido
    if not df_historico.empty:
        st.dataframe(df_historico.sort_index(ascending=False), use_container_width=True)
        
        st.divider()
        st.subheader("📥 Exportação Médica")
        st.write("Gere o relatório completo para enviar ao endocrinologista.")
        btn_pdf = st.download_button(
            label="Gerar Relatório em PDF",
            data=gerar_pdf(df_historico),
            file_name=f"relatorio_glicemia_{datetime.now().strftime('%m_%Y')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Ainda não há registros salvos.")

elif aba == "🍎 Lista Alimentos":
    st.header("🍎 Minha Tabela de Carboidratos")
    st.write("Adicione ou edite os alimentos que ela mais consome.")
    
    edit_df = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações na Tabela"):
        edit_df.to_csv("alimentos.csv", index=False)
        st.success("Tabela de alimentos atualizada!")