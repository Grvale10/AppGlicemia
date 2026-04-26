import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES ---
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

# --- 2. BANCO DE DADOS (CARREGAMENTO SEGURO) ---
def carregar_dados():
    # Alimentos
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
    else:
        # Se não existir, cria a base técnica inicial
        dados_sbd = {
            "Alimento": ["Arroz Branco", "Feijão Carioca", "Pão Francês", "Peito de Frango", "Ovo Cozido"],
            "Carboidratos": [28.0, 14.0, 25.0, 0.0, 0.6],
            "Proteínas": [2.5, 5.0, 4.0, 31.0, 6.3],
            "Gorduras": [0.2, 0.5, 1.5, 3.6, 5.3],
            "Unidade": ["Escumadeira", "Concha", "Unidade", "100g", "Unidade"]
        }
        df_a = pd.DataFrame(dados_sbd)
        df_a.to_csv("alimentos.csv", index=False)

    # Pacientes
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    
    # Histórico (Glicemia)
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carboidratos", "Proteínas", "Gorduras", "Dose", "Momento", "Glicemia_Pos"])
    
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = carregar_dados()

# --- 3. INTERFACE LATERAL ---
with st.sidebar:
    st.title("🛡️ Glicemia Para Todos")
    aba = st.radio("Navegação", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos"])

# --- ABA INÍCIO ---
if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty:
        st.info("Por favor, cadastre um paciente na aba 'Pacientes'.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: mom = st.selectbox("Refeição", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia"])
        with c3: gpre = st.number_input("Glicemia Pré (mg/dL)", value=110)
        
        st.divider()
        ca, cq = st.columns([3, 1])
        with ca:
            ali = st.selectbox("Selecionar Alimento", df_alimentos["Alimento"].tolist())
            inf = df_alimentos.loc[df_alimentos["Alimento"] == ali].iloc[0]
        with cq: qtd = st.number_input(f"Qtd ({inf['Unidade']})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({
                "Alimento": ali, "Qtd": qtd, "Unidade": inf["Unidade"],
                "Carboidratos": round(float(inf["Carboidratos"]) * qtd, 1),
                "Proteínas": round(float(inf["Proteínas"]) * qtd, 1),
                "Gorduras": round(float(inf["Gorduras"]) * qtd, 1)
            })
            st.rerun()

        if st.session_state.sacola_refeicao:
            tc = sum(i["Carboidratos"] for i in st.session_state.sacola_refeicao)
            tp = sum(i["Proteínas"] for i in st.session_state.sacola_refeicao)
            tg = sum(i["Gorduras"] for i in st.session_state.sacola_refeicao)
            
            st.subheader("Resumo")
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                st.write(f"✅ {item['Alimento']} ({item['Qtd']} {item['Unidade']})")
            
            st.write(f"**Totais:** Carboidratos: {tc}g | Proteínas: {tp}g | Gorduras: {tg}g")

            if st.button("💉 Salvar e Calcular Insulina"):
                dose = round(max(0, (gpre - 100)/50) + (tc / 15), 1)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carboidratos": tc, "Proteínas": tp, "Gorduras": tg, "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}])
                df_h = pd.concat([df_historico, novo], ignore_index=True)
                df_h.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []
                st.success(f"Dose sugerida: {dose} U")
                st.rerun()

# --- ABA PACIENTES ---
elif aba == "👥 Pacientes":
    st.header("👥 Cadastro de Pacientes")
    with st.form("f_pac"):
        n = st.text_input("Nome")
        p = st.selectbox("Vínculo", ["Filha", "Cônjuge", "Outro"])
        if st.form_submit_button("Salvar Paciente"):
            new_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": "", "Sangue": ""}])
            df_p = pd.concat([df_pacientes, new_p], ignore_index=True)
            df_p.to_csv("pacientes.csv", index=False)
            st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

# --- ABA PENDENTES ---
elif aba == "📌 Pendentes":
    st.header("📌 Glicemias Pós-Prandial")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if pendentes.empty:
        st.success("Tudo em dia!")
    else:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Paciente']} - {row['Momento']}"):
                v = st.number_input("Valor Medido", key=f"v_{idx}")
                if st.button("Salvar Pós", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()

# --- ABA HISTÓRICO ---
elif aba == "📊 Histórico":
    st.header("📊 Histórico de Registros")
    st.dataframe(df_historico, use_container_width=True)
    if st.button("Limpar Histórico (CUIDADO)"):
        if os.path.exists("dados_glicemia.csv"):
            os.remove("dados_glicemia.csv")
            st.rerun()

# --- ABA ALIMENTOS ---
elif aba == "🍎 Alimentos":
    st.header("🍎 Banco de Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)