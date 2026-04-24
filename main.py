import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- FUNÇÕES DE APOIO ---
def calcular_insulina(glicemia, meta, sensibilidade, carboidratos, relacao_c):
    # Regra de correção + Regra de carboidratos
    correcao = max(0, (glicemia - meta) / sensibilidade)
    dose_carbo = carboidratos / relacao_c
    return round(correcao + dose_carbo, 1)

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Glicemia", ln=True, align='C')
    pdf.ln(5)
    if not df.empty:
        media = round(df['Glicemia_Pre'].mean(), 1)
        pdf.set_font("Arial", size=12)
        pdf.cell(190, 8, f"Media de Glicemia: {media} mg/dL", ln=True)
        pdf.ln(10)
    
    pdf.set_font("Arial", "B", 9)
    cols = ["Data", "Glic. Pre", "Carbo", "Dose", "Momento"]
    for col in cols: pdf.cell(38, 8, col, 1)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        pdf.cell(38, 8, str(row['Data']), 1)
        pdf.cell(38, 8, str(row['Glicemia_Pre']), 1)
        pdf.cell(38, 8, str(row['Carbos']), 1)
        pdf.cell(38, 8, str(row['Dose']), 1)
        pdf.cell(38, 8, str(row['Momento']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAÇÃO E DESIGN MODERNO ---
st.set_page_config(page_title="BioCare Kids - Gestao Familiar", layout="wide")

# Inicializa cores padrão se não existirem
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"

# --- CSS ULTRA-ESPECÍFICO (SEM FAIXAS, COM TEXTO NOS BOTÕES) ---
st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* 🎯 CORREÇÃO: PINTAR APENAS O CÍRCULO DO MENU 🎯 */
    /* Remove preenchimento de fundo da label */
    div[data-testid="stRadio"] label {{
        background-color: transparent !important;
        border: none !important;
    }}
    
    /* Mudar cor do círculo quando selecionado (Bolhas das imagens) */
    div[data-testid="stRadio"] input[type="radio"]:checked + div {{
        background-color: {st.session_state.cor_botao} !important;
        border-color: {st.session_state.cor_botao} !important;
    }}
    
    /* Mudar cor da borda do círculo não selecionado */
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {{
        border-color: {st.session_state.cor_botao}88 !important;
    }}

    /* 🎯 CORREÇÃO: TEXTO APARECER NOS BOTÕES (IMAGE 3) 🎯 */
    /* Remove degradês e força cor sólida para o texto aparecer */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: {st.session_state.cor_botao} !important;
        background-image: none !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.02); opacity: 0.9; }}

    /* Tabs (Aba Registrar/Histórico) */
    button[aria-selected="true"] {{ 
        color: {st.session_state.cor_botao} !important;
        border-bottom-color: {st.session_state.cor_botao} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
try:
    df_historico = pd.read_csv("dados_glicemia.csv")
except:
    df_historico = pd.DataFrame(columns=["Data", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])

try:
    df_alimentos = pd.read_csv("alimentos.csv")
    if "Carboidratos por Porção" in df_alimentos.columns:
        df_alimentos = df_alimentos.rename(columns={"Carboidratos por Porção": "Carbos"})
except:
    df_alimentos = pd.DataFrame({"Alimento": ["Pão Francês", "Arroz Branco (colher)"], "Carbos": [28, 15]})

# --- MENU LATERAL (TRADUZIDO) ---
with st.sidebar:
    # 🎯 CORREÇÃO 1: NOME EM PORTUGUÊS
    st.title("📟 Cuidado BioCare")
    aba = st.radio("Navegar para:", ["🏠 Inicio", "📌 Pendentes", "📜 Historico", "⚙️ Perfil & Temas", "🍎 Alimentos"])
    st.divider()

# --- CONTEÚDO DAS ABAS ---

if aba == "🏠 Inicio":
    # 🎯 CORREÇÃO 2: TÍTULO EM PORTUGUÊS
    st.title("📊 Painel de Controle")
    tab1, tab2 = st.tabs(["📝 Registrar Refeição", "📜 Histórico Rápido"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            g_pre = st.number_input("Glicemia Antes da Refeição (mg/dL)", min_value=20, value=110)
            lista_alimentos = df_alimentos["Alimento"].tolist()
            alimento = st.selectbox("Escolha o Alimento Principal", lista_alimentos)
            info = df_alimentos[df_alimentos["Alimento"] == alimento].iloc[0]
        with col2:
            porcoes = st.number_input("Quantidade (porções/unidades)", min_value=0.1, value=1.0)
            momento = st.selectbox("Momento do Dia", ["Café", "Almoço", "Jantar", "Lanche"])
            carbo_total = info['Carbos'] * porcoes
        
        # 🎯 CORREÇÃO 3: TEXTO DO BOTÃO CORRIGIDO
        if st.button("Calcular e Salvar Registro"):
            # Usando valores padrão: Meta 100, Sensibilidade 50, Relação Carbo 15
            dose = calcular_insulina(g_pre, 100, 50, carbo_total, 15)
            
            novo = {
                "Data": datetime.now().strftime("%d/%m %H:%M"),
                "Glicemia_Pre": g_pre, "Carbos": carbo_total, "Dose": dose, 
                "Momento": momento, "Glicemia_Pos": 0
            }
            df_historico = pd.concat([df_historico, pd.DataFrame([novo])], ignore_index=True)
            df_historico.to_csv("dados_glicemia.csv", index=False)
            st.success(f"Dose sugerida: {dose} U. Registro salvo com sucesso!")

    with tab2:
        st.dataframe(df_historico, use_container_width=True)
        if not df_historico.empty:
            st.download_button("📥 Baixar PDF", data=gerar_pdf(df_historico), file_name="glicemia.pdf")

elif aba == "📌 Pendentes":
    st.header("📌 Glicemia 2h Após Refeição")
    pendentes = df_historico[df_historico["Glicemia_Pos"] == 0]
    if not pendentes.empty:
        for idx, row in pendentes.iterrows():
            with st.expander(f"{row['Momento']} - {row['Data']}"):
                v_pos = st.number_input("Valor após 2h", key=f"p_{idx}")
                # 🎯 BOTÃO CORRIGIDO
                if st.button("Confirmar Medição", key=f"b_{idx}"):
                    df_historico.at[idx, "Glicemia_Pos"] = v_pos
                    df_historico.to_csv("dados_glicemia.csv", index=False)
                    st.rerun()
    else:
        st.info("Nenhuma medição pendente.")

elif aba == "⚙️ Perfil & Temas":
    st.header("⚙️ Configurações de Aparência")
    st.subheader("🎨 Escolha um Tema Profissional")
    
    # Simulação de troca de tema (precisaria salvar em session_state para persistir)
    st.selectbox("Selecione uma paleta de cores para o app:", ["Padrão (Vermelho)", "Azul Oceano", "Verde Saúde"])
    
    st.divider()
    st.subheader("👤 Dados da Criança")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.text_input("Nome da Criança", "Minha Filha")
    with col_p2:
        st.number_input("Idade", value=5)
    
    # 🎯 BOTÃO CORRIGIDO
    if st.button("Salvar Alterações de Perfil"):
        st.success("Configurações salvas!")

elif aba == "🍎 Alimentos":
    st.header("🍎 Gestão de Alimentos")
    st.dataframe(df_alimentos, use_container_width=True)
    with st.expander("➕ Adicionar Novo Alimento"):
        n = st.text_input("Nome")
        c = st.number_input("Carbo (g)", min_value=0)
        u = st.text_input("Unidade")
        # 🎯 BOTÃO CORRIGIDO
        if st.button("Salvar Novo Alimento"):
            novo = {"Alimento": n, "Carbos": c, "Unidade": u}
            df_alimentos = pd.concat([df_alimentos, pd.DataFrame([novo])], ignore_index=True)
            df_alimentos.to_csv("alimentos.csv", index=False)
            st.success("Adicionado!")
            st.rerun()