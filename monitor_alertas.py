import yfinance as yf
import pymysql
import config

def ejecutar_monitor():
    try:
        conn = pymysql.connect(
            host='cpl16.main-hosting.eu',
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_DATABASE
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 1. Traer activos que marcamos como 'activo'
        cursor.execute("SELECT id, ticker, precio_compra FROM portfolio_monitor WHERE estado = 'activo'")
        activos = cursor.fetchall()
        
        if not activos:
            print("No hay activos para monitorear.")
            return

        for activo in activos:
            ticker = activo['ticker']
            p_compra = float(activo['precio_compra'])
            
            # 2. Descargar precio de Yahoo Finance
            # Nota: Algunos tickers locales (AL30, etc) pueden necesitar el sufijo .BA
            try:
                ticket_yf = yf.Ticker(ticker)
                p_actual = ticket_yf.history(period="1d")['Close'].iloc[-1]
                
                # 3. Calcular límites (Stop Loss 10%, Take Profit 25%)
                sl = p_compra * 0.90
                tp = p_compra * 1.25
                
                estado = 'activo'
                if p_actual <= sl: estado = 'stop_loss_hit'
                if p_actual >= tp: estado = 'take_profit_hit'

                # 4. Actualizar la fila con los datos de mercado
                sql = """
                    UPDATE portfolio_monitor 
                    SET precio_actual = %s, 
                        stop_loss = %s, 
                        take_profit = %s, 
                        estado = %s,
                        ultima_actualizacion = NOW()
                    WHERE id = %s
                """
                cursor.execute(sql, (p_actual, sl, tp, estado, activo['id']))
                print(f"✅ {ticker}: Actual ${p_actual:.2f} | SL: ${sl:.2f} | TP: ${tp:.2f}")

            except Exception as e:
                print(f"❌ Error con {ticker}: {e}")

        conn.commit()
        print("\n🚀 Monitor completado. Tabla actualizada.")

    finally:
        if conn: conn.close()

if __name__ == "__main__":
    ejecutar_monitor()