import yfinance as yf
import pymysql
import config

def get_dolar_mep():
    """Dólar CCL oficial"""
    try:
        return round(yf.download("USDC.MA", period="1d", progress=False)['Close'].iloc[-1], 0)
    except:
        return 1350  # Backup

print("🚀 MONITOR CORREGIDO INICIADO")
usd_ars = get_dolar_mep()
print(f"💵 Dólar CCL: ${usd_ars:,}\n")

# Conexión DB
conn = pymysql.connect(
    host='cpl16.main-hosting.eu',
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    database=config.DB_DATABASE
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# Solo activos con cantidad > 0
cursor.execute("""
    SELECT id, ticker, moneda, cantidad, precio_compra 
    FROM portfolio_monitor 
    WHERE cantidad > 0
""")
activos = cursor.fetchall()

alertas = []
for activo in activos:
    ticker = activo['ticker']
    moneda = activo['moneda']
    cantidad = activo['cantidad']
    p_compra = float(activo['precio_compra'])
    
    # Ticker correcto para Yahoo
    if moneda == 'USD':
        ticker_yf = ticker
    else:
        ticker_yf = f"{ticker}.BA"
    
    try:
        # Descargar precio
        data = yf.download(ticker_yf, period="2d", progress=False)
        if data.empty:
            print(f"  {ticker:>6} ❌ Sin cotización")
            continue
            
        precio_yf = data['Close'].iloc[-1]
        
        # CONVERTIR A USD para comparar
        if moneda == 'ARS':
            precio_usd = round(precio_yf / usd_ars, 2)
        else:
            precio_usd = round(precio_yf, 2)
        
        # Calcular SL/TP
        sl = round(p_compra * 0.90, 2)
        tp = round(p_compra * 1.25, 2)
        
        # Verificar alertas
        estado = 'activo'
        if precio_usd <= sl:
            estado = '🚨 STOP_LOSS'
            alertas.append(f"🚨 {ticker}: ${precio_usd} < SL ${sl}")
        elif precio_usd >= tp:
            estado = '🎉 TAKE_PROFIT'
            alertas.append(f"🎉 {ticker}: ${precio_usd} > TP ${tp}")
        
        # MOSTRAR
        cambio = round((precio_usd / p_compra - 1) * 100, 1)
        print(f"{ticker:>6} ({moneda}) | ${p_compra:>8,.0f} → ${precio_usd:>8,.0f} | {cambio:+.1f}% | {estado}")
        
        # GUARDAR EN DB
        cursor.execute("""
            UPDATE portfolio_monitor SET 
            precio_actual = %s, stop_loss = %s, take_profit = %s, 
            estado = %s, ultima_actualizacion = NOW()
            WHERE id = %s
        """, (precio_usd, sl, tp, estado, activo['id']))
        
    except Exception as e:
        print(f"  {ticker:>6} ❌ {e}")

conn.commit()
conn.close()

print(f"\n{'='*60}")
if alertas:
    print("🚨 ALERTAS:")
    for alerta in alertas:
        print(alerta)
else:
    print("✅ SIN ALERTAS - TODO CONTROLADO")
print("🎉 Monitor completado!")