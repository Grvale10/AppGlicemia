import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

# --- 2. BANCO DE DADOS (ESTRUTURA 8.1 MODIFICADA) ---
def iniciar_banco():
    # Lista SBD Completa com nomes por extenso
    sbd = [
        {"Alimento": "Arroz Branco", "Carboidratos": 28.0, "Proteínas": 2.5, "Gorduras": 0.2, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Feijão Carioca", "Carboidratos": 14.0, "Proteínas": 5.0, "Gorduras": 0.5, "Unidade": "Concha (100g)"},
        {"Alimento": "Pão Francês", "Carboidratos": 25.0, "Proteínas": 4.0, "Gorduras": 1.5, "Unidade": "Unidade (50g)"},
        {"Alimento": "Peito de Frango", "Carboidratos": 0.0, "Proteínas": 31.0, "Gorduras": 3.6, "Unidade": "Filé médio (100g)"},
        {"Alimento": "Ovo Cozido", "Carboidratos": 0.6, "Proteínas": 6.3, "Gorduras": 5.3, "Unidade": "Unidade"},
        {"Alimento": "Macarrão Cozido", "Carboidratos": 30.0, "Proteínas": 5.8, "Gorduras": 0.9, "Unidade": "Pegador (100g)"},
        {"Alimento": "Tapioca (Goma)", "Carboidratos": 54.0, "Proteínas": 0.0, "Gorduras": 0.0, "Unidade": "100g"},
        {"Alimento": "Leite Integral", "Carboidratos": 10.0, "Proteínas": 6.8, "Gorduras": 6.0, "Unidade": "Copo (200ml)"},
        {"Alimento": "Banana Prata", "Carboidratos": 22.0, "Proteínas": 1.3, "Gorduras": 0.3, "Unidade": "Unidade média"},
        {"Alimento": "Cuscuz de Milho", "Carboidratos": 25.0, "Proteínas": 2.2, "Gorduras": 0.5, "Unidade": "Fatia (100g)"}
    ]
    
    # Força a atualização se o arquivo for antigo para evitar erros de colunas faltantes
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        if "Proteínas" not in df_a.columns:
            df_a = pd.DataFrame(sbd)
            df_a.to_csv("alimentos.csv", index=False)
    else:
        df_a = pd.DataFrame(sbd)
        df_a.to_csv("alimentos.csv", index=False)
        
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carboidratos", "Proteínas", "Gorduras", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 3. INTERFACE (ESTILO 8.1) ---
st.sidebar.title("🛡️ Glicemia Para Todos")
aba = st.sidebar.radio("Navegação", ["Início", "Pacientes", "Pendentes", "Histórico", "Alimentos"])

# --- ABA INÍCIO ---
if aba == "Início":
    st.header("🍽️ Registro de Refeição")
    if df_pacientes.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with col2: mom = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Ceia"])
        with col3: gpre = st.number_input("Glicemia Pré (mg/dL)", value=110)
        
        st.divider()
        
        c_ali, c_qtd = st.columns([3, 1])
        with c_ali:
            escolha = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
            row = df_alimentos.loc[df_alimentos["Alimento"] == escolha].iloc[0]
        with c_qtd:
            qtd = st.number_input(f"Qtd ({row['Unidade']})", min_value=0.1, value=1.0)
            
        if st.button("Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({
                "Alimento": escolha, "Qtd": qtd, "Unidade": row["Unidade"],
                "Carboidratos": round(row["Carboidratos"] * qtd, 1),
                "Proteínas": round(row["Proteínas"] * qtd, 1),
                "Gorduras": round(row["Gorduras"] * qtd, 1)
            })
            st.rerun()

        if st.session_state.sacola_refeicao:
            st.subheader("Prato Atual")
            for i, item in enumerate(st.session_state.sacola_refeicao):
                st.write(f"• {item['Alimento']} - {item['Qtd']} {item['Unidade']} (C: {item['Carboidratos']}g | P: {item['Proteínas']}g | G: {item['Gorduras']}g)")
            
            tc = sum(x["Carboidratos"] for x in st.session_state.sacola_refeicao)
            tp = sum(x["Proteínas"] for x in st.session_state.sacola_refeicao)
            tg = sum(x["Gorduras"] for x in st.session_state.sacola_refeicao)
            
            st.markdown(f"**Totais:** Carboidratos: **{tc}g** | Proteínas: **{tp}g** | Gorduras: **{tg}g**")
            
            if st.button("Salvar e Calcular"):
                # Cálculo simples (Glicemia - 100)/50 + (Carbo / 15)
                dose = round(max(0, (gpre - 100)/50) + (tc / 15), 1)
                novo_reg = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carboidratos": tc, "Proteínas": tp, "Gorduras": tg, "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo_reg], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []
                st.success(f"Dose sugerida: {dose} U")
                st.rerun()

# --- ABA PACIENTES (ESTILO 8.1) ---
elif aba == "Pacientes":
    st.header("👥 Pacientes")
    with st.form("form_pac"):
        nome = st.text_input("Nome")
        parentesco = st.selectbox("Parentesco", ["Filha", "Filho", "Cônjuge", "Outro"])
        if st.form_submit_button("Cadastrar"):
            if nome:
                new_p = pd.DataFrame([{"Nome": nome, "Parentesco": parentesco, "CPF": "", "Sangue": ""}])
                df_pacientes = pd.concat([df_pacientes, new_p], ignore_index=True)
                df_pacientes.to_csv("pacientes.csv", index=False)
                st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

# --- ABA PENDENTES (ESTILO 8.1) ---
elif aba == "Pendentes":
    st.header("📌 Glicemia Pós-Prandial")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    if pend.empty:
        st.success("Nada pendente.")
    else:
        for idx, r in pend.iterrows():
            with st.expander(f"{r['Paciente']} - {r['Momento']} ({r['Data']})"):
                v = st.number_input("Valor Pós", key=f"v_{idx}")
                if st.button("Salvar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()

# --- ABA HISTÓRICO (ESTILO 8.1) ---
elif aba == "Histórico":
    st.header("📊 Histórico")
    st.dataframe(df_historico, use_container_width=True)

# --- ABA ALIMENTOS (ESTILO 8.1) ---
elif aba == "Alimentos":
    st.header("🍎 Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)