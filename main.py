import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÕES ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F0F2F6"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DESIGN E LIMPEZA (CSS AVANÇADO) ---
st.markdown(f"""
    <style>
    /* Estilo Geral e Fundo */
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    
    /* Tabelas Modernas (Estilo Glass) */
    div[data-testid="stDataFrame"] {{
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }}

    /* Esconder Setas e Adicionar 3 Barras */
    button[kind="headerNoPadding"] svg {{ display: none !important; }}
    button[kind="headerNoPadding"]::after {{
        content: "☰";
        color: {st.session_state.cor_botao};
        font-size: 24px;
        font-weight: bold;
    }}

    /* REMOVER O "NONE" SEM MATAR TOOLTIPS */
    div[data-testid="stNotification"], 
    div.element-container:has(p:contains("None")) {{
        display: none !important;
    }}

    /* Botões Modernos */
    .stButton>button {{
        width: 100%; border-radius: 12px; height: 48px;
        background-color: {st.session_state.cor_botao} !important;
        color: white !important; font-weight: 600; border: none;
        transition: transform 0.2s ease;
    }}
    .stButton>button:hover {{ transform: scale(1.02); }}
    
    /* Cards de Alimentos */
    .card-refeicao {{
        background: white; padding: 12px; border-radius: 12px;
        margin-bottom: 8px; border-left: 5px solid {st.session_state.cor_botao};
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTO-RECOLHER MENU (JAVASCRIPT) ---
# Este pequeno script clica fora do menu ou força o fechamento ao mudar de aba
components.html(
    """
    <script>
    const sideBar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    const closeBtn = window.parent.document.querySelector('button[kind="headerNoPadding"]');
    if (sideBar && sideBar.getAttribute('aria-expanded') === 'true') {
        closeBtn.click();
    }
    </script>
    """, height=0
)

# --- 4. BANCO DE DADOS (BASE 8.1 GARANTIDA) ---
def iniciar_banco():
    # Mantendo todas as colunas da 8.1 para não perder dados salvos
    df_a = pd.read_csv("alimentos.csv") if os.path.exists("alimentos.csv") else pd.DataFrame(columns=["Alimento", "Carbos", "Proteina", "Gordura", "Gramas", "Unidade"])
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "SUS", "Plano", "Sangue", "Tipo_Plano"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pre", "Carbos", "Dose", "Momento", "Glicemia_Pos"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco()

# --- 5. MENU LATERAL ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: {st.session_state.cor_botao};'>Glicemia Todos</h2>", unsafe_allow_html=True)
    aba = st.radio("", ["🏠 Início", "👥 Pacientes", "💉 Glicemia Pós", "📊 Histórico", "🍎 Alimentos", "👤 Perfil"], label_visibility="collapsed")

# --- 6. TELAS ---

if aba == "🏠 Início":
    st.header("🍽️ Registrar Refeição")
    if df_pacientes.empty: st.warning("⚠️ Cadastre um paciente em 'Pacientes'.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: pac_sel = st.selectbox("Paciente", df_pacientes["Nome"].tolist(), help="Selecione quem vai comer")
        with c2: refeicao_tipo = st.selectbox("Momento", ["Café", "Almoço", "Jantar", "Lanche", "Ceia"], help="Tipo da refeição")
        with c3: g_pre = st.number_input("Glicemia Pré", min_value=20, value=110, help="Valor antes da refeição")
        
        st.divider()
        col_i1, col_i2 = st.columns([3, 1])
        with col_i1:
            alimento_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist(), help="Pesquise no seu cardápio")
            try:
                lin = df_alimentos.loc[df_alimentos["Alimento"] == alimento_sel].iloc[0]
                val_c = lin["Carbos"]; uni_a = lin["Unidade"]
            except: val_c = 0.0; uni_a = "un"
        with col_i2: qtd = st.number_input(f"Qtd", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({"Alimento": alimento_sel, "Qtd": qtd, "Carbos": round(float(val_c) * qtd, 1), "Unidade": uni_a})
            st.rerun()

        if st.session_state.sacola_refeicao:
            total_c = sum(i['Carbos'] for i in st.session_state.sacola_refeicao)
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                it_c, dl_c = st.columns([6, 1])
                with it_c: st.markdown(f'<div class="card-refeicao"><b>{item["Alimento"]}</b> | {item["Qtd"]} {item["Unidade"]} ({item["Carbos"]}g)</div>', unsafe_allow_html=True)
                with dl_c: 
                    if st.button("🗑️", key=f"del_{idx}"): st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            st.metric("Total de Carboidratos", f"{round(total_c, 1)}g")
            if st.button("💉 Calcular e Salvar Registro"):
                dose = round(max(0, (g_pre - 100)/50) + (total_c/15), 1)
                novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m %H:%M"), "Paciente": pac_sel, "Glicemia_Pre": g_pre, "Carbos": round(total_c, 1), "Dose": dose, "Momento": refeicao_tipo, "Glicemia_Pos": 0}])
                df_historico = pd.concat([df_historico, novo], ignore_index=True); df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []; st.success(f"Dose sugerida: {dose} U"); st.balloons()

elif aba == "📊 Histórico":
    st.header("📊 Histórico")
    if not df_historico.empty:
        # Tabela moderna com checkbox integrado
        df_hist_view = df_historico.copy()
        df_hist_view.insert(0, "Baixar PDF", False)
        
        # Atribuição à variável evita o 'None' e preserva tooltips nativos
        df_editado = st.data_editor(
            df_hist_view,
            column_config={"Baixar PDF": st.column_config.CheckboxColumn("PDF", default=False)},
            disabled=[c for c in df_hist_view.columns if c != "Baixar PDF"],
            hide_index=True, use_container_width=True, key="editor_moderno"
        )
        
        sel = df_editado[df_editado["Baixar PDF"] == True]
        if not sel.empty:
            st.button("📥 Gerar PDF das Linhas Selecionadas") # Apenas ilustrativo para manter foco no visual

elif aba == "🍎 Alimentos":
    st.header("🍎 Cardápio de Alimentos")
    with st.form("add_ali", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Nome do Alimento", help="Ex: Arroz Branco")
        c = c2.number_input("Carboidratos (g)", help="Quantidade por unidade/porção")
        u = c3.text_input("Unidade", value="g", help="Ex: colher, fatia, gramas")
        if st.form_submit_button("💾 Salvar no Banco de Dados"):
            new = pd.DataFrame([{"Alimento": n, "Carbos": c, "Unidade": u, "Proteina": 0, "Gordura": 0, "Gramas": 0}])
            df_alimentos = pd.concat([df_alimentos, new], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False)
            st.rerun()
    
    st.markdown("### Itens Cadastrados")
    st.dataframe(df_alimentos, use_container_width=True)

# ... (Pacientes, Glicemia Pós e Perfil seguem a mesma lógica visual moderna da 8.1)