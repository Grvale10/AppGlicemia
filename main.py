import streamlit as st
import pandas as pd
from carbeglice import calcular_insulina, definir_status, gerar_pdf
from datetime import datetime, timedelta

st.set_page_config(page_title="BioCare Kids", layout="wide")

# Inicializar Bancos de Dados
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
    # Garantir que a coluna Glicemia_Pos existe
    if "Glicemia_Pos" not in df_historico.columns:
        df_historico["Glicemia_Pos"] = 0
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Manual"], "Carboidratos por Porção": [0], "Unidade": ["g"]})

# --- BARRA LATERAL ---
st.sidebar.header("👶 Perfil da Criança")
st.sidebar.write(f"**Peso:** {st.sidebar.number_input('Peso (kg)', value=25.0)}kg")

# --- CORPO DO APP ---
aba1, aba_pendente, aba2, aba3 = st.tabs(["📝 Nova Refeição", "📌 Pendente (2h Após)", "📜 Histórico Completo", "➕ Alimentos"])

with aba1:
    st.header("Registrar Refeição")
    col1, col2 = st.columns(2)
    with col1:
        glicemia_pre = st.number_input("Glicemia Antes (mg/dL)", min_value=0, value=110)
        alimento_selecionado = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        info = df_alimentos[df_alimentos["Alimento"] == alimento_selecionado].iloc[0]
        porcoes = st.number_input("Quantas porções?", min_value=0.1, value=1.0, step=0.1)
        carbos_totais = info['Carboidratos por Porção'] * porcoes
    with col2:
        momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche"])
        meta, sensi, rel_c = 100, 50, 15

    if st.button("Calcular e Salvar"):
        dose = calcular_insulina(glicemia_pre, meta, sensi, carbos_totais, rel_c)
        status, cor = definir_status(glicemia_pre, 70, 180)
        st.subheader(f"Dose: {dose} U")
        
        novo_dado = {
            "Data": datetime.now().strftime("%d/%m %H:%M"),
            "Glicemia_Pre": glicemia_pre,
            "Carbos": carbos_totais,
            "Dose": dose,
            "Momento": momento,
            "Glicemia_Pos": 0  # Começa zerado
        }
        df_historico = pd.concat([df_historico, pd.DataFrame([novo_dado])], ignore_index=True)
        df_historico.to_csv("dados_glicemia.csv", index=False)
        st.success("Registrado! Não esqueça de medir daqui a 2 horas.")

with aba_pendente:
    st.header("Registrar Glicemia de 2h Após")
    # Filtrar registros onde a Glicemia_Pos ainda é 0
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"Refeição: {row['Momento']} às {row['Data']}"):
                col_a, col_b = st.columns(2)
                valor_pos = col_a.number_input(f"Valor 2h após para {row['Data']}", key=f"input_{idx}")
                if col_b.button("Salvar Medição", key=f"btn_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = valor_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()
    else:
        st.success("Tudo em dia! Nenhum registro pendente.")

with aba2:
    st.header("Histórico Completo")
    # Mostrar a tabela com a comparação
    st.dataframe(df_historico, use_container_width=True)
    
    if not df_historico.empty:
        # Gráfico comparativo
        st.subheader("Gráfico Pré vs Pós")
        chart_data = df_historico[df_historico["Glicemia_Pos"] > 0]
        if not chart_data.empty:
            st.line_chart(chart_data.set_index("Data")[["Glicemia_Pre", "Glicemia_Pos"]])

with aba3:
    # (Mantém o código de adicionar alimentos anterior)
    st.header("➕ Adicionar Novo Alimento")
    n_nome = st.text_input("Nome")
    n_carbo = st.number_input("Carbo (g)", min_value=0)
    n_un = st.text_input("Unidade (Ex: 1 fatia)")
    if st.button("Salvar Alimento"):
        novo_al = {"Alimento": n_nome, "Carboidratos por Porção": n_carbo, "Unidade": n_un}
        df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo_al])], ignore_index=True)
        df_alimentos.to_csv("alimentos.csv", index=False)
        st.success("Alimento salvo!")