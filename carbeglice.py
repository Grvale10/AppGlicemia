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
