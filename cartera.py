import yfinance as yf
import pandas as pd
from datetime import datetime
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def convertir_fecha(fecha_str):
    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
    return fecha_obj.strftime("%d/%m/%Y")

# Tu cartera
portfolio = [
    {"ticker": "BMA", "quantity": 10, "buy_price": 150},
    {"ticker": "AAPL", "quantity": 10, "buy_price": 150},
    #{"ticker": "YPF", "quantity": 5, "buy_price": 10}
]

# Función para precio actual
def get_current_price(ticker):
    return yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]

# Calcular ganancias/pérdidas
total_value = 0
total_cost = 0
for item in portfolio:
    current = get_current_price(item["ticker"])
    value = current * item["quantity"]
    cost = item["buy_price"] * item["quantity"]
    gain_loss = value - cost
    total_value += value
    total_cost += cost
    print(f"{item['ticker']}: Valor actual {value:.2f}, Ganancia/Pérdida {gain_loss:.2f}")

print(f"Total cartera: Valor {total_value:.2f}, Costo {total_cost:.2f}, Ganancia/Pérdida total {total_value - total_cost:.2f}")

# # Resumen mensual (igual, solo para "BMA")
# ticker = "BMA"
inicio = "2025-09-01"  # Cambiado a fecha pasada para datos reales
fin = "2025-12-18"     # Cambiado a fecha pasada
# data = yf.download(ticker, start=inicio, end=fin, auto_adjust=False)
# print(f"Fecha convertida {convertir_fecha(inicio)}")
# if data.empty:
#     print(f"No hay datos para {ticker} en las fechas especificadas.")
# else:
#     data.columns = data.columns.droplevel(1)
#     close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
#     monthly_summary = data.resample('ME').agg({close_col: 'last', 'Volume': 'sum'})
#     print("Resumen mensual (último precio ajustado y volumen total por mes):")
#     print(monthly_summary)

# Gráfica de velas para TODOS los tickers en portfolio
tickers = [item["ticker"] for item in portfolio]
data_multi = yf.download(tickers, start=inicio, end=fin, auto_adjust=False)

if data_multi.empty:
    print("No hay datos para los tickers en las fechas especificadas.")
else:
    # Crear figura con 1 fila por ticker
    num_tickers = len(tickers)
    fig, axes = plt.subplots(nrows=num_tickers, figsize=(12, 8 * num_tickers), sharex=True)
    if num_tickers == 1:  # Si solo hay uno, axes no es lista
        axes = [axes]
    
    # Iterar por cada ticker
    for i, ticker in enumerate(tickers):
        # Extraer datos OHLC para este ticker
        ohlc_data = data_multi[['Open', 'High', 'Low', 'Close', 'Volume']].xs(ticker, axis=1, level=1)
        
        # Crear gridspec para subdividir el subplot en 2 filas (velas arriba, volumen abajo)
        gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=axes[i].get_subplotspec(), hspace=0.1)  # Corregido
        
        # Sub-ejes: gs[0] para velas, gs[1] para volumen
        ax_velas = fig.add_subplot(gs[0])
        ax_volumen = fig.add_subplot(gs[1], sharex=ax_velas)  # Compartir eje X
        
        # Graficar velas (sin title, ylabel)
        mpf.plot(ohlc_data, type='candle', style='charles', ax=ax_velas, volume=ax_volumen,
                 ylabel='Precio (USD)', warn_too_much_data=1000)
        
        # Setear título en el eje de velas
        ax_velas.set_title(f'Velas Diarias - {ticker}')
    
    # Título general para la figura
    fig.suptitle(f'Velas Diarias - {convertir_fecha(inicio)} a {convertir_fecha(fin)})', fontsize=12)
    plt.tight_layout()
    plt.show()