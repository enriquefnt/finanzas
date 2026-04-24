import yfinance as yf
import pandas as pd
import config

# 1. Parámetros de tu estrategia
STOP_LOSS = 0.90    # Vende si cae 10% o más
TAKE_PROFIT = 1.25  # Vende si sube 25% o más

# Tus tenencias (sin CRM, según tu tabla)
portfolio_qty = {
    "DDI": 94, "IEF": 7, "SGOV": 6, 
    "VCIT": 4, "VIG": 4, "QUAL": 3, "VOOG": 6,
    "CRM": 1
}

# 2. Descargar datos
activos = list(portfolio_qty.keys())
data = yf.download(activos, start="2021-08-31")['Close']
data.columns = data.columns.get_level_values(0)

print(f"--- Simulando Gestión de Riesgos ---\n")

# 3. Analizar activo por activo
for activo in activos:
    precios = data[activo].dropna()
    if precios.empty: continue
    
    precio_inicial = precios.iloc[0]  # Simulamos que compraste al inicio del periodo
    precio_actual = precios.iloc[-1]
    rendimiento = precio_actual / precio_inicial
    
    # Lógica de alertas
    if rendimiento <= STOP_LOSS:
        print(f"⚠️ [STOP LOSS] {activo}: Cayó un {((1-rendimiento)*100):.1f}%. Deberías haber vendido.")
    
    elif rendimiento >= TAKE_PROFIT:
        print(f"💰 [TAKE PROFIT] {activo}: Subió un {((rendimiento-1)*100):.1f}%. ¡Ya ganaste bastante, vendé!")
    
    else:
        print(f"✅ {activo}: En rango neutral ({((rendimiento-1)*100):.1f}% de retorno).")

# 4. Cálculo del valor de liquidación
# (Si vendieras todo hoy según estas reglas)