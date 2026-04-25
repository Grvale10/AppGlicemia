import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F0F2F6"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DESIGN E LIMPEZA (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* Tabelas e Dataframes Modernos */
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
        background: white; border-radius: 15px; padding: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); border: 1px solid #E5E7EB;
    }}

    /* Botões */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 45px;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}

    /* REMOVER SETINHAS E COLOCAR 3 BARRAS */
    button[kind="headerNoPadding"] svg {{ display: none !important; }}
    button[kind="headerNoPadding"]::after {{
        content: "☰"; color: {st.session_state.cor_botao};
        font-size: 26px; font-weight: bold; display: block;
    }}

    /* ELIMINAR O "NONE" LOG */
    div[data-testid="stNotification"], div.element-container:has(p:contains("None")) {{
        display: none !important;
    }}

    /* Tooltips e Estilo de Cards */
    .card-refeicao {{
        background: white; padding: 12px; border-radius: 12px;
        margin-bottom: 8px; border-left: 5px solid {st.session_state.cor_botao};
        box-shadow: 2px 2px 5px rgba(0,0,0,0.03);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS (ESTRUTURA COMPLETA 8.1) ---
def iniciar_banco():
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carbos", "Proteina", "Gordura", "Gramas", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 4. FUNÇÕES ---
def gerar_pdf(df_sel):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatório Glicêmico", ln=True, align='C')
    # Resumo simplificado para garantir funcionamento
    for _, r in df_sel.iterrows():
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"{r['Data']} - {r['Paciente']}: Pre {r['Glicemia_Pre']} | Carbos {r['Carbos']} | Dose {r['Dose']}", ln=True)
    return bytes(pdf.output())

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: {st.session_state.cor_botao};'>Glicemia Todos</h2>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "💉 Glicemia Pós", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist(), help="Para quem é a refeição?")
        with c2: mom = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Ceia"], help="Qual o tipo da refeição?")
        with c3: gpre = st.number_input("Glicemia Pré", value=110, help="Valor antes de comer")
        
        st.divider()
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            ali_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist(), help="Pesquise o que cadastrou")
            lin = df_alimentos.loc[df_alimentos["Alimento"] == ali_sel].iloc[0] if not df_alimentos.empty else None
            val_c = lin["Carbos"] if lin is not None else 0
            uni_a = lin["Unidade"] if lin is not None else "un"
        with col_i2: qtd = st.number_input(f"Qtd", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar"):
            st.session_state.sacola_refeicao.append({"A": ali_sel, "Q": qtd, "C": round(float(val_c) * qtd, 1), "U": uni_a})
            st.rerun()

        if st.session_state.sacola_refeicao:
            total = sum(i['C'] for i in st.session_state.sacola_refeicao)
            for idx, i in enumerate(st.session_state.sacola_refeicao):
                col_it, col_de = st.columns([6, 1])
                with col_it: st.markdown(f'<div class="card-refeicao"><b>{i["A"]}</b> | {i["Q"]} {i["U"]} ({i["C"]}g)</div>', unsafe_allow_html=True)
                with col_de: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            st.metric("Total Carboidratos", f"{round(total, 1)}g")
            if st.button("💉 Salvar Registro"):
                dose = round(max(0, (gpre - 100)/50) + (total/15), 1)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carbos": round(total, 1), "Dose": dose, "Momento": mom, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success("Salvo!"); st.rerun()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        df_vis = df_historico.copy()
        df_vis.insert(0, "Sel", False)
        df_ed = st.data_editor(df_vis, column_config={"Sel": st.column_config.CheckboxColumn("PDF")}, disabled=[c for c in df_vis.columns if c != "Sel"], hide_index=True, use_container_width=True, key="ed_hist")
        sel = df_ed[df_ed["Sel"] == True]
        if not sel.empty:
            pdf = gerar_pdf(sel.drop(columns=["Sel"]))
            st.download_button("📥 Baixar PDF", pdf, "Historico.pdf", "application/pdf")
    else: st.info("Histórico vazio.")

elif aba == "💉 Glicemia Pós":
    st.header("💉 Glicemia Pós")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} - {r['Data']}"):
            v_pos = st.number_input("Valor Pós", key=f"v_{idx}")
            if st.button("Confirmar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v_pos; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("f_p"):
        n = st.text_input("Nome")
        p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"])
        if st.form_submit_button("Salvar"):
            new = pd.DataFrame([{"Nome": n, "Parentesco": p}])
            df_pacientes = pd.concat([df_pacientes, new], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    with st.form("f_a"):
        n = st.text_input("Alimento")
        c = st.number_input("Carbos (g)")
        u = st.text_input("Unidade (ex: colher, gramas)")
        if st.form_submit_button("Cadastrar"):
            new = pd.DataFrame([{"Alimento": n, "Carbos": c, "Unidade": u}])
            df_alimentos = pd.concat([df_alimentos, new], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "👤 Perfil":
    st.header("👤 Perfil")
    st.session_state.cor_botao = st.color_picker("Cor do App", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()