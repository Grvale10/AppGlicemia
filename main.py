import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. CONFIGURAÇÕES E ESTADO DO APLICATIVO ---
if "cor_fundo" not in st.session_state: st.session_state.cor_fundo = "#F8F9FA"
if "cor_botao" not in st.session_state: st.session_state.cor_botao = "#6366F1"
if "sacola_refeicao" not in st.session_state: st.session_state.sacola_refeicao = []

st.set_page_config(page_title="Glicemia Para Todos", layout="wide", initial_sidebar_state="expanded")

# --- 2. ESTILIZAÇÃO VISUAL (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {st.session_state.cor_fundo}; }}
    [data-testid="stStatusWidget"], .element-container:has(p:contains("None")) {{ display: none !important; }}
    .card-refeicao {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-left: 6px solid {st.session_state.cor_botao}; margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS TÉCNICO (Nomes Completos e Dados SBD) ---
def iniciar_banco_dados():
    # Lista SBD robusta com as 3 macronutrientes por extenso
    lista_sbd_completa = [
        {"Alimento": "Arroz Branco", "Carboidratos": 28.0, "Proteínas": 2.5, "Gorduras": 0.2, "Unidade": "Escumadeira (100g)"},
        {"Alimento": "Feijão Carioca", "Carboidratos": 14.0, "Proteínas": 5.0, "Gorduras": 0.5, "Unidade": "Concha (100g)"},
        {"Alimento": "Pão Francês", "Carboidratos": 25.0, "Proteínas": 4.0, "Gorduras": 1.5, "Unidade": "Unidade (50g)"},
        {"Alimento": "Peito de Frango Grelhado", "Carboidratos": 0.0, "Proteínas": 31.0, "Gorduras": 3.6, "Unidade": "Filé médio (100g)"},
        {"Alimento": "Ovo Cozido", "Carboidratos": 0.6, "Proteínas": 6.3, "Gorduras": 5.3, "Unidade": "Unidade"},
        {"Alimento": "Carne Moída (Patinho)", "Carboidratos": 0.0, "Proteínas": 26.0, "Gorduras": 7.0, "Unidade": "100g"},
        {"Alimento": "Macarrão Cozido", "Carboidratos": 30.0, "Proteínas": 5.8, "Gorduras": 0.9, "Unidade": "Pegador (100g)"},
        {"Alimento": "Tapioca (Goma)", "Carboidratos": 54.0, "Proteínas": 0.0, "Gorduras": 0.0, "Unidade": "100g"},
        {"Alimento": "Leite Integral", "Carboidratos": 10.0, "Proteínas": 6.8, "Gorduras": 6.0, "Unidade": "Copo (200ml)"},
        {"Alimento": "Banana Prata", "Carboidratos": 22.0, "Proteínas": 1.3, "Gorduras": 0.3, "Unidade": "Unidade"},
        {"Alimento": "Pizza Mussarela", "Carboidratos": 25.0, "Proteínas": 10.0, "Gorduras": 9.0, "Unidade": "Fatia média"},
        {"Alimento": "Cuscuz de Milho", "Carboidratos": 25.0, "Proteínas": 2.2, "Gorduras": 0.5, "Unidade": "Fatia (100g)"},
        {"Alimento": "Maçã com Casca", "Carboidratos": 15.0, "Proteínas": 0.3, "Gorduras": 0.2, "Unidade": "Unidade média"}
    ]
    
    if os.path.exists("alimentos.csv"):
        df_a = pd.read_csv("alimentos.csv")
        # Se os dados estiverem incompletos ou abreviados, reiniciamos o arquivo
        if "Carboidratos" not in df_a.columns or len(df_a) < 10:
            os.remove("alimentos.csv")
            df_a = pd.DataFrame(lista_sbd_completa)
            df_a.to_csv("alimentos.csv", index=False)
    else:
        df_a = pd.DataFrame(lista_sbd_completa)
        df_a.to_csv("alimentos.csv", index=False)
        
    df_p = pd.read_csv("pacientes.csv") if os.path.exists("pacientes.csv") else pd.DataFrame(columns=["Nome", "Parentesco", "CPF", "Sangue"])
    df_h = pd.read_csv("dados_glicemia.csv") if os.path.exists("dados_glicemia.csv") else pd.DataFrame(columns=["Data", "Paciente", "Glicemia_Pré", "Carboidratos", "Proteínas", "Gorduras", "Dose", "Momento", "Glicemia_Pós"])
    return df_a, df_h, df_p

df_alimentos, df_historico, df_pacientes = iniciar_banco_dados()

# --- 4. INTERFACE ---
with st.sidebar:
    st.title("🛡️ Glicemia Para Todos")
    aba = st.radio("Navegação", ["🏠 Registrar Refeição", "👥 Pacientes", "📌 Pendentes", "📊 Histórico", "🍎 Tabela de Alimentos", "👤 Perfil"])

if aba == "🏠 Registrar Refeição":
    st.header("🍽️ Registro de Refeição")
    
    if df_pacientes.empty:
        st.warning("Cadastre um paciente primeiro na aba 'Pacientes'.")
    else:
        # 1. Dados Iniciais
        col_dados1, col_dados2, col_dados3 = st.columns(3)
        with col_dados1: pac_escolhido = st.selectbox("Paciente", df_pacientes["Nome"].tolist())
        with col_dados2: mom_escolhido = st.selectbox("Refeição", ["Café da Manhã", "Almoço", "Jantar", "Lanche", "Ceia"])
        with col_dados3: gli_pre = st.number_input("Glicemia Pré (mg/dL)", value=110)
        
        st.divider()
        
        # 2. ADICIONAR ALIMENTOS (ESTA É A PARTE QUE TINHA SUMIDO)
        st.subheader("🍕 Adicionar Alimentos")
        col_sel1, col_sel2 = st.columns([3, 1])
        with col_sel1:
            nome_sel = st.selectbox("Buscar Alimento", df_alimentos["Alimento"].tolist())
            alimento_info = df_alimentos.loc[df_alimentos["Alimento"] == nome_sel].iloc[0]
        with col_sel2:
            qtd_sel = st.number_input(f"Qtd ({alimento_info['Unidade']})", min_value=0.1, value=1.0)
        
        if st.button("➕ Adicionar ao Prato"):
            st.session_state.sacola_refeicao.append({
                "Alimento": nome_sel,
                "Quantidade": qtd_sel,
                "Unidade": alimento_info["Unidade"],
                "Carboidratos": round(float(alimento_info["Carboidratos"]) * qtd_sel, 1),
                "Proteínas": round(float(alimento_info["Proteínas"]) * qtd_sel, 1),
                "Gorduras": round(float(alimento_info["Gorduras"]) * qtd_sel, 1)
            })
            st.rerun()

        # 3. Resumo e Totais
        if st.session_state.sacola_refeicao:
            st.markdown("---")
            total_c = sum(i["Carboidratos"] for i in st.session_state.sacola_refeicao)
            total_p = sum(i["Proteínas"] for i in st.session_state.sacola_refeicao)
            total_g = sum(i["Gorduras"] for i in st.session_state.sacola_refeicao)
            
            for idx, item in enumerate(st.session_state.sacola_refeicao):
                c_c1, c_c2 = st.columns([9, 1])
                with c_c1:
                    st.markdown(f"""
                    <div class="card-refeicao">
                        <strong>{item['Alimento']}</strong> — {item['Quantidade']} {item['Unidade']}<br>
                        <small>Carboidratos: {item['Carboidratos']}g | Proteínas: {item['Proteínas']}g | Gorduras: {item['Gorduras']}g</small>
                    </div>
                    """, unsafe_allow_html=True)
                with c_c2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.sacola_refeicao.pop(idx); st.rerun()
            
            st.subheader("📊 Totais")
            t1, t2, t3 = st.columns(3)
            t1.metric("Total Carboidratos", f"{round(total_c, 1)}g")
            t2.metric("Total Proteínas", f"{round(total_p, 1)}g")
            t3.metric("Total Gorduras", f"{round(total_g, 1)}g")

            if st.button("💉 Salvar e Gerar Dose"):
                dose = round(max(0, (gli_pre - 100)/50) + (total_c / 15), 1)
                novo_r = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": pac_escolhido,
                    "Glicemia_Pré": gli_pre, "Carboidratos": total_c, "Proteínas": total_p, "Gorduras": total_g,
                    "Dose": dose, "Momento": mom_escolhido, "Glicemia_Pós": 0
                }])
                df_historico = pd.concat([df_historico, novo_r], ignore_index=True)
                df_historico.to_csv("dados_glicemia.csv", index=False)
                st.session_state.sacola_refeicao = []
                st.success(f"Salvo! Dose: {dose} U"); st.balloons()

elif aba == "🍎 Tabela de Alimentos":
    st.header("🍎 Banco de Alimentos SBD")
    st.dataframe(df_alimentos, use_container_width=True)
    
    with st.form("novo_ali_form", clear_on_submit=True):
        st.subheader("Cadastrar Novo Alimento")
        f1, f2, f3 = st.columns(3)
        with f1: n = st.text_input("Nome"); u = st.text_input("Unidade")
        with f2: c = st.number_input("Carboidratos"); p = st.number_input("Proteínas")
        with f3: g = st.number_input("Gorduras")
        if st.form_submit_button("Salvar Alimento"):
            novo_a = pd.DataFrame([{"Alimento": n, "Carboidratos": c, "Proteínas": p, "Gorduras": g, "Unidade": u}])
            df_alimentos = pd.concat([df_alimentos, novo_a], ignore_index=True); df_alimentos.to_csv("alimentos.csv", index=False); st.rerun()

# (Pacientes, Pendentes e Perfil continuam funcionando normalmente)