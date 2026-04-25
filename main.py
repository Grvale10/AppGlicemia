import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

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
        pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='R')
        pdf.ln(5)
        
        p_info = df_pacs[df_pacs["Nome"] == p_nome]
        if not p_info.empty:
            p_info = p_info.iloc[0]
            pdf.set_fill_color(245, 247, 255); pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 10, "  Informações do Paciente", ln=True, fill=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(70, 8, f" CPF: {p_info.get('CPF', '-')}")
            pdf.cell(70, 8, f" Sangue: {p_info.get('Sangue', '-')}")
            pdf.cell(0, 8, f" Plano: {p_info.get('Tipo_Plano', 'N/A')}", ln=True)
            pdf.ln(5)
            
        w = {"data": 35, "refeicao": 55, "pre": 40, "carbo": 35, "dose": 30, "pos": 40}
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        pdf.cell(w["data"], 10, " Data/Hora", border=1, fill=True, align='C')
        pdf.cell(w["refeicao"], 10, " Tipo de Refeição", border=1, fill=True, align='C')
        pdf.cell(w["pre"], 10, " Glicemia Pré", border=1, fill=True, align='C')
        pdf.cell(w["carbo"], 10, " Carboidratos", border=1, fill=True, align='C')
        pdf.cell(w["dose"], 10, " Dose (U)", border=1, fill=True, align='C')
        pdf.cell(w["pos"], 10, " Glicemia Pós", border=1, fill=True, align='C', ln=True)
        
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        dados_p = df_selecionado[df_selecionado["Paciente"] == p_nome]
        zebra = False
        for _, row in dados_p.iterrows():
            pdf.set_fill_color(245, 245, 245) if zebra else pdf.set_fill_color(255, 255, 255)
            pdf.cell(w["data"], 9, f" {row['Data']}", border=1, fill=True)
            pdf.cell(w["refeicao"], 9, f" {row.get('Momento', 'Outro')}", border=1, fill=True)
            pdf.cell(w["pre"], 9, f"{row['Glicemia_Pre']} mg/dL", border=1, fill=True, align='C')
            pdf.cell(w["carbo"], 9, f"{row['Carbos']}g", border=1, fill=True, align='C')
            pdf.cell(w["dose"], 9, f"{row['Dose']} U", border=1, fill=True, align='C')
            g_v = row.get('Glicemia_Pos', 0)
            pdf.cell(w["pos"], 9, f"{g_v} mg/dL" if g_v != 0 else "Pendente", border=1, fill=True, align='C', ln=True)
            zebra = not zebra
            
    try: return bytes(pdf.output())
    except: return pdf.output(dest='S').encode('latin-1')

# --- 3. DESIGN CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    .stButton>button {{ width: 100%; border-radius: 14px; background-color: {st.session_state.cor_botao} !important; color: white !important; font-weight: bold; border: none; }}
    .card-refeicao {{ background-color: white; padding: 15px; border-radius: 15px; border: 1px solid #E5E7EB; margin-bottom: 5px; }}
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
    st.markdown("<h1 style='text-align: center; font-size: 22px;'>Glicemia Para Todos</h1>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty:
        st.warning("⚠️ Cadastre um paciente primeiro.")
    else:
        with st.container():
            c1, c2, c3 = st.columns(3)
            with c1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
            with c2: refeicao_tipo = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia", "Outro"])
            with c3: g_pre = st.number_input("Glicemia Pré (mg/dL)", min_value=20, value=110)
            
            st.divider()
            col_i1, col_i2 = st.columns([3, 1])
            with col_i1:
                alimento_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
                try:
                    lin = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel].iloc[0]
                    val_c = lin["Carbos"]; uni_a = lin["Unidade"]
                except: val_c = 0.0; uni_a = "un"
            with col_i2: qtd = st.number_input(f"Qtd ({uni_a})", min_value=0.1, value=1.0)
            
            if st.button("➕ Adicionar ao Prato"):
                st.session_state.sacola_refeicao.append({"Alimento": alimento_sel, "Qtd": qtd, "Carbos": round(float(val_c) * qtd, 1), "Unidade": uni_a})
                st.rerun()

            if st.session_state.sacola_refeicao:
                st.markdown(f"### 📋 Prato: {refeicao_tipo}")
                total_c = 0.0
                for idx, item in enumerate(st.session_state.sacola_refeicao):
                    it_c, dl_c = st.columns([6, 1])
                    with it_c:
                        st.markdown(f"""<div class="card-refeicao"><b>{item['Alimento']}</b> | {item['Qtd']} {item['Unidade']} ({item['Carbos']}g)</div>""", unsafe_allow_html=True)
                        total_c += item['Carbos']
                    with dl_c:
                        if st.button("🗑️", key=f"del_{idx}"):
                            st.session_state.sacola_refeicao.pop(idx); st.rerun()
                
                st.metric("Total Carboidratos", f"{round(total_c, 1)}g")
                if st.button("💉 Calcular e Salvar"):
                    dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
                    novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": round(total_c, 1), "Dose": dose, "Momento": refeicao_tipo, "Glicemia_Pos": 0}])
                    df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.session_state.sacola_refeicao = []; st.success(f"Dose: {dose} U"); st.balloons()

elif aba == "📊 Histórico":
    st.header("📊 Histórico e Exportação")
    if not df_historico.empty:
        st.write("Marque na coluna **Download?** os itens que deseja no PDF:")
        df_com_selecao = df_historico.copy()
        df_com_selecao.insert(0, "Selecionar", False)
        
        st.data_editor(
            df_com_selecao,
            column_config={
                "Selecionar": st.column_config.CheckboxColumn("Download?", default=False)
            },
            disabled=[col for col in df_com_selecao.columns if col != "Selecionar"],
            hide_index=True,
            use_container_width=True,
        )
        # Nota: Na 8.1 original, a lógica de exportação dependia da seleção acima.

elif aba == "👥 Pacientes":
    st.header("👥 Pacientes")
    with st.form("p_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Nome"); p = st.selectbox("Parentesco", ["Filho", "Filha", "Outro"])
        with c2: cp = st.text_input("CPF"); s = st.selectbox("Sangue", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        if st.form_submit_button("Salvar"):
            new_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s}])
            df_pacientes = pd.concat([df_pacientes, new_p], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    st.dataframe(df_pacientes, use_container_width=True)

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    with st.form("a_f"):
        n_a = st.text_input("Nome"); c_a = st.number_input("Carbos"); u_a = st.text_input("Unidade")
        if st.form_submit_button("Salvar"):
            new_a = pd.DataFrame([{"Alimento": n_a, "Carbos": c_a, "Unidade": u_a}])
            df_alimentos = pd.concat([df_alimentos, new_a], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    st.dataframe(df_alimentos, use_container_width=True)

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós")
    pend = df_historico[df_historico["Glicemia_Pos"] == 0]
    for idx, r in pend.iterrows():
        with st.expander(f"{r['Paciente']} ({r['Data']})"):
            v = st.number_input("Valor Pós", key=f"v_{idx}")
            if st.button("Salvar", key=f"b_{idx}"):
                df_historico.at[idx, "Glicemia_Pos"] = v; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.header("👤 Ajustes")
    st.session_state.cor_botao = st.color_picker("Cor Principal", st.session_state.cor_botao)
    if st.button("Salvar"): st.rerun()