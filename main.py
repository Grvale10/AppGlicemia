import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DESIGN CSS (CORREÇÃO NONE E 3 BARRAS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stStatusWidget"], div.element-container:has(p:contains("None")) {{ display: none !important; }}
    button[kind="headerNoPadding"] svg {{ display: none !important; }}
    button[kind="headerNoPadding"]::after {{
        content: "☰"; color: {st.session_state.cor_botao};
        font-size: 24px; font-weight: bold;
    }}
    .stButton>button {{
        width: 100%; border-radius: 14px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}
    .card-refeicao {{
        background-color: white; padding: 15px; border-radius: 15px;
        border-left: 5px solid {st.session_state.cor_botao}; margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf_detalhado(df_hist, df_pacs):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    for p_nome in df_hist["Paciente"].unique():
        pdf.add_page()
        pdf.set_font("Arial", "B", 18); pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 15, f"Relatorio: {p_nome}", ln=True, align='C')
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        pdf.cell(40, 10, " Data/Hora", 1, 0, 'L', True)
        pdf.cell(60, 10, " Refeicao", 1, 0, 'L', True)
        pdf.cell(40, 10, " Glicemia Pre", 1, 0, 'C', True)
        pdf.cell(40, 10, " Carboidratos", 1, 0, 'C', True)
        pdf.cell(30, 10, " Dose", 1, 0, 'C', True)
        pdf.cell(40, 10, " Glicemia Pos", 1, 1, 'C', True)
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        for _, row in df_hist[df_hist["Paciente"] == p_nome].iterrows():
            pdf.cell(40, 9, f" {row['Data']}", 1)
            pdf.cell(60, 9, f" {row['Momento']}", 1)
            pdf.cell(40, 9, f" {row['Glicemia_Pre']} mg/dL", 1, 0, 'C')
            pdf.cell(40, 9, f" {row['Carbos']}g", 1, 0, 'C')
            pdf.cell(30, 9, f" {row['Dose']} U", 1, 0, 'C')
            pdf.cell(40, 9, f" {row.get('Glicemia_Pos', 0)} mg/dL", 1, 1, 'C')
    return bytes(pdf.output())

# --- 4. BANCO DE DADOS (CORREÇÃO DE KEYERROR) ---
def iniciar_banco():
    sbd = [
        {"Alimento": "Arroz Branco", "Carbos": 28.0, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Arroz Integral", "Carbos": 25.0, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Feijao Carioca", "Carbos": 14.0, "Unidade": "Concha (100g)"},
        {"Alimento": "Pao Frances", "Carbos": 25.0, "Unidade": "1 unidade (50g)"},
        {"Alimento": "Tapioca (Goma)", "Carbos": 54.0, "Unidade": "3 colheres (100g)"},
        {"Alimento": "Cuscuz", "Carbos": 25.0, "Unidade": "Fatia media (100g)"},
        {"Alimento": "Banana Prata", "Carbos": 22.0, "Unidade": "1 unidade"},
        {"Alimento": "Maca media", "Carbos": 15.0, "Unidade": "1 unidade"},
        {"Alimento": "Leite Integral", "Carbos": 10.0, "Unidade": "Copo (200ml)"},
        {"Alimento": "Macarrao Cozido", "Carbos": 30.0, "Unidade": "Pegador (100g)"}
    ]
    
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        # Se a coluna 'Carbos' não existir, deletamos o arquivo antigo para evitar o erro
        if "Carbos" not in df_a.columns:
            os.remove("alimentos.csv")
            df_a = pd.DataFrame(sbd)
            df_a.to_csv("alimentos.csv", index=False)
    else:
        df_a = pd.DataFrame(sbd)
        df_a.to_csv("alimentos.csv", index=False)
        
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: {st.session_state.cor_botao};'>Glicemia App</h2>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Inicio", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---
if aba == "🏠 Inicio":
    st.header("🍽️ Registrar Refeicao")
    if df_pacientes.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist(), help="Selecione o paciente.")
        with c2: mom = st.selectbox("Momento", ["Cafe", "Almoco", "Jantar", "Lanche", "Ceia"], help="Tipo da refeicao.")
        with c3: gpre = st.number_input("Glicemia Pre (mg/dL)", value=110, help="Glicemia antes de comer.")
        
        st.divider()
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            ali_sel = st.selectbox("Alimento (SBD)", df_alimentos["Alimento"].tolist())
            lin = df_alimentos.loc[df_alimentos["Alimento"] == ali_sel].iloc[0]
            v_carbo = lin["Carbos"]; v_uni = lin["Unidade"]
        with col_i2: qtd = st.number_input(f"Qtd ({v_uni})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar"):
            st.session_state.sacola_refeicao.append({"A": ali_sel, "Q": qtd, "C": round(float(v_carbo) * qtd, 1), "U": v_uni})
            st.rerun()

        if st.session_state.sacola_refeicao:
            total_c = sum(i['C'] for i in st.session_state.sacola_refeicao)
            for idx, i in enumerate(st.session_state.sacola_refeicao):
                cit, cde = st.columns([6, 1])
                with cit: st.markdown(f'<div class="card-refeicao"><b>{i["A"]}</b> | {i["Q"]} {i["U"]} ({i["C"]}g)</div>', unsafe_allow_html=True)
                with cde: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            st.metric("Total Carboidratos", f"{round(total_c, 1)}g")
            if st.button("💉 Salvar e Calcular"):
                dose = calcular_insulina(gpre, 100, 50, total_c, 15)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carbos": round(total_c, 1), "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Salvo! Dose: {dose} U"); st.balloons()

elif aba == "📊 Histórico":
    st.header("📊 Historico e PDF")
    if not df_historico.empty:
        df_vis = df_historico.copy()
        df_vis.insert(0, "Exportar", False)
        df_ed = st.data_editor(df_vis, column_config={"Exportar": st.column_config.CheckboxColumn("Exportar", default=False)}, disabled=[c for c in df_vis.columns if c != "Exportar"], hide_index=True, use_container_width=True)
        sel = df_ed[df_ed["Exportar"] == True]
        if not sel.empty:
            pdf_b = gerar_pdf_detalhado(sel.drop(columns=["Exportar"]), df_pacientes)
            st.download_button("📥 Baixar PDF", pdf_b, "Relatorio.pdf", "application/pdf")
    else: st.info("Historico vazio.")

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardapio SBD")
    with st.form("f_ali", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: n = st.text_input("Nome Alimento")
        with c2: c = st.number_input("Carbos (g)")
        with c3: u = st.text_input("Unidade (ex: fatia)")
        if st.form_submit_button("Salvar"):
            new = pd.DataFrame([{"Alimento": n, "Carbos": c, "Unidade": u}])
            df_alimentos = pd.concat([df_alimentos, new], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("add_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Nome"); p = st.selectbox("Parentesco", ["Filha", "Filho", "Conjuge", "Outro"])
        with c2: cp = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        if st.form_submit_button("Salvar"):
            np = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s}])
            df_pacientes = pd.concat([df_pacientes, np], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.table(df_pacientes)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pos")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} - {r['Momento']} ({r['Data']})"):
            v = st.number_input("Valor Pos", key=f"v_{idx}")
            if st.button("Confirmar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.header("⚙️ Ajustes")
    st.session_state.cor_botao = st.color_picker("Cor Botao", st.session_state.cor_botao)
    if st.button("Aplicar"): st.rerun()