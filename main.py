import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

# Configuração da página para iniciar com o menu recolhido (opcional, mas ajuda na experiência mobile)
st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FUNÇÕES TÉCNICAS (PDF E CÁLCULO) ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf_detalhado(df_selecionado, df_pacs):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    if df_selecionado.empty: return b""
    pacientes_no_hist = df_selecionado["Paciente"].unique()
    for p_nome in pacientes_no_hist:
        pdf.add_page()
        pdf.set_font("Arial", "B", 20); pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 15, f"Relatório de Controle Glicêmico - {p_nome}", ln=True, align='C')
        pdf.ln(5)
        w = {"data": 35, "refeicao": 55, "pre": 40, "carbo": 35, "dose": 30, "pos": 40}
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        for k, v in zip(w.keys(), ["Data", "Refeição", "Pré", "Carbo", "Dose", "Pós"]):
            pdf.cell(w[k], 10, f" {v}", border=1, fill=True, align='C')
        pdf.ln()
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        dados_p = df_selecionado[df_selecionado["Paciente"] == p_nome]
        zebra = False
        for _, row in dados_p.iterrows():
            pdf.set_fill_color(245, 245, 245) if zebra else pdf.set_fill_color(255, 255, 255)
            pdf.cell(w["data"], 9, f" {row['Data']}", border=1, fill=True)
            pdf.cell(w["refeicao"], 9, f" {row.get('Momento', 'Outro')}", border=1, fill=True)
            pdf.cell(w["pre"], 9, f"{row['Glicemia_Pre']}", border=1, fill=True, align='C')
            pdf.cell(w["carbo"], 9, f"{row['Carbos']}", border=1, fill=True, align='C')
            pdf.cell(w["dose"], 9, f"{row['Dose']}", border=1, fill=True, align='C')
            g_v = row.get('Glicemia_Pos', 0)
            pdf.cell(w["pos"], 9, f"{g_v}" if g_v != 0 else "-", border=1, fill=True, align='C', ln=True)
            zebra = not zebra
    return bytes(pdf.output())

# --- 3. DESIGN CSS (CUSTOMIZAÇÃO DO ÍCONE E MENU) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    .stButton>button {{ width: 100%; border-radius: 14px; background-color: {st.session_state.cor_botao} !important; color: white !important; font-weight: bold; border: none; }}
    .card-refeicao {{ background-color: white; padding: 15px; border-radius: 15px; border: 1px solid #E5E7EB; margin-bottom: 5px; }}
    
    /* TROCAR ">>" POR 3 BARRAS */
    button[kind="headerNoPadding"] {{
        background-color: transparent !important;
    }}
    button[kind="headerNoPadding"] svg {{
        display: none; /* Esconde as setinhas originais */
    }}
    button[kind="headerNoPadding"]::after {{
        content: "☰"; /* Ícone de 3 barras */
        font-size: 24px;
        color: {st.session_state.cor_botao};
        visibility: visible;
        display: block;
        padding-bottom: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS ---
def iniciar_banco():
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carbos", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue", "Tipo_Plano"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1F2937;'>Menu</h2>", unsafe_allow_html=True)
    # No Streamlit, ao mudar o valor do rádio, a página recarrega. 
    # Com initial_sidebar_state="collapsed", ele tende a fechar no mobile após a ação.
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "💉 Glicemia Pós", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS (FIÉIS À 8.1) ---

if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty: st.warning("Cadastre um paciente.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: refeicao_tipo = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia", "Outro"])
        with c3: g_pre = st.number_input("Glicemia Pré (mg/dL)", min_value=20, value=110)
        st.divider()
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            alimento_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
            try: lin = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel].iloc[0]; val_c = lin["Carbos"]; uni_a = lin["Unidade"]
            except: val_c = 0.0; uni_a = "un"
        with col_i2: qtd = st.number_input(f"Qtd ({uni_a})", min_value=0.1, value=1.0)
        if st.button("➕ Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({"Alimento": alimento_sel, "Qtd": qtd, "Carbos": round(float(val_c) * qtd, 1), "Unidade": uni_a})
            st.rerun()
        if st.session_state.sacola_refeicao:
            total_c = sum(i['Carbos'] for i in st.session_state.sacola_refeicao)
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                it_c, dl_c = st.columns([6, 1])
                with it_c: st.markdown(f'<div class="card-refeicao"><b>{item["Alimento"]}</b> | {item["Qtd"]} {item["Unidade"]}</div>', unsafe_allow_html=True)
                with dl_c: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            if st.button("💉 Salvar Registro"):
                dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": round(total_c, 1), "Dose": dose, "Momento": refeicao_tipo, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Dose: {dose} U"); st.rerun()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        df_com_sel = df_historico.copy(); df_com_sel.insert(0, "Sel", False)
        df_editado = st.data_editor(df_com_sel, column_config={"Sel": st.column_config.CheckboxColumn("PDF", default=False)}, disabled=[c for c in df_com_sel.columns if c != "Sel"], hide_index=True, use_container_width=True, key="hist_final")
        itens = df_editado[df_editado["Sel"] == True]
        if not itens.empty:
            pdf_b = gerar_pdf_detalhado(itens.drop(columns=["Sel"]), df_pacientes)
            st.download_button("📥 Baixar PDF", pdf_b, "Relatorio.pdf", "application/pdf")

elif aba == "💉 Glicemia Pós":
    st.header("💉 Glicemia Pós")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} ({r['Data']})"):
            v = st.number_input("Valor Pós", key=f"v_{idx}")
            if st.button("Salvar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("pf"):
        n = st.text_input("Nome"); p = st.selectbox("Parentesco", ["Filho", "Filha", "Outro"])
        if st.form_submit_button("Salvar"):
            new = pd.DataFrame([{"Nome": n, "Parentesco": p}])
            df_pacientes = pd.concat([df_pacientes, new], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    with st.form("af"):
        n_a = st.text_input("Nome"); c_a = st.number_input("Carbos"); u_a = st.text_input("Unidade")
        if st.form_submit_button("Salvar"):
            new = pd.DataFrame([{"Alimento": n_a, "Carbos": c_a, "Unidade": u_a}])
            df_alimentos = pd.concat([df_alimentos, new], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "👤 Perfil":
    st.session_state.cor_botao = st.color_picker("Cor", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()