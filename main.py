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

# --- 3. DESIGN CSS (ATUALIZADO PARA MODERNIDADE) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{ display: none !important; }}
    
    /* Menu Lateral Moderno */
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

    /* Estilização dos Cards de Entrada */
    .stForm {{
        background-color: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.02) !important;
    }}

    /* Botões */
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
        if "Carbos" not in df_a.columns: df_a["Carbos"] = 0.0
    else:
        df_a = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco"], "Carbos": [28.0, 15.0]})
    
    if os.path.exists("pacientes.csv"):
        df_p = pd.read_csv("pacientes.csv")
    else:
        df_p = pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue"])

    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 24px; color: #1F2937; margin-bottom: 25px;'>BioCare Kids</h1>", unsafe_allow_html=True)
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
                g_pre = st.number_input("Glicemia Atual", min_value=20, value=110, help="Valor do glicômetro.")
            with col2:
                alimento_sel = st.selectbox("O que vai comer?", df_alimentos["Alimento"].tolist())
                val_c = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel, "Carbos"].values[0] if alimento_sel in df_alimentos["Alimento"].values else 0.0
                qtd = st.number_input("Porção", min_value=0.1, value=1.0)
            
            total_c = round(float(val_c) * qtd, 1)
            st.metric("Total de Carboidratos", f"{total_c}g")

            if st.button("Calcular Dose"):
                dose = calcular_insulina(g_pre, 100, 50, total_c, 15)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": total_c, "Dose": dose, "Momento": "Refeição", "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.success(f"Dose sugerida: {dose} U")

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardápio de Alimentos")
    st.write("Adicione novos itens ou gerencie os carboidratos da lista.")

    # Layout Moderno para Adicionar
    with st.form("novo_alimento", clear_on_submit=True):
        st.subheader("➕ Novo Alimento")
        c1, c2 = st.columns([2, 1])
        with c1:
            nome_a = st.text_input("Nome do Alimento", placeholder="Ex: Maçã, Tapioca...")
        with c2:
            carbo_a = st.number_input("Carbos (por 1 un/dose)", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Salvar na Lista"):
            if nome_a:
                novo_item = pd.DataFrame([{"Alimento": nome_a, "Carbos": carbo_a}])
                df_alimentos = pd.concat([df_alimentos, novo_item], ignore_index=True)
                df_alimentos.to_csv("alimentos.csv", index=False)
                st.success("Alimento adicionado!")
                st.rerun()

    st.divider()
    
    # Gerenciamento da Tabela
    st.subheader("📋 Lista Salva")
    st.info("💡 Você pode editar os valores diretamente na tabela abaixo e clicar em 'Atualizar Tudo'.")
    df_editado = st.data_editor(
        df_alimentos, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Alimento": st.column_config.TextColumn("Alimento", width="large"),
            "Carbos": st.column_config.NumberColumn("G de Carboidratos", format="%.1f g")
        }
    )
    
    if st.button("💾 Atualizar Tudo"):
        df_editado.to_csv("alimentos.csv", index=False)
        st.success("Cardápio atualizado com sucesso!")

# --- (Outras abas como Pacientes e Histórico permanecem com as correções anteriores) ---
elif aba == "👥 Pacientes":
    st.header("👥 Gestão de Pacientes")
    aba_p = st.tabs(["➕ Adicionar", "✏️ Editar/Remover"])
    with aba_p[0]:
        with st.form("add_pac"):
            c1, c2 = st.columns(2)
            with c1: n = st.text_input("Nome"); p = st.selectbox("Parentesco", ["Filho", "Filha", "Cônjuge", "Outro"])
            with c2: s = st.selectbox("Sangue", ["Não Sei", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]); pl = st.text_input("Plano")
            if st.form_submit_button("Cadastrar"):
                if n:
                    np = pd.DataFrame([{"Nome": n, "Parentesco": p, "Sangue": s, "Plano": pl}])
                    df_pacientes = pd.concat([df_pacientes, np], ignore_index=True); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()

    with aba_p[1]:
        if not df_pacientes.empty:
            edit_p = st.selectbox("Selecionar Paciente", df_pacientes["Nome"].tolist())
            idx = df_pacientes.index[df_pacientes["Nome"] == edit_p][0]
            if st.button("🗑️ Remover Paciente"):
                df_pacientes = df_pacientes.drop(idx); df_pacientes.to_csv("pacientes.csv", index=False); st.rerun()

elif aba == "📊 Histórico":
    st.header("📜 Histórico")
    st.dataframe(df_historico, use_container_width=True)
    if not df_historico.empty:
        st.download_button("📥 Baixar PDF", data=gerar_pdf(df_historico), file_name="relatorio.pdf")

elif aba == "👤 Perfil":
    st.header("👤 Configurações")
    with st.expander("🎨 Aparência"):
        st.session_state.cor_botao = st.color_picker("Cor Principal", st.session_state.cor_botao)
        if st.button("Aplicar"): st.rerun()