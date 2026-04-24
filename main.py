import streamlit as st
from carbeglice import calcular_insulina, verificar_alerta

st.set_page_config(page_title="Controle de Glicemia Familiar", layout="centered")

st.title("📊 Controle de Glicemia")
st.subheader("Monitoramento da Saúde da Nossa Filha")

# Sidebar para configurações que não mudam sempre
st.sidebar.header("Configurações Médicas")
meta = st.sidebar.number_input("Meta de Glicemia (mg/dL)", value=100)
sensibilidade = st.sidebar.number_input("Fator de Sensibilidade", value=50)
relacao_carb = st.sidebar.number_input("Relação Carboidrato (1U para Xg)", value=15)

# Área principal
col1, col2 = st.columns(2)

with col1:
    glicemia = st.number_input("Glicemia Atual (mg/dL)", min_value=0, value=110)
    alerta = verificar_alerta(glicemia)
    if "ALERTA" in alerta:
        st.error(alerta)
    else:
        st.success(alerta)

with col2:
    carbos = st.number_input("Carboidratos da Refeição (g)", min_value=0, value=0)

if st.button("Calcular Dose de Insulina"):
    dose = calcular_insulina(glicemia, meta, sensibilidade, carbos, relacao_carb)
    st.metric(label="Dose Sugerida", value=f"{dose} Unidades")
    st.info("Sempre valide a dose com a prescrição médica antes de aplicar.")

# Espaço para anotações
notas = st.text_area("Anotações da Refeição (Ex: O que comeu, sintomas)")
if st.button("Salvar Log"):
    st.toast("Dados salvos localmente (Simulação)")
    import streamlit as st
import pandas as pd
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

st.set_page_config(page_title="BioCare Kids", layout="wide")

# Inicializar Banco de Dados simples
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia", "Carbos", "Dose", "Momento"])

# --- BARRA LATERAL (PERFIL) ---
st.sidebar.header("👶 Perfil da Criança")
nome = st.sidebar.text_input("Nome", "Minha Filha")
idade = st.sidebar.number_input("Idade", value=7)
peso = st.sidebar.number_input("Peso (kg)", value=25.0)

st.sidebar.divider()
st.sidebar.header("⚙️ Ajustes de Faixa")
f_baixa = st.sidebar.slider("Limite Hipoglicemia", 50, 90, 70)
f_alta = st.sidebar.slider("Limite Hiperglicemia", 140, 250, 180)

# --- CORPO DO APP ---
aba1, aba2, aba3 = st.tabs(["📝 Nova Refeição", "📜 Histórico", "📊 Gráficos"])

with aba1:
    st.header("Registrar Dados")
    col1, col2 = st.columns(2)
    
    with col1:
        glicemia_pre = st.number_input("Glicemia Antes (mg/dL)", min_value=0, value=100)
        momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Madrugada"])
    
    with col2:
        carbos = st.number_input("Total de Carboidratos (g)", min_value=0)
        # Configurações médicas rápidas
        meta = 100
        sensi = 50
        rel_c = 15

    if st.button("Calcular e Salvar"):
        dose = calcular_insulina(glicemia_pre, meta, sensi, carbos, rel_c)
        status, cor = definir_status(glicemia_pre, f_baixa, f_alta)
        
        st.subheader(f"Dose Recomendada: {dose} U")
        st.markdown(f"Status: :{cor}[{status}]")
        
        # Salvar no arquivo
        novo_dado = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia": glicemia_pre, "Carbos": carbos, "Dose": dose, "Momento": momento}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo_dado])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success("Dados salvos com sucesso!")

with aba2:
    st.header("Histórico de Registros")
    st.dataframe(df_historico, use_container_width=True)
    
    if not df_historico.empty:
        pdf_data = gerar_pdf(df_historico)
        st.download_button(label="📥 Baixar Relatório PDF", data=pdf_data, file_name="relatorio_glicemia.pdf", mime="application/pdf")

with aba3:
    st.header("Evolução")
    if not df_historico.empty:
        st.line_chart(df_historico.set_index("Data")["Glicemia"])
    else:
        st.info("Ainda não há dados para mostrar o gráfico.")