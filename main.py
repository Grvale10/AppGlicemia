import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

st.set_page_config(page_title="BioCare Kids", layout="wide")

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
        background-color: #F3F4F6 !important; border-radius: 12px !important;
        padding: 12px 15px !important; margin-bottom: 8px !important;
        width: 100% !important; display: flex !important;
        justify-content: center !important; align-items: center !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label p {{
        color: #1F2937 !important; font-size: 16px !important; margin: 0px !important;
    }}
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{ display: none !important; }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
        background-color: {st.session_state.cor_botao} !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: white !important; font-weight: bold !important;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: bold; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. BANCO DE DADOS (PROTEÇÃO TOTAL) ---
def iniciar_banco():
    # Carregar Alimentos
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame({"Alimento": ["Pão", "Arroz"], "Carbos": [28.0, 15.0]})
    
    # Carregar Pacientes
    if os.path.exists("pacientes.csv"):
        df_p = pd.read_csv("pacientes.csv")
        df_p.columns = df_p.columns.str.strip()
        for col in ["CPF", "SUS", "Plano", "Sangue"]:
            if col not in df_p.columns: df_p[col] = ""
        df_p = df_p.fillna("")
    else:
        df_p = pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue"])

    # Carregar Histórico (Aqui mora o perigo do KeyError)
    if os.path.exists("dados_glicemia.csv"):
        df_h = pd.read_csv("dados_glicemia.csv")
        df_h.columns = df_h.columns.str.strip() # Remove espaços invisíveis
        # FORÇA A CRIAÇÃO SE NÃO EXISTIR
        if "Glicemia_Pos" not in df_h.columns:
            df_h["Glicemia_Pos"] = 0
        if "Paciente" not in df_h.columns:
            df_h["Paciente"] = "Geral"
    else:
        df_h = pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 24px; color: #1F2937; margin-bottom: 25px;'>Menu</h1>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("📝 Registrar Refeição")
    if df_pacientes.empty:
        st.warning("⚠️ Cadastre um paciente na aba 'Pacientes' primeiro.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
            g_pre = st.number_input("Glicemia Atual (mg/dL)", min_value=20, value=110, help="Valor medido antes da refeição.")
            momento = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche"])
        with col2:
            alimento_sel = st.selectbox("Alimento", df_alimentos["Alimento"].tolist())
            val_c = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0] if alimento_sel in df_alimentos["Alimento"].values else 0.0
            qtd = st.number_input("Quantidade", min_value=0.1, value=1.0, help="Quantidade/porção consumida.")
            total_c = round(float(val_c) * qtd, 1)
            st.info(f"Carboidratos: {total_c}g")

        if st.button("Calcular e Salvar"):
            dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": total_c, "Dose": dose, "Momento": momento, "Glicemia_Pos": 0}])
            df_historico = pd.concat([df_historico, novo], ignore_index=True)
            df_historico.to_csv("dados_glicemia.csv", index=False)
            st.success(f"Salvo! Dose: {dose} U.")

elif aba == "👥 Pacientes":
    st.header("👥 Gestão de Pacientes")
    aba_p = st.tabs(["➕ Adicionar", "✏️ Editar/Remover"])
    
    with aba_p[0]:
        with st.form("form_add"):
            c1, c2 = st.columns(2)
            with c1:
                n = st.text_input("Nome Completo")
                p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"])
                c = st.text_input("CPF")
            with c2:
                s = st.text_input("Cartão SUS")
                pl = st.text_input("Plano de Saúde")
                sg = st.selectbox("Sangue", ["Não Sei", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            if st.form_submit_button("Cadastrar"):
                if n:
                    novo_p = pd.DataFrame([{"Nome": n, "Parentesco": p, "CPF": c, "SUS": s, "Plano": pl, "Sangue": sg}])
                    df_pacientes = pd.concat([df_pacientes, novo_p], ignore_index=True)
                    df_pacientes.to_csv("pacientes.csv", index=False)
                    st.success("Salvo!"); st.rerun()
                else: st.error("Nome é obrigatório.")

    with aba_p[1]:
        if not df_pacientes.empty:
            edit_p = st.selectbox("Paciente para alterar", df_pacientes["Nome"].tolist())
            idx = df_pacientes.index[df_pacientes["Nome"] == edit_p][0]
            
            # Listas para os selects (evita o ValueError)
            l_p = ["Filho", "Filha", "Cônjuge", "Outro"]
            l_s = ["Não Sei", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            
            # Dados atuais com segurança
            curr_p = df_pacientes.at[idx, "Parentesco"]
            curr_s = df_pacientes.at[idx, "Sangue"]
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                n_n = st.text_input("Nome", value=df_pacientes.at[idx, "Nome"])
                n_p = st.selectbox("Parentesco", l_p, index=l_p.index(curr_p) if curr_p in l_p else 0)
                n_c = st.text_input("CPF", value=df_pacientes.at[idx, "CPF"])
            with c2:
                n_s = st.text_input("SUS", value=df_pacientes.at[idx, "SUS"])
                n_pl = st.text_input("Plano", value=df_pacientes.at[idx, "Plano"])
                n_sg = st.selectbox("Sangue", l_s, index=l_s.index(curr_s) if curr_s in l_s else 0)
            
            cb1, cb2 = st.columns(2)
            with cb1:
                if st.button("💾 Salvar Alterações"):
                    df_pacientes.loc[idx] = [n_n, n_p, n_c, n_s, n_pl, n_sg]
                    df_pacientes.to_csv("pacientes.csv", index=False); st.success("Atualizado!"); st.rerun()
            with cb2:
                if st.button("🗑️ Remover"):
                    df_pacientes = df_pacientes.drop(idx)
                    df_pacientes.to_csv("pacientes.csv", index=False); st.warning("Removido!"); st.rerun()
        else:
            st.info("Nenhum paciente cadastrado.")

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia Pós-Refeição")
    # A verificação de segurança agora está lá no iniciar_banco()
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row.get('Paciente', 'Geral')} - {row['Momento']} ({row['Data']})"):
                v_pos = st.number_input("Valor 2h após", key=f"p_{idx}", help="Meça a glicemia 2 horas após a refeição.")
                if st.button("Salvar Medição", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False); st.rerun()
    else: st.info("Nada pendente.")

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("Baixar PDF", data=gerar_pdf(df_historico), file_name="historico.pdf")

elif aba == "🍎 Alimentos":
    st.header("🍎 Alimentos")
    df_n = st.data_editor(df_alimentos, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alimentos"):
        df_n.to_csv("alimentos.csv", index=False); st.success("Salvo!")

elif aba == "👤 Perfil":
    st.header("👤 Personalização")
    with st.expander("🎨 Temas"):
        st.session_state.cor_fundo = st.color_picker("Fundo", st.session_state.cor_fundo)
        st.session_state.cor_botao = st.color_picker("Botões", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()