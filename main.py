import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

st.set_page_config(page_title="Glicemia Para Todos", layout="wide")

# --- 2. FUNÇÕES TÉCNICAS ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Glicemia", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        paciente = row.get('Paciente', 'Geral')
        texto = f"{row['Data']} | {paciente} | Glic: {row['Glicemia_Pre']} | Dose: {row['Dose']} U"
        pdf.cell(190, 8, texto.encode('latin-1', 'replace').decode('latin-1'), ln=True)
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
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05) !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
        border: 1px solid {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important; font-weight: bold !important;
    }}

    .stForm {{
        background-color: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.02) !important;
    }}

    .stButton>button {{
        width: 100%; border-radius: 14px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0px 4px 12px rgba(99, 102, 241, 0.3);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS ---
def iniciar_banco():
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        df_a.columns = df_a.columns.str.strip()
        if "Carbos" not in df_a.columns:
            if "Carboidratos" in df_a.columns: df_a = df_a.rename(columns={"Carboidratos": "Carbos"})
            else: df_a["Carbos"] = 0.0
    else:
        df_a = pd.DataFrame({"Alimento": ["Pão", "Arroz"], "Carbos": [28.0, 15.0]})
    
    if os.path.exists("pacientes.csv"):
        df_p = pd.read_csv("pacientes.csv")
        df_p.columns = df_p.columns.str.strip()
        for col in ["CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"]:
            if col not in df_p.columns: df_p[col] = ""
        df_p = df_p.fillna("")
    else:
        df_p = pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"])

    if os.path.exists("dados_glicemia.csv"):
        df_h = pd.read_csv("dados_glicemia.csv")
        df_h.columns = df_h.columns.str.strip()
        if "Glicemia_Pos" not in df_h.columns: df_h["Glicemia_Pos"] = 0
        if "Paciente" not in df_h.columns: df_h["Paciente"] = "Geral"
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
    st.header("📝 Nova Refeição")
    if df_pacientes.empty:
        st.warning("⚠️ Cadastre um paciente primeiro.")
    else:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                pac_sel = st.selectbox("Quem vai comer?", df_pacientes["Nome"].tolist())
                g_pre = st.number_input("Glicemia Atual", min_value=20, value=110)
            with col2:
                alimento_sel = st.selectbox("O que vai comer?", df_alimentos["Alimento"].tolist())
                try:
                    val_c = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0]
                except:
                    val_c = 0.0
                qtd = st.number_input("Porção", min_value=0.1, value=1.0)
            
            total_c = round(float(val_c) * qtd, 1)
            st.metric("Total de Carboidratos", f"{total_c}g")

            if st.button("Calcular Dose"):
                dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": total_c, "Dose": dose, "Momento": "Refeição", "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.success(f"Dose sugerida: {dose} U")

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
                # Alteração: Plano virou selectbox
                tp_plano = st.selectbox("Plano de Saúde", lista_planos)
                # Campo condicional para dados do plano
                detalhe_plano = st.text_input("Dados do Plano (Opcional)", placeholder="Ex: Unimed, Bradesco...")
            
            if st.form_submit_button("Cadastrar"):
                if n:
                    np = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": cp, "Sangue": s, "Plano": detalhe_plano, "Tipo_Plano": tp_plano, "SUS": ""}])
                    df_pacientes = pd.concat([df_pacientes, np], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()

    with aba_p[1]:
        if not df_pacientes.empty:
            edit_p = st.selectbox("Selecionar Paciente", df_pacientes["Nome"].tolist())
            idx = df_pacientes.index[df_pacientes["Nome"] == edit_p][0]
            
            curr_s = df_pacientes.at[idx, "Sangue"]
            curr_tp = df_pacientes.at[idx, "Tipo_Plano"] if "Tipo_Plano" in df_pacientes.columns else "Particular"
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                n_n = st.text_input("Nome", value=df_pacientes.at[idx, "Nome"])
                n_p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"], index=0) # Index simplificado para o diff
                n_c = st.text_input("CPF", value=df_pacientes.at[idx, "CPF"])
            with c2:
                n_sg = st.selectbox("Tipo Sanguíneo", lista_tipos_sangue, index=lista_tipos_sangue.index(curr_s) if curr_s in lista_tipos_sangue else 0)
                n_tp = st.selectbox("Plano", lista_planos, index=lista_planos.index(curr_tp) if curr_tp in lista_planos else 0)
                n_pl = st.text_input("Dados do Plano", value=df_pacientes.at[idx, "Plano"])
            
            if st.button("💾 Salvar Alterações"):
                df_pacientes.at[idx, "Nome"] = n_n
                df_pacientes.at[idx, "Sangue"] = n_sg
                df_pacientes.at[idx, "Tipo_Plano"] = n_tp
                df_pacientes.at[idx, "Plano"] = n_pl
                df_pacientes.at[idx, "CPF"] = n_c
                df_pacientes.to_csv("pacientes.csv", index=False); st.success("Atualizado!"); st.rerun()

            if st.button("🗑️ Remover Paciente"):
                df_pacientes = df_pacientes.drop(idx); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()

# --- Outras abas permanecem inalteradas conforme Código Base ---
elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Refeição")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row.get('Paciente', 'Geral')} - ({row['Data']})"):
                v_pos = st.number_input("Valor 2h após", key=f"p_{idx}")
                if st.button("Confirmar", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos; df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()
    else: st.info("Nada pendente.")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 Baixar PDF", data=gerar_pdf(df_historico), file_name="relatorio.pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardápio")
    with st.form("novo_alimento", clear_on_submit=True):
        st.subheader("➕ Novo Alimento")
        c1, c2 = st.columns([2, 1])
        with c1: n_a = st.text_input("Nome do Alimento")
        with c2: c_a = st.number_input("Carbos (por 1 un/dose)", min_value=0.0, step=0.1)
        if st.form_submit_button("Salvar na Lista"):
            if n_a:
                ni = pd.DataFrame([{"Alimento": n_a, "Carbos": c_a}])
                df_alimentos = pd.concat([df_alimentos, ni], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()
    
    st.divider()
    df_ed = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Atualizar Tabela"):
        df_ed.to_csv("alimentos.csv", index=False); st.success("Atualizado!")

elif aba == "👤 Perfil":
    st.header("👤 Configurações")
    with st.expander("🎨 Aparência"):
        st.session_state.cor_botao = st.color_picker("Cor Principal", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()