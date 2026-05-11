import yfinance as yf
import pymysql
import config
import warnings
warnings.filterwarnings("ignore")

# ETF US - PRECIOS EN USD
ETF_US = ['DDI', 'IEF', 'QUAL', 'SGOV', 'VCIT', 'VIG', 'VOOG', 'CRM']
# CEDEARS - PRECIOS EN ARS  
CEDEARS = ['AAPL', 'AMGN', 'CRM', 'MELI', 'NU', 'PG', 'PLTR', 'XP']

def main():
    print("🚀 MONITOR FINAL - ETF US + CEDEARS")
    
    # Dólar para CEDEARS
    usd_ccl = 1350  # Fijo por ahora
    print(f"💵 CCL: ${usd_ccl:,}\n")
    
    conn = pymysql.connect(
        host='cpl16.main-hosting.eu',
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_DATABASE,
        autocommit=True
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("🇺🇸 ETF US (USD)\n")
    for ticker in ETF_US:
        try:
            precio_usd = float(yf.download(ticker, period="5d", progress=False)['Close'].iloc[-1])
            
            cursor.execute("SELECT cantidad, precio_compra FROM portfolio_monitor WHERE ticker = %s", (ticker,))
            row = cursor.fetchone()
            if not row:
                continue
                
            p_compra_usd = float(row['precio_compra'])
            cantidad = row['cantidad']
            
            sl = round(p_compra_usd * 0.90, 2)
            tp = round(p_compra_usd * 1.25, 2)
            
            cambio = round((precio_usd / p_compra_usd - 1) * 100, 1)
            estado = 'activo'
            if precio_usd <= sl:
                estado = '🚨 SL'
            elif precio_usd >= tp:
                estado = '🎉 TP'
            
            print(f"{ticker:>6} | ${p_compra_usd:>7.2f} → ${precio_usd:>7.2f} | {cambio:+4.1f}% | {estado}")
            
            cursor.execute("""
                UPDATE portfolio_monitor SET 
                precio_actual=%s, stop_loss=%s, take_profit=%s, estado=%s
                WHERE ticker=%s
            """, (precio_usd, sl, tp, estado, ticker))
            
        except:
            pass
    
    print(f"\n🪙 CEDEARS (ARS)\n")
    for ticker in CEDEARS:
        try:
            precio_usd = float(yf.download(ticker, period="5d", progress=False)['Close'].iloc[-1])
            precio_ars = precio_usd * usd_ccl  # Convertir a ARS
            
            cursor.execute("SELECT cantidad, precio_compra FROM portfolio_monitor WHERE ticker = %s", (ticker,))
            row = cursor.fetchone()
            if not row:
                continue
                
            p_compra_ars = float(row['precio_compra'])
            
            sl = round(p_compra_ars * 0.90, 0)
            tp = round(p_compra_ars * 1.25, 0)
            
            cambio = round((precio_ars / p_compra_ars - 1) * 100, 1)
            estado = 'activo'
            if precio_ars <= sl:
                estado = '🚨 SL'
            elif precio_ars >= tp:
                estado = '🎉 TP'
            
            print(f"{ticker:>6} | ${p_compra_ars:>9,} → ${precio_ars:>10,.0f}ARS | {cambio:+4.1f}% | {estado}")
            
            cursor.execute("""
                UPDATE portfolio_monitor SET 
                precio_actual=%s, stop_loss=%s, take_profit=%s, estado=%s
                WHERE ticker=%s
            """, (precio_ars, sl, tp, estado, ticker))
            
        except:
            pass
    
    conn.close()
    print("\n✅ MONITOR COMPLETADO - Precios corregidos!")
    
    print("\n🔍 Verifica tu tabla ahora:")
    print("SELECT ticker, precio_compra, precio_actual, estado FROM portfolio_monitor WHERE cantidad > 0")

if __name__ == "__main__":
    main()