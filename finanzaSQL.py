import pandas as pd
import pymysql
import config # Asegurate de que config.py tenga el nuevo HOSTNAME

def actualizar_db_desde_csv():
    # 1. Procesar el CSV para obtener el PPP
    try:
        df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
        df.columns = [col.strip() for col in df.columns]
        
        # Limpieza de datos numéricos
        df['Cantidad'] = pd.to_numeric(df['Cantidad'].astype(str).str.replace(',', '.'), errors='coerce')
        df['Precio Ponderado'] = pd.to_numeric(df['Precio Ponderado'].astype(str).str.replace(',', '.'), errors='coerce')
        
        # Calcular PPP solo de las compras
        compras = df[df['Tipo Transacción'].str.contains('Compra', na=False)].copy()
        compras['Costo_Total'] = compras['Cantidad'] * compras['Precio Ponderado']
        
        resumen = compras.groupby('Simbolo').agg({'Cantidad': 'sum', 'Costo_Total': 'sum'})
        resumen['PPP'] = resumen['Costo_Total'] / resumen['Cantidad']
        
        # Obtener cantidades netas actuales (Compras - Ventas)
        df['Cant_Neto'] = df.apply(lambda r: r['Cantidad'] if 'Compra' in r['Tipo Transacción'] else -r['Cantidad'], axis=1)
        cantidades_reales = df.groupby('Simbolo')['Cant_Neto'].sum()
        
    except Exception as e:
        print(f"❌ Error procesando CSV: {e}")
        return

    # 2. Conectar a MySQL y subir los datos
    try:
        conn = pymysql.connect(
            host='cpl16.main-hosting.eu',
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_DATABASE
        )
        cursor = conn.cursor()

        print("--- Sincronizando Portafolio ---")
        for ticker, row in resumen.iterrows():
            cant_actual = cantidades_reales[ticker]
            
            # Solo subimos si aún tenemos acciones de ese papel
            if cant_actual > 0:
                ppp = round(float(row['PPP']), 2)
                
                sql = """
                INSERT INTO portfolio_monitor (ticker, cantidad, precio_compra, estado)
                VALUES (%s, %s, %s, 'activo')
                ON DUPLICATE KEY UPDATE 
                cantidad = VALUES(cantidad), 
                precio_compra = VALUES(precio_compra),
                estado = 'activo'
                """
                cursor.execute(sql, (ticker, cant_actual, ppp))
                print(f"✅ {ticker}: {cant_actual} unidades a PPP ${ppp}")

        conn.commit()
        print("\n🚀 Base de Datos actualizada y lista para el monitor de Stop Loss.")

    except Exception as e:
        print(f"❌ Error subiendo a MySQL: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    actualizar_db_desde_csv()