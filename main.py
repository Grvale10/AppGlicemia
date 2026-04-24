import streamlit as st
import pandas as pd
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime

st.set_page_config(page_title="BioCare Kids", layout="wide")

# Inicializar Bancos de Dados
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia", "Carbos", "Dose", "Momento"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Manual"], "Carboidratos por Porção": [0], "Unidade": ["g"]})

# --- BARRA LATERAL ---
st.sidebar.header("👶 Perfil da Criança")
nome = st.sidebar.text_input("Nome", "Minha Filha")
peso = st.sidebar.number_input("Peso (kg)", value=25.0)

st.sidebar.divider()
st.sidebar.header("⚙️ Ajustes de Faixa")
f_baixa = st.sidebar.slider("Limite Hipoglicemia", 50, 90, 70)
f_alta = st.sidebar.slider("Limite Hiperglicemia", 140, 250, 180)

# --- CORPO DO APP ---
aba1, aba2, aba3 = st.tabs(["📝 Nova Refeição", "📜 Histórico", "🍎 Cadastrar Alimento"])

with aba1:
    st.header("Registrar Dados")
    col1, col2 = st.columns(2)
    
    with col1:
        glicemia_pre = st.number_input("Glicemia Antes (mg/dL)", min_value=0, value=110)
        
        # Seleção de Alimento da Tabela
        alimento_selecionado = st.selectbox("Selecione um Alimento da Lista", df_alimentos["Alimento"].tolist())
        info_alimento = df_alimentos[df_alimentos["Alimento"] == alimento_selecionado].iloc[0]
        
        st.info(f"Porção padrão: {info_alimento['Unidade']} ({info_alimento['Carboidratos por Porção']}g carbos)")
        quantas_porcoes = st.number_input("Quantas porções?", min_value=0.1, value=1.0, step=0.1)
        
        carbos_totais = info_alimento['Carboidratos por Porção'] * quantas_porcoes
        st.write(f"**Total de Carboidratos: {carbos_totais:.1f}g**")

    with col2:
        momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Madrugada"])
        # Ajustes Médicos (Depois podemos colocar isso na lateral também)
        meta = 100
        sensi = 50
        rel_c = 15

    if st.button("Calcular e Salvar"):
        dose = calcular_insulina(glicemia_pre, meta, sensi, carbos_totais, rel_c)
        status, cor = definir_status(glicemia_pre, f_baixa, f_alta)
        
        st.subheader(f"Dose Recomendada: {dose} U")
        st.markdown(f"Status: :{cor}[{status}]")
        
        novo_dado = {"Data": datetime.now().strftime("%d/%m %H:%M"), "Glicemia": glicemia_pre, "Carbos": carbos_totais, "Dose": dose, "Momento": momento}
        df_historico = pd.concat([df_historico, pd.DataFrame([novo_dado])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success("Dados salvos no histórico!")

with aba2:
    st.header("Histórico de Registros")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        pdf_data = gerar_pdf(df_historico)
        st.download_button("📥 Baixar Relatório PDF", data=pdf_data, file_name="relatorio.pdf", mime="application/pdf")

with aba3:
    st.header("➕ Adicionar Novo Alimento à Lista")
    novo_nome = st.text_input("Nome do Alimento")
    novo_carbo = st.number_input("Carboidratos (g) por porção", min_value=0)
    nova_unidade = st.text_input("Unidade (Ex: 1 concha, 100g, 1 unidade)")
    
    if st.button("Salvar Alimento"):
        novo_alimento = {"Alimento": novo_nome, "Carboidratos por Porção": novo_carbo, "Unidade": nova_unidade}
        df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo_alimento])], ignore_index=True)
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success(f"{novo_nome} adicionado! Atualize a página para ver na lista.")