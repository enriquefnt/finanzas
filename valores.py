import yfinance as yf


import pandas as pd

# Ejemplo: Obtener datos históricos diarios de una acción (ej. Apple en EE.UU. o YPF en Argentina/EE.UU.)
ticker = "AAPL"  # Cambia a "YPF" para una acción argentina listada en NYSE
data = yf.download(ticker, start="2025-10-01", end="2025-10-31", interval="1d")

# Mostrar los primeros 5 días
print(data.head(20))

# Precio actual (último cierre)
current_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
print(f"Precio actual de {ticker}: {current_price}")