import yfinance as yf
import pandas as pd

# 1. Descargar datos de DoubleDown (DDI)
ticker = "DDI"
# Usamos group_by='column' y luego seleccionamos 'Close' para evitar el MultiIndex
data = yf.download(ticker, start="2021-08-31", end="2026-04-20")

# Limpiamos el DataFrame para que las columnas sean simples (solo 'Open', 'Close', etc.)
data.columns = data.columns.get_level_values(0)

# 2. Definir indicadores
data['SMA20'] = data['Close'].rolling(window=20).mean()

# 3. Eliminar los primeros 20 días donde la SMA20 es NaN (esto evita errores de comparación)
data = data.dropna(subset=['SMA20'])

capital_inicial = 400.0
posicion = 0
precio_compra = 0

# 4. Bucle de la Estrategia
for i in range(len(data)):
    # Usamos .item() para extraer el valor escalar puro y evitar el error de Series
    precio_actual = data['Close'].iloc[i].item()
    sma_actual = data['SMA20'].iloc[i].item()
    
    #print(f"\nPrecioActual: ${precio_actual:.2f}")
    if posicion == 0 and precio_actual > sma_actual:
        posicion = capital_inicial / precio_actual
        precio_compra = precio_actual
        print(f"Compra a ${precio_actual:.2f}")

    elif posicion > 0 and precio_actual > (precio_compra * 1.10):
        capital_inicial = posicion * precio_actual
        print(f"Venta a ${precio_actual:.2f} | Nuevo Capital: ${capital_inicial:.2f}")
        posicion = 0

# Resultado final
precio_final = data['Close'].iloc[-1].item()
capital_final = capital_inicial if posicion == 0 else posicion * precio_final
print(f"\nResultado final: ${capital_final:.2f}")