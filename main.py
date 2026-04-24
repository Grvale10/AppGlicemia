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