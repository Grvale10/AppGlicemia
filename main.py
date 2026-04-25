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

# --- 2. DESIGN CSS (OTIMIZADO PARA PC) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* REMOVER MENSAGENS DE LOG E "NONE" */
    [data-testid="stStatusWidget"], .element-container:has(p:contains("None")) {{ display: none !important; }}

    /* ESTILO DOS CARDS DE REFEIÇÃO */
    .card-refeicao {{
        background-color: white; padding: 18px; border-radius: 15px;
        border-left: 6px solid {st.session_state.cor_botao}; margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: 0.3s;
    }}
    .card-refeicao:hover {{ transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }}

    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.2em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none; font-size: 16px;
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
        pdf.cell(0, 15, f"Relatorio de Controle: {p_nome}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
        cols = {"Data": 40, "Momento": 60, "Pre": 40, "Carbo": 40, "Dose": 30, "Pos": 40}
        for k, v in cols.items(): pdf.cell(v, 10, k, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        for _, r in df_hist[df_hist["Paciente"] == p_nome].iterrows():
            pdf.cell(40, 9, f" {r['Data']}", 1)
            pdf.cell(60, 9, f" {r['Momento']}", 1)
            pdf.cell(40, 9, f"{r['Glicemia_Pre']} mg/dL", 1, 0, 'C')
            pdf.cell(40, 9, f"{r['Carbos']}g", 1, 0, 'C')
            pdf.cell(30, 9, f"{r['Dose']} U", 1, 0, 'C')
            pdf.cell(40, 9, f"{r.get('Glicemia_Pos', 0)} mg/dL", 1, 1, 'C')
    return bytes(pdf.output())

# --- 4. BANCO DE DADOS (COM TABELA SBD COMPLETA) ---
def iniciar_banco():
    sbd_data = [
        {"Alimento": "Arroz Branco (Escumadeira)", "Carbos": 28, "Unidade": "100g"},
        {"Alimento": "Arroz Integral (Escumadeira)", "Carbos": 25, "Unidade": "100g"},
        {"Alimento": "Feijão Carioca (Concha)", "Carbos": 14, "Unidade": "100g"},
        {"Alimento": "Pão Francês (Unidade)", "Carbos": 25, "Unidade": "50g"},
        {"Alimento": "Macarrão Cozido (Pegador)", "Carbos": 30, "Unidade": "100g"},
        {"Alimento": "Batata Inglesa Cozida", "Carbos": 12, "Unidade": "100g"},
        {"Alimento": "Tapioca (Goma)", "Carbos": 18, "Unidade": "Colher de sopa"},
        {"Alimento": "Cuscuz de Milho (Fatia)", "Carbos": 25, "Unidade": "100g"},
        {"Alimento": "Banana Prata", "Carbos": 22, "Unidade": "Unidade"},
        {"Alimento": "Maçã com casca", "Carbos": 15, "Unidade": "Unidade média"},
        {"Alimento": "Leite Integral (Copo)", "Carbos": 10, "Unidade": "200ml"},
        {"Alimento": "Iogurte Natural (Pote)", "Carbos": 9, "Unidade": "170g"},
        {"Alimento": "Ovo Cozido", "Carbos": 0.6, "Unidade": "Unidade"},
        {"Alimento": "Frango Grelhado", "Carbos": 0, "Unidade": "100g"},
        {"Alimento": "Carne Bovina Grelhada", "Carbos": 0, "Unidade": "100g"},
        {"Alimento": "Suco de Laranja Natural", "Carbos": 21, "Unidade": "200ml"},
        {"Alimento": "Pizza de Mussarela", "Carbos": 25, "Unidade": "Fatia média"},
        {"Alimento": "Biscoito Cream Cracker", "Carbos": 4.5, "Unidade": "Unidade"}
    ]
    
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        if "Carbos" not in df_a.columns: # Proteção contra o erro que deu
            df_a = pd.DataFrame(sbd_data)
            df_a.to_csv("alimentos.csv", index=False)
    else:
        df_a = pd.DataFrame(sbd_data)
        df_a.to_csv("alimentos.csv", index=False)

    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🛡️ Glicemia PRO")
    aba = st.radio("Menu", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"])

if aba == "🏠 Início":
    st.header("🍽️ Registro Rápido de Refeição")
    if df_pacientes.empty:
        st.info("👋 Bem-vindo! Comece cadastrando um paciente na aba lateral.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with col2: mom_sel = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia"])
        with col3: g_pre = st.number_input("Glicemia Pré (mg/dL)", value=110)

        st.divider()
        c_ali, c_qtd = st.columns([3, 1])
        with c_ali:
            ali_nome = st.selectbox("Buscar na Tabela SBD", df_alimentos["Alimento"].tolist())
            ali_info = df_alimentos.loc[df_alimentos["Alimento"] == ali_nome].iloc[0]
        with c_qtd:
            qtd = st.number_input(f"Quantidade ({ali_info['Unidade']})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({
                "A": ali_nome, "Q": qtd, "C": round(float(ali_info["Carbos"]) * qtd, 1), "U": ali_info["Unidade"]
            })
            st.rerun()

        if st.session_state.sacola_refeicao:
            st.subheader("📋 Itens no Prato")
            total_c = sum(item["C"] for item in st.session_state.sacola_refeicao)
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                ca, cd = st.columns([8, 1])
                with ca: st.markdown(f'<div class="card-refeicao"><b>{item["A"]}</b> | {item["Q"]} {item["U"]} — <b>{item["C"]}g de Carbo</b></div>', unsafe_allow_html=True)
                with cd: 
                    if st.button("🗑️", key=f"btn_{idx}"):
                        st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            st.metric("Total de Carboidratos", f"{round(total_c, 1)} g")
            if st.button("💉 Calcular Dose e Salvar"):
                dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
                novo_reg = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, 
                    "Glicemia_Pre": g_pre, "Carbos": round(total_c, 1), "Dose": dose, 
                    "Momento": mom_sel, "Glicemia_Pos": 0
                }])
                df_historico = pd.concat([df_historico, novo_reg], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []
                st.success(f"Dose Recomendada: {dose} U"); st.balloons()

elif aba == "📊 Histórico":
    st.header("📊 Histórico de Medições")
    if not df_historico.empty:
        df_copy = df_historico.copy()
        df_copy.insert(0, "Selecionar", False)
        ed = st.data_editor(df_copy, hide_index=True, use_container_width=True)
        selecionados = ed[ed["Selecionar"] == True]
        if not selecionados.empty:
            pdf = gerar_pdf_detalhado(selecionados.drop(columns=["Selecionar"]), df_pacientes)
            st.download_button("📥 Baixar Relatório PDF", pdf, "Historico_Glicemia.pdf", "application/pdf")
    else: st.warning("Nenhum dado encontrado.")

elif aba == "🍎 Alimentos":
    st.header("🍎 Banco de Alimentos (SBD)")
    with st.form("add_ali", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: n = st.text_input("Nome do Alimento")
        with c2: c = st.number_input("Carbos (g)")
        with c3: u = st.text_input("Unidade (ex: fatia, g, copo)")
        if st.form_submit_button("💾 Salvar Novo Alimento"):
            new_a = pd.DataFrame([{"Alimento": n, "Carbos": c, "Unidade": u}])
            df_alimentos = pd.concat([df_alimentos, new_a], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False)
            st.success("Alimento salvo!"); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "👥 Pacientes":
    st.header("👥 Gestão de Pacientes")
    with st.form("p_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: nome = st.text_input("Nome Completo"); par = st.selectbox("Vínculo", ["Filha", "Filho", "Cônjuge", "Próprio"])
        with c2: cpf = st.text_input("CPF"); sang = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        if st.form_submit_button("💾 Cadastrar"):
            new_p = pd.DataFrame([{"Nome": nome, "Parentesco": par, "CPF": cpf, "Sangue": sang}])
            df_pacientes = pd.concat([df_pacientes, new_p], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.table(df_pacientes)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Prandial")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if pendentes.empty: st.success("Tudo em dia! Nenhuma medição pendente.")
    for idx, row in pendentes.iterrows():
        with st.expander(f"📝 {row['Paciente']} - {row['Momento']} ({row['Data']})"):
            valor = st.number_input("Valor medido (mg/dL)", key=f"pos_{idx}")
            if st.button("Confirmar", key=f"conf_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = valor
                df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.header("⚙️ Configurações")
    st.session_state.cor_botao = st.color_picker("Cor da Identidade Visual", st.session_state.cor_botao)
    if st.button("Aplicar Nova Cor"): st.rerun()