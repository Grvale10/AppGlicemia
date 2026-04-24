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

# --- 2. FUNÇÕES TÉCNICAS ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf_detalhado(df_hist, df_pacs):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pacientes_no_hist = df_hist["Paciente"].unique() if "Paciente" in df_hist.columns else ["Geral"]
    for p_nome in pacientes_no_hist:
        pdf.add_page()
        pdf.set_font("Arial", "B", 18); pdf.set_text_color(99, 102, 241)
        pdf.cell(190, 10, "Relatorio de Controle Glicemico", ln=True, align='C')
        pdf.set_font("Arial", "", 10); pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        pdf.ln(5)
        p_info = df_pacs[df_pacs["Nome"] == p_nome]
        if not p_info.empty:
            p_info = p_info.iloc[0]
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", "B", 12)
            pdf.cell(190, 10, f" Dados do Paciente: {p_nome}", ln=True, fill=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(95, 8, f"CPF: {p_info.get('CPF', '-')}"); pdf.cell(95, 8, f"Tipo Sanguineo: {p_info.get('Sangue', '-')}", ln=True)
            pdf.cell(95, 8, f"Plano: {p_info.get('Tipo_Plano', 'N/A')}"); pdf.cell(95, 8, f"Detalhes: {p_info.get('Plano', '-')}", ln=True)
            pdf.ln(5)
        pdf.set_font("Arial", "B", 10); pdf.set_fill_color(99, 102, 241); pdf.set_text_color(255, 255, 255)
        pdf.cell(30, 10, " Data/Hora", border=1, fill=True); pdf.cell(35, 10, " Momento", border=1, fill=True)
        pdf.cell(25, 10, " Glic. Pre", border=1, fill=True); pdf.cell(25, 10, " Carbos", border=1, fill=True)
        pdf.cell(25, 10, " Dose (U)", border=1, fill=True); pdf.cell(25, 10, " Glic. Pos", border=1, fill=True, ln=True)
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
        dados_p = df_hist[df_hist["Paciente"] == p_nome]
        for _, row in dados_p.iterrows():
            pdf.cell(30, 8, str(row['Data']), border=1); pdf.cell(35, 8, str(row.get('Momento', 'Refeicao')), border=1)
            pdf.cell(25, 8, f"{row['Glicemia_Pre']} mg/dL", border=1); pdf.cell(25, 8, f"{row['Carbos']}g", border=1)
            pdf.cell(25, 8, f"{row['Dose']} U", border=1)
            g_val = row.get('Glicemia_Pos', 0); pdf.cell(25, 8, f"{g_val if g_val != 0 else '-'}", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. DESIGN CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{ display: none !important; }}
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        background-color: #ffffff !important; border-radius: 12px !important;
        padding: 12px 15px !important; margin-bottom: 10px !important;
        width: 100% !important; border: 1px solid #E5E7EB !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important; font-weight: bold !important;
    }}
    .stButton>button {{
        width: 100%; border-radius: 14px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}
    .card-refeicao {{
        background-color: white; padding: 15px; border-radius: 15px;
        border: 1px solid #E5E7EB; margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS ---
def iniciar_banco():
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        for col, val in {"Carbos": 0.0, "Proteina": 0.0, "Gordura": 0.0, "Gramas": 0.0, "Unidade": "un"}.items():
            if col not in df_a.columns: df_a[col] = val
    else:
        df_a = pd.DataFrame(columns=["Alimento", "Carbos", "Proteina", "Gordura", "Gramas", "Unidade"])
    
    if os.path.exists("pacientes.csv"): df_p = pd.read_csv("pacientes.csv")
    else: df_p = pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"])

    if os.path.exists("dados_glicemia.csv"):
        df_h = pd.read_csv("dados_glicemia.csv")
        if "Glicemia_Pos" not in df_h.columns: df_h["Glicemia_Pos"] = 0
    else:
        df_h = pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 22px; color: #1F2937; margin-bottom: 25px;'>Glicemia Para Todos</h1>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("🍽️ Montar Refeição")
    if df_pacientes.empty:
        st.warning("⚠️ Cadastre um paciente primeiro.")
    else:
        with st.container():
            col_f1, col_f2 = st.columns(2)
            with col_f1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
            with col_f2: g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110)
            
            st.divider()
            
            st.subheader("➕ Adicionar Alimento")
            col_i1, col_i2 = st.columns([2, 1])
            with col_i1:
                alimento_sel = st.selectbox("Selecione o Alimento", df_alimentos["Alimento"].tolist())
                try:
                    linha_a = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel].iloc[0]
                    val_c = linha_a["Carbos"]; uni_a = linha_a["Unidade"]
                except:
                    val_c = 0.0; uni_a = "un"
            with col_i2:
                qtd = st.number_input(f"Qtd ({uni_a})", min_value=0.1, value=1.0)
            
            if st.button("➕ Adicionar à Refeição"):
                st.session_state.sacola_refeicao.append({
                    "Alimento": alimento_sel,
                    "Qtd": qtd,
                    "Carbos": round(float(val_c) * qtd, 1),
                    "Unidade": uni_a
                })
                st.rerun()

            if st.session_state.sacola_refeicao:
                st.markdown("### 📋 No seu prato:")
                total_c_refeicao = 0.0
                for i, item in enumerate(st.session_state.sacola_refeicao):
                    with st.container():
                        st.markdown(f"""
                        <div class="card-refeicao">
                            <b>{item['Alimento']}</b><br>
                            {item['Qtd']} {item['Unidade']} - {item['Carbos']}g de carbo
                        </div>
                        """, unsafe_allow_html=True)
                        total_c_refeicao += item['Carbos']
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🗑️ Limpar Prato"):
                        st.session_state.sacola_refeicao = []
                        st.rerun()
                with col_btn2:
                    st.metric("Total Carbos", f"{round(total_c_refeicao, 1)}g")

                if st.button("💉 Calcular e Salvar Refeição"):
                    dose = calcular_insulina(g_pre, 100, 50, total_c_refeicao, 15)
                    itens_str = " + ".join([f"{i['Alimento']} ({i['Qtd']}{i['Unidade']})" for i in st.session_state.sacola_refeicao])
                    
                    novo = pd.DataFrame([{
                        "Data": datetime.now().strftime("%d/%m %H:%M"),
                        "Paciente": pac_sel,
                        "Glicemia_Pre": g_pre,
                        "Carbos": round(total_c_refeicao, 1),
                        "Dose": dose,
                        "Momento": itens_str[:50] + "...", 
                        "Glicemia_Pos": 0
                    }])
                    df_historico = pd.concat([df_historico, novo], ignore_index=True)
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.session_state.sacola_refeicao = []
                    st.success(f"Dose sugerida: {dose} U")
                    st.balloons()

elif aba == "👥 Pacientes":
    st.header("👥 Gestão de Pacientes")
    aba_p = st.tabs(["➕ Adicionar", "✏️ Editar/Remover"])
    lista_tipos_sangue = ["Não Sei", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    lista_planos = ["Particular", "SUS", "Outro"]
    with aba_p[0]:
        with st.form("add_pac"):
            c1, c2 = st.columns(2)
            with c1: 
                n = st.text_input("Nome")
                p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"])
                cp = st.text_input("CPF")
            with c2: 
                s = st.selectbox("Tipo Sanguíneo", lista_tipos_sangue)
                tp_plano = st.selectbox("Plano de Saúde", lista_planos)
                # Termo (Opcional) recolocado conforme solicitado
                detalhe_plano = st.text_input("Dados do Plano (Opcional)")
            if st.form_submit_button("Cadastrar"):
                if n:
                    np = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s, "Plano": detalhe_plano, "Tipo_Plano": tp_plano, "SUS": ""}])
                    df_pacientes = pd.concat([df_pacientes, np], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()
    with aba_p[1]:
        if not df_pacientes.empty:
            edit_p = st.selectbox("Selecionar Paciente", df_pacientes["Nome"].tolist())
            idx = df_pacientes.index[df_pacientes["Nome"] == edit_p][0]
            if st.button("🗑️ Remover Paciente"): df_pacientes = df_pacientes.drop(idx); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    if not df_historico.empty:
        pac_filtro = st.multiselect("Filtrar por Paciente", df_historico["Paciente"].unique(), default=df_historico["Paciente"].unique())
        df_filtrado = df_historico[df_historico["Paciente"].isin(pac_filtro)]
        st.dataframe(df_filtrado, use_container_width=True)
        pdf_data = gerar_pdf_detalhado(df_filtrado, df_pacientes)
        st.download_button("📥 Baixar PDF", data=pdf_data, file_name=f"Relatorio_{datetime.now().strftime('%d_%m')}.pdf", mime="application/pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardápio Detalhado")
    with st.form("novo_alimento_detalhado", clear_on_submit=True):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            n_a = st.text_input("Nome do Alimento"); u_a = st.text_input("Unidade (Ex: colher, ml)"); g_a = st.number_input("Peso (g)", min_value=0.0)
        with col_a2:
            c_a = st.number_input("Carbos (g)", min_value=0.0); p_a = st.number_input("Proteína (g)", min_value=0.0); f_a = st.number_input("Gordura (g)", min_value=0.0)
        if st.form_submit_button("Salvar no Cardápio"):
            if n_a:
                novo_item = pd.DataFrame([{"Alimento": n_a, "Carbos": c_a, "Proteina": p_a, "Gordura": f_a, "Gramas": g_a, "Unidade": u_a}])
                df_alimentos = pd.concat([df_alimentos, novo_item], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    df_ed = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Alterações"): df_ed.to_csv("alimentos.csv", index=False); st.success("Atualizado!")

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Refeição")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Paciente']} - {row['Data']}"):
                v_pos = st.number_input("Valor 2h após", key=f"p_{idx}")
                if st.button("Confirmar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()

elif aba == "👤 Perfil":
    st.header("👤 Configurações")
    with st.expander("🎨 Aparência"):
        st.session_state.cor_botao = st.color_picker("Cor Principal", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()