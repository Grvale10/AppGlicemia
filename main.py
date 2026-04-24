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

# --- 2. FUNÇÃO PDF ---
def gerar_pdf_detalhado(df_selecionado, df_pacs):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pacientes_no_hist = df_selecionado["Paciente"].unique()
    for p_nome in pacientes_no_hist:
        pdf.add_page()
        pdf.set_font("Arial", "B", 18); pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 15, f"Relatorio de Controle Glicemico - {p_nome}", ln=True, align='C')
        pdf.ln(5)
        w = {"data": 35, "refeicao": 70, "pre": 30, "carbo": 30, "dose": 30, "pos": 30}
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        cols = ["Data/Hora", "Detalhes", "Pre", "Carbos", "Dose", "Pos"]
        for i, header in enumerate(cols):
            pdf.cell(list(w.values())[i], 10, f" {header}", border=1, fill=True, align='C')
        pdf.ln()
        pdf.set_font("Arial", "", 9); pdf.set_text_color(0, 0, 0)
        zebra = False
        for _, row in df_selecionado[df_selecionado["Paciente"] == p_nome].iterrows():
            pdf.set_fill_color(230, 230, 230) if zebra else pdf.set_fill_color(255, 255, 255)
            pdf.cell(w["data"], 9, f" {row['Data']}", border=1, fill=True)
            pdf.cell(w["refeicao"], 9, f" {str(row['Momento'])[:45]}", border=1, fill=True)
            pdf.cell(w["pre"], 9, f"{row['Glicemia_Pre']}", border=1, fill=True, align='C')
            pdf.cell(w["carbo"], 9, f"{row['Carbos']}", border=1, fill=True, align='C')
            pdf.cell(w["dose"], 9, f"{row['Dose']}", border=1, fill=True, align='C')
            g_v = row.get('Glicemia_Pos', 0)
            pdf.cell(w["pos"], 9, f"{g_v}" if g_v != 0 else "-", border=1, fill=True, align='C', ln=True)
            zebra = not zebra
    return bytes(pdf.output())

# --- 3. DESIGN CSS (TRAVA REFORÇADA) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background-color: {st.session_state.cor_botao} !important; color: white !important; font-weight: bold; height: 45px; }}
    /* ESTA REGRA MATA O NONE NA RAIZ */
    [data-testid="stNotification"] {{ display: none !important; }}
    div.element-container:has(p:contains("None")) {{ display: none !important; }}
    .card-refeicao {{ background-color: white; padding: 10px; border-radius: 10px; border: 1px solid #E5E7EB; margin-bottom: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS ---
def iniciar_banco():
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carbos", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Controle Glicêmico</h2>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---
if aba == "🏠 Início":
    st.header("🍽️ Nova Refeição")
    if df_pacientes.empty: st.warning("Cadastre um paciente.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with c2: mom = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Ceia", "Outro"])
        with c3: gpre = st.number_input("Glicemia Pré", value=110)
        
        st.divider()
        ca1, ca2 = st.columns([3, 1])
        with ca1: ali = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
        with ca2: qtd = st.number_input("Qtd", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar"):
            c_val = df_alimentos.loc[df_alimentos["Alimento"] == ali, "Carbos"].values[0]
            u_val = df_alimentos.loc[df_alimentos["Alimento"] == ali, "Unidade"].values[0]
            st.session_state.sacola_refeicao.append({"A": ali, "Q": qtd, "C": round(c_val * qtd, 1), "U": u_val})
            st.rerun()

        if st.session_state.sacola_refeicao:
            total = sum(i['C'] for i in st.session_state.sacola_refeicao)
            for idx, i in enumerate(st.session_state.sacola_refeicao):
                col_i, col_d = st.columns([6, 1])
                with col_i: st.markdown(f'<div class="card-refeicao">{i["A"]} - {i["Q"]} {i["U"]}</div>', unsafe_allow_html=True)
                with col_d: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            if st.button("💉 Salvar Registro"):
                dose = round(max(0, (gpre - 100)/50) + (total/15), 1)
                detalhe = " + ".join([f"{x['A']} ({x['Q']}{x['U']})" for x in st.session_state.sacola_refeicao])
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac, "Glicemia_Pre": gpre, "Carbos": total, "Dose": dose, "Momento": detalhe, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success("Salvo!"); st.rerun()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        df_edit = df_historico.copy()
        df_edit.insert(0, "Sel", False)
        
        # O SEGREDO: Capturar o retorno em uma variável e não fazer nada com ela na interface principal
        tabela_placeholder = st.empty()
        with tabela_placeholder.container():
            df_final = st.data_editor(
                df_edit,
                column_config={"Sel": st.column_config.CheckboxColumn("PDF", default=False)},
                disabled=[c for c in df_edit.columns if c != "Sel"],
                hide_index=True, use_container_width=True, key="editor_pc_final"
            )
        
        sel_rows = df_final[df_final["Sel"] == True]
        if not sel_rows.empty:
            pdf = gerar_pdf_detalhado(sel_rows.drop(columns=["Sel"]), df_pacientes)
            st.download_button(f"📥 Baixar PDF ({len(sel_rows)} itens)", pdf, "Relatorio.pdf", "application/pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardápio")
    with st.form("a"):
        n, c, u = st.columns(3)
        name = n.text_input("Nome"); carb = c.number_input("Carbos"); unit = u.text_input("Unidade")
        if st.form_submit_button("Salvar"):
            new = pd.DataFrame([{"Alimento": name, "Carbos": carb, "Unidade": unit}])
            df_alimentos = pd.concat([df_alimentos, new], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

# (Demais abas simplificadas para manter performance)
elif aba == "👥 Pacientes":
    name = st.text_input("Nome Paciente")
    if st.button("Salvar"):
        new = pd.DataFrame([{"Nome": name, "Parentesco": "Dependente"}])
        df_pacientes = pd.concat([df_pacientes, new], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

elif aba == "📌 Pendentes":
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} - {r['Data']}"):
            v = st.number_input("Valor Pós", key=idx)
            if st.button("Confirmar", key=f"b{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.session_state.cor_botao = st.color_picker("Cor", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()