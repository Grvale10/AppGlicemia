import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

# --- 2. BANCO DE DADOS (COM PADRONIZAÇÃO) ---
def iniciar_banco_dados():
    # Se o arquivo de glicemia existir, vamos garantir que as colunas tenham os nomes certos
    c_hist = ["Data", "Paciente", "Glicemia_Pré", "Carboidratos", "Proteínas", "Gorduras", "Dose", "Momento", "Glicemia_Pós"]
    
    if os.path.exists("dados_glicemia.csv"):
        df_h = pd.read_csv("dados_glicemia.csv")
        # Se as colunas estiverem com nomes antigos, renomeamos agora para evitar o KeyError
        mapa_nomes = {
            "Glicemia Pré": "Glicemia_Pré",
            "Glicemia Pós": "Glicemia_Pós",
            "Glicemia_Pre": "Glicemia_Pré",
            "Glicemia_Pos": "Glicemia_Pós"
        }
        df_h = df_h.rename(columns=mapa_nomes)
    else:
        df_h = pd.DataFrame(columns=c_hist)

    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carboidratos", "Proteínas", "Gorduras", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    
    return df_a, df_h, df_p

# --- 3. FUNÇÃO DO PDF CORRIGIDA ---
def gerar_pdf_completo(df_hist):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatorio Glicemia Para Todos", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    cols = ["Data", "Paciente", "Glicemia Pre", "Carbo", "Prot", "Gord", "Dose", "Glicemia Pos"]
    larguras = [35, 45, 30, 25, 25, 25, 25, 30]
    for i, col in enumerate(cols):
        pdf.cell(larguras[i], 10, col, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for _, r in df_hist.iterrows():
        # Usamos .get() ou nomes seguros para evitar o erro se a coluna sumir
        g_pre = r.get('Glicemia_Pré', r.get('Glicemia_Pre', 0))
        g_pos = r.get('Glicemia_Pós', r.get('Glicemia_Pos', 0))
        
        pdf.cell(35, 8, str(r['Data']), 1)
        pdf.cell(45, 8, str(r['Paciente']), 1)
        pdf.cell(30, 8, f"{g_pre} mg/dL", 1, 0, 'C')
        pdf.cell(25, 8, f"{r.get('Carboidratos', 0)}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r.get('Proteínas', 0)}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r.get('Gorduras', 0)}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r['Dose']} U", 1, 0, 'C')
        pdf.cell(30, 8, f"{g_pos} mg/dL", 1, 1, 'C')
    return bytes(pdf.output())

df_alimentos, df_historico, df_pacientes = iniciar_banco_dados()

# --- 4. INTERFACE (MANTENDO AS ABAS RESTAURADAS) ---
with st.sidebar:
    st.title("🛡️ Glicemia Para Todos")
    aba = st.radio("Menu", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos"])

if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: mom = st.selectbox("Refeição", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia"])
        with c3: gpre = st.number_input("Glicemia Pré (mg/dL)", value=110)
        
        st.divider()
        ca, cq = st.columns([3, 1])
        with ca:
            if not df_alimentos.empty:
                ali_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
                inf = df_alimentos.loc[df_alimentos["Alimento"] == ali_sel].iloc[0]
            else: st.error("Tabela de alimentos vazia.")
        with cq: qtd = st.number_input(f"Qtd", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar"):
            st.session_state.sacola_refeicao.append({
                "Alimento": ali_sel, "Quantidade": qtd, "Unidade": inf["Unidade"],
                "Carboidratos": round(float(inf["Carboidratos"]) * qtd, 1),
                "Proteínas": round(float(inf["Proteínas"]) * qtd, 1),
                "Gorduras": round(float(inf["Gorduras"]) * qtd, 1)
            })
            st.rerun()

        if st.session_state.sacola_refeicao:
            total_c = sum(i["Carboidratos"] for i in st.session_state.sacola_refeicao)
            total_p = sum(i["Proteínas"] for i in st.session_state.sacola_refeicao)
            total_g = sum(i["Gorduras"] for i in st.session_state.sacola_refeicao)
            
            st.subheader("📊 Totais")
            t1, t2, t3 = st.columns(3)
            t1.metric("Carboidratos", f"{round(total_c, 1)}g")
            t2.metric("Proteínas", f"{round(total_p, 1)}g")
            t3.metric("Gorduras", f"{round(total_g, 1)}g")

            if st.button("💉 Salvar Registro"):
                dose = round(max(0, (gpre - 100)/50) + (total_c / 15), 1)
                novo_r = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": pac,
                    "Glicemia_Pré": gpre, "Carboidratos": total_c, "Proteínas": total_p, "Gorduras": total_g,
                    "Dose": dose, "Momento": mom, "Glicemia_Pós": 0
                }])
                df_historico = pd.concat([df_historico, novo_r], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []
                st.success(f"Salvo! Dose: {dose} U"); st.rerun()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        df_edit = df_historico.copy()
        df_edit.insert(0, "Selecionar", False)
        ed = st.data_editor(df_edit, hide_index=True, use_container_width=True)
        sel = ed[ed["Selecionar"] == True]
        if not sel.empty:
            pdf = gerar_pdf_completo(sel)
            st.download_button("📥 Baixar PDF", pdf, "Historico.pdf", "application/pdf")
    else: st.info("Histórico vazio.")

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("p_form", clear_on_submit=True):
        n = st.text_input("Nome"); p = st.selectbox("Vínculo", ["Filha", "Filho", "Cônjuge", "Outro"])
        c = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        if st.form_submit_button("Salvar"):
            new_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": c, "Sangue": s}])
            df_p = pd.concat([df_pacientes, new_p], ignore_index=True); df_p.to_csv("pacientes.csv", index=False); st.rerun()
    st.table(df_pacientes)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Prandial")
    # Filtra onde Glicemia_Pós é 0 ou Nulo
    pend = df_historico[df_historico["Glicemia_Pós"].astype(float) == 0]
    for idx, row in pend.iterrows():
        with st.expander(f"{row['Paciente']} - {row['Momento']}"):
            val = st.number_input("Valor Pós", key=f"p_{idx}")
            if st.button("Confirmar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pós"] = val
                df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)