def calcular_insulina(glicemia_atual, meta, fator_sensibilidade, carboidratos, relacao_carb):
    # Cálculo para corrigir a glicemia alta
    dose_correcao = (glicemia_atual - meta) / fator_sensibilidade
    if dose_correcao < 0:
        dose_correcao = 0
        
    # Cálculo para cobrir o que vai comer
    dose_carboidrato = carboidratos / relacao_carb
    
    total = dose_correcao + dose_carboidrato
    return round(total, 1)

def verificar_alerta(glicemia):
    if glicemia < 70:
        return "⚠️ ALERTA: Hipoglicemia! Agir imediatamente."
    elif glicemia > 180:
        return "⚠️ ALERTA: Glicemia Alta."
    return "✅ Glicemia dentro da meta."
import pandas as pd
from fpdf import FPDF
import datetime

def calcular_insulina(glicemia_atual, meta, fator_sensibilidade, carboidratos, relacao_carb):
    dose_correcao = (glicemia_atual - meta) / fator_sensibilidade
    dose_carboidrato = carboidratos / relacao_carb
    total = max(0, dose_correcao) + dose_carboidrato
    return round(total, 1)

def definir_status(glicemia, faixa_baixa, faixa_alta):
    if glicemia <= faixa_baixa:
        return "Hipoglicemia ⚠️", "red"
    elif glicemia >= faixa_alta:
        return "Hiperglicemia ⚠️", "orange"
    else:
        return "Na Faixa Ideal ✅", "green"

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatório de Glicemia", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    
    # Cabeçalho da tabela no PDF
    pdf.cell(40, 10, "Data/Hora", 1)
    pdf.cell(30, 10, "Glicemia", 1)
    pdf.cell(30, 10, "Carbos(g)", 1)
    pdf.cell(30, 10, "Insulina", 1)
    pdf.ln()
    
    for i, row in df.tail(10).iterrows(): # Pega os últimos 10 registros
        pdf.cell(40, 10, str(row['Data']), 1)
        pdf.cell(30, 10, str(row['Glicemia']), 1)
        pdf.cell(30, 10, str(row['Carbos']), 1)
        pdf.cell(30, 10, str(row['Dose']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')