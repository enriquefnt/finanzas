import pandas as pd
import pymysql
import config  # Asegúrate de que config.py tenga: DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

def actualizar_db_solo_usa():
    try:
        # 1. Leer CSV con parámetros de seguridad
        # Usamos sep=';' y encoding='latin1' que es el estándar de exportación de brokers argentinos
        df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
        
        # Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = [col.strip() for col in df.columns]
        
        # --- BÚSQUEDA FLEXIBLE DE COLUMNAS ---
        # Buscamos columnas que contengan 'Transacci' o 'Simbolo' por si hay tildes o errores
        col_trans = [c for c in df.columns if 'Transacci' in c][0]
        col_simb = [c for c in df.columns if 'Simbolo' in c or 'Símbolo' in c][0]
        
        df = df.rename(columns={col_trans: 'Tipo Transacción', col_simb: 'Simbolo'})

        # 2. Limpieza de datos en las celdas
        df['Tipo Transacción'] = df['Tipo Transacción'].astype(str).fillna('')
        
        # Limpiamos el Simbolo: Solo quitamos espacios, mantenemos números (para AL30, etc.)
        df['Simbolo'] = df['Simbolo'].astype(str).str.strip().str.upper()

        print("--- DEBUG DE DATOS ---")
        print(f"Total de filas leídas: {len(df)}")
        todos_los_simbolos = df['Simbolo'].unique()
        print(f"Símbolos detectados: {todos_los_simbolos}")
        
        # 3. FILTRO INTELIGENTE
        # En lugar de una lista fija, excluimos lo que sabemos que NO es USA/Acción
        # Excluimos lo que tiene más de 5 caracteres (Letras del tesoro como S28N5)
        # o lo que explícitamente no queremos monitorear aquí.
        def es_ticker_usa(s):
            excluir = ['S28N5', 'S31O5', 'T13F6', 'TZXM6', 'AL30', 'AL30D', 'GD30']
            if s in excluir: return False
            if len(s) > 6: return False # Filtra nombres muy largos de bonos
            return True

        # 4. Limpieza de datos numéricos
        # Reemplazamos coma por punto para que Python lo entienda como float
        for col in ['Cantidad', 'Precio Ponderado']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # 5. Cálculos de Cartera (PPP y Cantidad Neta)
        compras = df[df['Tipo Transacción'].str.contains('Compra', case=False, na=False)].copy()
        compras['Costo_Total'] = compras['Cantidad'] * compras['Precio Ponderado']
        
        resumen = compras.groupby('Simbolo').agg({'Cantidad': 'sum', 'Costo_Total': 'sum'})
        resumen['PPP'] = resumen['Costo_Total'] / resumen['Cantidad'].replace(0, 1)
        
        # Cálculo de cantidad neta (Compras - Ventas)
        def calcular_neto(row):
            return row['Cantidad'] if 'Compra' in str(row['Tipo Transacción']).lower() else -row['Cantidad']

        df['Cant_Neto'] = df.apply(calcular_neto, axis=1)
        cantidades_reales = df.groupby('Simbolo')['Cant_Neto'].sum()

        # 6. Conexión y Subida a MySQL (Hostinger)
        conn = pymysql.connect(
            host='cpl16.main-hosting.eu',
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_DATABASE
        )
        cursor = conn.cursor()

        # Limpiamos la tabla para que no queden residuos de ejecuciones anteriores
        cursor.execute("DELETE FROM portfolio_monitor")

        print("\n--- Sincronizando Portafolio USA (NYSE/NASDAQ) ---")
        conteo = 0
        for ticker, row in resumen.iterrows():
            cant_actual = cantidades_reales[ticker]
            
            # Solo subimos activos que aún conservamos en cartera
            if cant_actual > 0:
                ppp = round(float(row['PPP']), 2)
                
                sql = """
                INSERT INTO portfolio_monitor (ticker, cantidad, precio_compra, estado)
                VALUES (%s, %s, %s, 'activo')
                """
                cursor.execute(sql, (ticker, cant_actual, ppp))
                print(f"✅ {ticker}: {cant_actual} unidades a PPP USD {ppp}")
                conteo += 1

        conn.commit()
        print(f"\n🚀 Proceso terminado. Se subieron {conteo} activos a Hostinger.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == "__main__":
    actualizar_db_solo_usa()