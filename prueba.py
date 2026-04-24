import yfinance as yf
ticker = "GGAL.BA"
data = yf.download(
    ticker,
    start="2025-12-01",
    end="2025-12-19"
)
# Función para precio actual
def get_current_price(ticker):
    return yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]



print(data)

print('\n--Describe--\n', data.describe())
print('\n--Columns--\n', data.columns)
print(f'\n-- get_current_price(item["ticker"])', data.describe())
