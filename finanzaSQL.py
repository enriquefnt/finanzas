import pandas as pd
import pymysql
import config

def actualizar_db_usa_exclusivo():
    try:
        # 1. Leer CSV
        df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
        
        # 2. ACCESO POR POSICIÓN (No por nombre)
        # Según tu ejemplo:
        # Index 4: Tipo Transacción
        # Index 8: Simbolo
        # Index 9: Cantidad
        # Index 11: Precio Ponderado
        
        df_limpio = pd.DataFrame()
        df_limpio['Simbolo'] = df.iloc[:, 8].astype(str).str.strip().str.upper()
        df_limpio['Tipo'] = df.iloc[:, 4].astype(str).str.strip().str.lower()
        df_limpio['Cant_Str'] = df.iloc[:, 9].astype(str)
        df_limpio['Precio_Str'] = df.iloc[:, 11].astype(str)

        # 3. Filtrar activos USA
        activos_usa = ['QUAL', 'VCIT', 'VIG', 'SGOV', 'VOOG', 'IEF', 'DDI','CRM']
        df_usa = df_limpio[df_limpio['Simbolo'].isin(activos_usa)].copy()

        if df_usa.empty:
            print("⚠️ No se encontraron activos de la lista en el CSV.")
            return

        # 4. Limpieza numérica
        df_usa['Cantidad'] = pd.to_numeric(df_usa['Cant_Str'].str.replace(',', '.'), errors='coerce').fillna(0)
        df_usa['Precio'] = pd.to_numeric(df_usa['Precio_Str'].str.replace(',', '.'), errors='coerce').fillna(0)
        
        # 5. Cálculo de Posición Neta y PPP
        # Posición
        df_usa['Cant_Neto'] = df_usa.apply(lambda r: r['Cantidad'] if 'comp' in r['Tipo'] else -r['Cantidad'], axis=1)
        resumen_posicion = df_usa.groupby('Simbolo')['Cant_Neto'].sum()

        # PPP
        compras = df_usa[df_usa['Tipo'].str.contains('comp', na=False)].copy()
        resumen_ppp = pd.DataFrame()
        if not compras.empty:
            compras['Costo_Total'] = compras['Cantidad'] * compras['Precio']
            resumen_ppp = compras.groupby('Simbolo').agg({'Cantidad': 'sum', 'Costo_Total': 'sum'})
            resumen_ppp['PPP'] = resumen_ppp['Costo_Total'] / resumen_ppp['Cantidad'].replace(0, 1)

        # 6. Conexión a MySQL
        conn = pymysql.connect(
            host='cpl16.main-hosting.eu',
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_DATABASE
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_monitor")

        print("--- Sincronizando Cartera USA ---")
        conteo = 0
        for ticker in activos_usa:
            if ticker in resumen_posicion.index:
                cant_total = abs(resumen_posicion[ticker])
                if cant_total > 0:
                    ppp = 0
                    if not resumen_ppp.empty and ticker in resumen_ppp.index:
                        ppp = round(float(resumen_ppp.loc[ticker, 'PPP']), 2)
                    
                    sql = "INSERT INTO portfolio_monitor (ticker, cantidad, precio_compra, estado) VALUES (%s, %s, %s, 'activo')"
                    cursor.execute(sql, (ticker, cant_total, ppp))
                    print(f"✅ {ticker}: {cant_total} un. | PPP: USD {ppp}")
                    conteo += 1

        conn.commit()
        print(f"\n🚀 Sincronización exitosa. {conteo} activos en la base de datos.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == "__main__":
    actualizar_db_usa_exclusivo()