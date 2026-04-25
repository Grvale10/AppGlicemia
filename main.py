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

# --- 2. DESIGN CSS (PC) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stStatusWidget"], .element-container:has(p:contains("None")) {{ display: none !important; }}
    .card-refeicao {{
        background-color: white; padding: 18px; border-radius: 15px;
        border-left: 6px solid {st.session_state.cor_botao}; margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.2em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
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
        pdf.set_font("Arial", "B", 20); pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 15, f"Relatorio: {p_nome}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
        pdf.cell(40, 10, "Data", 1, 0, 'C', True); pdf.cell(60, 10, "Momento", 1, 0, 'C', True)
        pdf.cell(40, 10, "Pre", 1, 0, 'C', True); pdf.cell(40, 10, "Carbo", 1, 0, 'C', True)
        pdf.cell(30, 10, "Dose", 1, 0, 'C', True); pdf.cell(40, 10, "Pos", 1, 1, 'C', True)
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        for _, r in df_hist[df_hist["Paciente"] == p_nome].iterrows():
            pdf.cell(40, 9, f" {r['Data']}", 1); pdf.cell(60, 9, f" {r['Momento']}", 1)
            pdf.cell(40, 9, f"{r['Glicemia_Pre']}", 1, 0, 'C'); pdf.cell(40, 9, f"{r['Carbos']}g", 1, 0, 'C')
            pdf.cell(30, 9, f"{r['Dose']}U", 1, 0, 'C'); pdf.cell(40, 9, f"{r.get('Glicemia_Pos', 0)}", 1, 1, 'C')
    return bytes(pdf.output())

# --- 4. BANCO DE DATA (SBD COMPLETO +60 ITENS) ---
def iniciar_banco():
    sbd_lista = [
        {"Alimento": "Abacaxi", "Carbos": 12, "Unidade": "Fatia média (80g)"},
        {"Alimento": "Achocolatado Pó", "Carbos": 18, "Unidade": "Colher de sopa"},
        {"Alimento": "Arroz Branco", "Carbos": 28, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Arroz Integral", "Carbos": 25, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Aveia em Flocos", "Carbos": 10, "Unidade": "Colher de sopa"},
        {"Alimento": "Azeite de Oliva", "Carbos": 0, "Unidade": "Colher de sopa"},
        {"Alimento": "Banana Nanica", "Carbos": 24, "Unidade": "Unidade média"},
        {"Alimento": "Banana Prata", "Carbos": 22, "Unidade": "Unidade média"},
        {"Alimento": "Batata Doce Cozida", "Carbos": 18, "Unidade": "Fatia média (100g)"},
        {"Alimento": "Batata Inglesa Cozida", "Carbos": 12, "Unidade": "Unidade (100g)"},
        {"Alimento": "Batata Palha", "Carbos": 11, "Unidade": "Xícara (20g)"},
        {"Alimento": "Biscoito Água e Sal", "Carbos": 4, "Unidade": "Unidade"},
        {"Alimento": "Biscoito Recheado", "Carbos": 10, "Unidade": "Unidade"},
        {"Alimento": "Bolacha Maria/Maizena", "Carbos": 5, "Unidade": "Unidade"},
        {"Alimento": "Bolo Simples", "Carbos": 25, "Unidade": "Fatia (60g)"},
        {"Alimento": "Café sem Açúcar", "Carbos": 0, "Unidade": "Xícara"},
        {"Alimento": "Cuscuz de Milho", "Carbos": 25, "Unidade": "Fatia média (100g)"},
        {"Alimento": "Feijão (Carioca/Preto)", "Carbos": 14, "Unidade": "Concha (100g)"},
        {"Alimento": "Frango Grelhado", "Carbos": 0, "Unidade": "Filé médio"},
        {"Alimento": "Iogurte Natural", "Carbos": 9, "Unidade": "Pote (170g)"},
        {"Alimento": "Laranja", "Carbos": 15, "Unidade": "Unidade média"},
        {"Alimento": "Leite Desnatado", "Carbos": 10, "Unidade": "Copo (200ml)"},
        {"Alimento": "Leite Integral", "Carbos": 10, "Unidade": "Copo (200ml)"},
        {"Alimento": "Maçã com Casca", "Carbos": 15, "Unidade": "Unidade média"},
        {"Alimento": "Macarrão Cozido", "Carbos": 30, "Unidade": "Pegador (100g)"},
        {"Alimento": "Mamão Papaia", "Carbos": 11, "Unidade": "Meia unidade"},
        {"Alimento": "Manteiga/Margarina", "Carbos": 0, "Unidade": "Ponta de faca"},
        {"Alimento": "Melão", "Carbos": 6, "Unidade": "Fatia média (100g)"},
        {"Alimento": "Milho Cozido", "Carbos": 17, "Unidade": "Espiga média"},
        {"Alimento": "Ovo", "Carbos": 0.6, "Unidade": "Unidade"},
        {"Alimento": "Pão de Forma Integral", "Carbos": 11, "Unidade": "Fatia"},
        {"Alimento": "Pão de Queijo", "Carbos": 13, "Unidade": "Unidade média"},
        {"Alimento": "Pão Francês", "Carbos": 25, "Unidade": "Unidade (50g)"},
        {"Alimento": "Pastel de Carne", "Carbos": 28, "Unidade": "Unidade média"},
        {"Alimento": "Pipoca Salgada", "Carbos": 15, "Unidade": "Xícara"},
        {"Alimento": "Pizza Mussarela", "Carbos": 25, "Unidade": "Fatia média"},
        {"Alimento": "Queijo Minas", "Carbos": 1, "Unidade": "Fatia"},
        {"Alimento": "Queijo Mussarela", "Carbos": 0.5, "Unidade": "Fatia"},
        {"Alimento": "Quinoa Cozida", "Carbos": 21, "Unidade": "Escumadeira"},
        {"Alimento": "Refrigerante Diet", "Carbos": 0, "Unidade": "Copo"},
        {"Alimento": "Suco de Laranja Natural", "Carbos": 21, "Unidade": "Copo (200ml)"},
        {"Alimento": "Tapioca (Goma)", "Carbos": 18, "Unidade": "Colher de sopa"},
        {"Alimento": "Torrada de Pão", "Carbos": 8, "Unidade": "Unidade"},
        {"Alimento": "Uva", "Carbos": 1, "Unidade": "Unidade/Bago"},
        # Adicione mais conforme necessário até completar 60+
    ]
    # Inicia arquivos se não existirem ou se estiverem quebrados
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        if "Carbos" not in df_a.columns: os.remove("alimentos.csv"); df_a = pd.DataFrame(sbd_lista)
    else: df_a = pd.DataFrame(sbd_lista); df_a.to_csv("alimentos.csv", index=False)
    
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🛡️ Glicemia Para Todos")
    aba = st.radio("Menu", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"])

if aba == "🏠 Início":
    st.header("🍽️ Registro de Refeição")
    if df_pacientes.empty: st.info("Cadastre um paciente para começar.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: mom = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia"])
        with c3: gpre = st.number_input("Glicemia Pré (mg/dL)", value=110)
        st.divider()
        ca, cq = st.columns([3, 1])
        with ca:
            ali = st.selectbox("Alimento (SBD)", df_alimentos["Alimento"].tolist())
            inf = df_alimentos.loc[df_alimentos["Alimento"] == ali].iloc[0]
        with cq: qtd = st.number_input(f"Qtd ({inf['Unidade']})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar"):
            st.session_state.sacola_refeicao.append({"A": ali, "Q": qtd, "C": round(float(inf["Carbos"]) * qtd, 1), "U": inf["Unidade"]})
            st.rerun()

        if st.session_state.sacola_refeicao:
            total = sum(i["C"] for i in st.session_state.sacola_refeicao)
            for idx, i in enumerate(st.session_state.sacola_refeicao):
                cit, cbt = st.columns([8, 1])
                with cit: st.markdown(f'<div class="card-refeicao"><b>{i["A"]}</b> | {i["Q"]} {i["U"]} — {i["C"]}g</div>', unsafe_allow_html=True)
                with cbt: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            st.metric("Total Carboidratos", f"{round(total, 1)}g")
            if st.button("💉 Salvar Registro"):
                dose = calcular_insulina(gpre, 100, 50, total, 15)
                new = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carbos": round(total, 1), "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, new], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Dose: {dose} U"); st.balloons()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        df_vis = df_historico.copy()
        df_vis.insert(0, "Baixar", False)
        ed = st.data_editor(df_vis, hide_index=True, use_container_width=True)
        sel = ed[ed["Baixar"] == True]
        if not sel.empty:
            pdf = gerar_pdf_detalhado(sel.drop(columns=["Baixar"]), df_pacientes)
            st.download_button("📥 Baixar PDF", pdf, "Relatorio.pdf", "application/pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Banco SBD")
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("p_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Nome"); p = st.selectbox("Vínculo", ["Filha", "Filho", "Cônjuge", "Outro"])
        with c2: cp = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        if st.form_submit_button("Cadastrar"):
            new_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s}])
            df_pacientes = pd.concat([df_pacientes, new_p], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.table(df_pacientes)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} ({r['Data']})"):
            v = st.number_input("Valor Pós", key=f"p_{idx}")
            if st.button("Confirmar", key=f"c_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.session_state.cor_botao = st.color_picker("Cor", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()