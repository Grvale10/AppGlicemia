import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []
if "selecionados_pdf" not in st.session_state: st.session_state.selecionados_pdf = set()

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

# --- 2. FUNÇÕES TÉCNICAS ---
def gerar_pdf_detalhado(df_selecionado, df_pacs):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pacientes_no_hist = df_selecionado["Paciente"].unique()
    for p_nome in pacientes_no_hist:
        pdf.add_page()
        pdf.set_font("Arial", "B", 20); pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 15, f"Relatorio de Controle Glicemico - {p_nome}", ln=True, align='C')
        pdf.ln(5)
        w = {"data": 35, "refeicao": 65, "pre": 35, "carbo": 35, "dose": 30, "pos": 35}
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        pdf.cell(w["data"], 10, " Data/Hora", border=1, fill=True, align='C')
        pdf.cell(w["refeicao"], 10, " Detalhes", border=1, fill=True, align='C')
        pdf.cell(w["pre"], 10, " Pre", border=1, fill=True, align='C')
        pdf.cell(w["carbo"], 10, " Carbos", border=1, fill=True, align='C')
        pdf.cell(w["dose"], 10, " Dose", border=1, fill=True, align='C')
        pdf.cell(w["pos"], 10, " Pos", border=1, fill=True, align='C', ln=True)
        pdf.set_font("Arial", "", 9); pdf.set_text_color(0, 0, 0)
        zebra = False
        for _, row in df_selecionado[df_selecionado["Paciente"] == p_nome].iterrows():
            pdf.set_fill_color(245, 245, 245) if zebra else pdf.set_fill_color(255, 255, 255)
            pdf.cell(w["data"], 9, f" {row['Data']}", border=1, fill=True)
            pdf.cell(w["refeicao"], 9, f" {str(row.get('Momento', ''))[:40]}", border=1, fill=True)
            pdf.cell(w["pre"], 9, f"{row['Glicemia_Pre']}", border=1, fill=True, align='C')
            pdf.cell(w["carbo"], 9, f"{row['Carbos']}", border=1, fill=True, align='C')
            pdf.cell(w["dose"], 9, f"{row['Dose']}", border=1, fill=True, align='C')
            g_v = row.get('Glicemia_Pos', 0)
            pdf.cell(w["pos"], 9, f"{g_v}" if g_v != 0 else "-", border=1, fill=True, align='C', ln=True)
            zebra = not zebra
    return bytes(pdf.output())

# --- 3. DESIGN CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background-color: {st.session_state.cor_botao} !important; color: white !important; }}
    .card-refeicao {{ background-color: white; padding: 10px; border-radius: 10px; border: 1px solid #E5E7EB; margin-bottom: 5px; }}
    .tabela-hist {{ background-color: white; border-radius: 15px; padding: 20px; border: 1px solid #E5E7EB; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS ---
def iniciar_banco():
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carbos", "Proteina", "Gordura", "Gramas", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>Glicemia Para Todos</h3>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---
if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty: st.warning("Cadastre um paciente.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: refeicao_tipo = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia", "Pré-Treino", "Outro"])
        with c3: g_pre = st.number_input("Glicemia Pré (mg/dL)", min_value=20, value=110)
        st.divider()
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            alimento_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
            try: lin = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel].iloc[0]; val_c = lin["Carbos"]; uni_a = lin["Unidade"]
            except: val_c = 0.0; uni_a = "un"
        with col_i2: qtd = st.number_input(f"Qtd ({uni_a})", min_value=0.1, value=1.0)
        if st.button("➕ Adicionar"):
            st.session_state.sacola_refeicao.append({"Alimento": alimento_sel, "Qtd": qtd, "Carbos": round(float(val_c) * qtd, 1), "Unidade": uni_a})
            st.rerun()
        if st.session_state.sacola_refeicao:
            total_c = sum(i['Carbos'] for i in st.session_state.sacola_refeicao)
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                it_c, dl_c = st.columns([6, 1])
                with it_c: st.markdown(f"""<div class="card-refeicao"><b>{item['Alimento']}</b> ({item['Qtd']} {item['Unidade']})</div>""", unsafe_allow_html=True)
                with dl_c: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            if st.button("💉 Salvar Registro"):
                dose = round(max(0, (g_pre - 100) / 50) + (total_c / 15), 1)
                detalhe = " + ".join([f"{i['Alimento']}" for i in st.session_state.sacola_refeicao])
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": round(total_c, 1), "Dose": dose, "Momento": detalhe, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Salvo! Dose: {dose} U"); st.rerun()

elif aba == "📊 Histórico":
    st.header("📊 Histórico de Medições")
    if not df_historico.empty:
        st.write("Selecione os itens para o PDF clicando em **Incluir**:")
        
        # --- TABELA DE HISTÓRICO COM BOTÕES LATERAIS (SEM DATA_EDITOR) ---
        for idx, row in df_historico.sort_index(ascending=False).iterrows():
            col_check, col_data, col_pac, col_mom, col_dose = st.columns([1, 2, 2, 4, 1])
            
            is_sel = idx in st.session_state.selecionados_pdf
            label_btn = "✅" if is_sel else "Incluir"
            
            with col_check:
                if st.button(label_btn, key=f"check_{idx}"):
                    if is_sel: st.session_state.selecionados_pdf.remove(idx)
                    else: st.session_state.selecionados_pdf.add(idx)
                    st.rerun()
            
            with col_data: st.write(row['Data'])
            with col_pac: st.write(row['Paciente'])
            with col_mom: st.write(str(row['Momento'])[:50])
            with col_dose: st.write(f"{row['Dose']}U")
            st.divider()

        # Botões de Ação
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("🗑️ Limpar Seleção"): st.session_state.selecionados_pdf = set(); st.rerun()
        with c_p2:
            if st.session_state.selecionados_pdf:
                df_selecionado = df_historico.loc[list(st.session_state.selecionados_pdf)]
                pdf_bytes = gerar_pdf_detalhado(df_selecionado, df_pacientes)
                st.download_button("📥 Baixar PDF Selecionado", data=pdf_bytes, file_name="Relatorio.pdf", mime="application/pdf")
    else:
        st.info("Nenhum dado registrado.")

# Outras abas mantidas...
elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("add_p"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Nome"); p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"])
        with c2: cp = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Não Sei"])
        if st.form_submit_button("Salvar"):
            if n:
                np = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s}])
                df_pacientes = pd.concat([df_pacientes, np], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    if not df_pacientes.empty: st.dataframe(df_pacientes, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    with st.form("add_a"):
        n_a = st.text_input("Nome"); c_a = st.number_input("Carbos"); u_a = st.text_input("Unidade")
        if st.form_submit_button("Salvar Alimento"):
            ni = pd.DataFrame([{"Alimento": n_a, "Carbos": c_a, "Unidade": u_a}])
            df_alimentos = pd.concat([df_alimentos, ni], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} ({r['Data']})"):
            v = st.number_input("Valor Pós", key=f"v_{idx}")
            if st.button("Confirmar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.header("👤 Ajustes")
    st.session_state.cor_botao = st.color_picker("Cor Principal", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()