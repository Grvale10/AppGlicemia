import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="expanded")

# --- 2. DESIGN CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stStatusWidget"], .element-container:has(p:contains("None")) {{ display: none !important; }}
    .card-refeicao {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-left: 6px solid {st.session_state.cor_botao}; margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
def iniciar_banco_dados():
    lista_sbd = [
        {"Alimento": "Arroz Branco", "Carboidratos": 28.0, "Proteínas": 2.5, "Gorduras": 0.2, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Feijão Carioca", "Carboidratos": 14.0, "Proteínas": 5.0, "Gorduras": 0.5, "Unidade": "Concha (100g)"},
        {"Alimento": "Pão Francês", "Carboidratos": 25.0, "Proteínas": 4.0, "Gorduras": 1.5, "Unidade": "Unidade (50g)"},
        {"Alimento": "Peito de Frango Grelhado", "Carboidratos": 0.0, "Proteínas": 31.0, "Gorduras": 3.6, "Unidade": "100g"},
        {"Alimento": "Ovo Cozido", "Carboidratos": 0.6, "Proteínas": 6.3, "Gorduras": 5.3, "Unidade": "Unidade"},
        {"Alimento": "Leite Integral", "Carboidratos": 10.0, "Proteínas": 6.8, "Gorduras": 6.0, "Unidade": "Copo (200ml)"}
    ]
    
    if not os.path.exists("alimentos.csv"):
        pd.DataFrame(lista_sbd).to_csv("alimentos.csv", index=False)
    
    df_a = pd.read_csv("alimentos.csv")
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pré", "Carboidratos", "Proteínas", "Gorduras", "Dose", "Momento", "Glicemia_Pós"])
    
    return df_a, df_h, df_p

def gerar_pdf_completo(df_hist):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatório Glicemia Para Todos", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    
    # Cabeçalho do PDF
    colunas = ["Data", "Paciente", "Glicemia Pré", "Carbo", "Prot", "Gord", "Dose", "Glicemia Pós"]
    larguras = [35, 45, 30, 25, 25, 25, 25, 30]
    for i, col in enumerate(colunas):
        pdf.cell(larguras[i], 10, col, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for _, r in df_hist.iterrows():
        pdf.cell(35, 8, str(r['Data']), 1)
        pdf.cell(45, 8, str(r['Paciente']), 1)
        pdf.cell(30, 8, f"{r['Glicemia_Pré']} mg/dL", 1, 0, 'C')
        pdf.cell(25, 8, f"{r['Carboidratos']}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r['Proteínas']}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r['Gorduras']}g", 1, 0, 'C')
        pdf.cell(25, 8, f"{r['Dose']} U", 1, 0, 'C')
        pdf.cell(30, 8, f"{r['Glicemia_Pós']} mg/dL", 1, 1, 'C')
    return bytes(pdf.output())

df_alimentos, df_historico, df_pacientes = iniciar_banco_dados()

# --- 4. INTERFACE ---
with st.sidebar:
    st.title("🛡️ Glicemia Para Todos")
    aba = st.radio("Menu", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos"])

# --- ABA INÍCIO (REGISTRO) ---
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
            ali_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
            inf = df_alimentos.loc[df_alimentos["Alimento"] == ali_sel].iloc[0]
        with cq: qtd = st.number_input(f"Qtd ({inf['Unidade']})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar ao Prato"):
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
            
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                st.markdown(f'<div class="card-refeicao"><b>{item["Alimento"]}</b> - {item["Quantidade"]} {item["Unidade"]}<br><small>Carboidratos: {item["Carboidratos"]}g | Proteínas: {item['Proteínas']}g | Gorduras: {item['Gorduras']}g</small></div>', unsafe_allow_html=True)
            
            st.subheader("📊 Totais")
            t1, t2, t3 = st.columns(3)
            t1.metric("Total Carboidratos", f"{round(total_c, 1)}g")
            t2.metric("Total Proteínas", f"{round(total_p, 1)}g")
            t3.metric("Total Gorduras", f"{round(total_g, 1)}g")

            if st.button("💉 Salvar e Calcular"):
                dose = round(max(0, (gpre - 100)/50) + (total_c / 15), 1)
                novo_r = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": pac, "Glicemia_Pré": gpre, "Carboidratos": total_c, "Proteínas": total_p, "Gorduras": total_g, "Dose": dose, "Momento": mom, "Glicemia_Pós": 0}])
                df_historico = pd.concat([df_historico, novo_r], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Salvo! Dose: {dose} U"); st.balloons()

# --- ABA PACIENTES (RESTAURADA) ---
elif aba == "👥 Pacientes":
    st.header("👥 Gestão de Pacientes")
    with st.form("p_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: n = st.text_input("Nome Completo"); p = st.selectbox("Parentesco", ["Filha", "Filho", "Cônjuge", "Outro"])
        with col2: c = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        if st.form_submit_button("Cadastrar Paciente"):
            new_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": c, "Sangue": s}])
            df_pacientes = pd.concat([df_pacientes, new_p], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.table(df_pacientes)

# --- ABA PENDENTES (RESTAURADA) ---
elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Prandial")
    pendentes = df_historico[df_historico["Glicemia_Pós"] == 0]
    if pendentes.empty:
        st.success("Nenhuma medição pendente!")
    else:
        for idx, row in pendentes.iterrows():
            with st.expander(f"📝 {row['Paciente']} - {row['Momento']} ({row['Data']})"):
                valor_pos = st.number_input("Valor medido (mg/dL)", key=f"pos_{idx}")
                if st.button("Confirmar", key=f"btn_{idx}"):
                    df_historico.at[idx, "Glicemia_Pós"] = valor_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

# --- ABA HISTÓRICO (RESTAURADA) ---
elif aba == "📊 Histórico":
    st.header("📊 Histórico Completo")
    if not df_historico.empty:
        df_edit = df_historico.copy()
        df_edit.insert(0, "Selecionar", False)
        ed = st.data_editor(df_edit, hide_index=True, use_container_width=True)
        selecionados = ed[ed["Selecionar"] == True]
        if not selecionados.empty:
            pdf = gerar_pdf_completo(selecionados)
            st.download_button("📥 Baixar PDF Selecionado", pdf, "Historico.pdf", "application/pdf")
    else: st.info("Nenhum registro encontrado.")

# --- ABA ALIMENTOS ---
elif aba == "🍎 Alimentos":
    st.header("🍎 Tabela de Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)