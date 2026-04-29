import pandas as pd
import pymysql
import config

def actualizar_db_solo_usa():
    # Leer CSV
    df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
    df.columns = [col.strip() for col in df.columns]
    
    print("✅ CSV cargado:", len(df), "filas")
    
    # Limpiar
    df['Tipo'] = df['Tipo Transacción'].fillna('').astype(str).str.strip()
    df['Simbolo'] = df['Simbolo'].fillna('').astype(str).str.strip().str.upper()
    
    # Filtrar USA (excluir futuros)
    futuros_ar = ['AL30', 'AL30D', 'GD30', 'S28N5', 'S31O5', 'T13F6', 'TZXM6', 'IRCPO', 'YMCIO']
    df_usa = df[~df['Simbolo'].isin(futuros_ar)].copy()
    
    # Números
    df_usa['Cantidad'] = pd.to_numeric(df_usa['Cantidad'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df_usa['Precio'] = pd.to_numeric(df_usa['Precio Ponderado'].astype(str).str.replace(',', '.').str.replace('$', ''), errors='coerce').fillna(0)
    
    print(f"✅ {len(df_usa)} movimientos USA")
    
    # CANTIDAD NETA SIMPLIFICADA
    df_usa['Es_Compra'] = df_usa['Tipo'].str.lower() == 'compra'
    df_usa['Cant_Neto'] = df_usa['Es_Compra'].astype(int) * 2 - 1 * df_usa['Cantidad']
    
    cantidades_netas = df_usa.groupby('Simbolo')['Cant_Neto'].sum()
    
    # PPP solo compras
    compras = df_usa[df_usa['Es_Compra'] == True].copy()
    print(f"✅ {len(compras)} compras encontradas")
    
    compras['Costo'] = compras['Cantidad'] * compras['Precio']
    resumen = compras.groupby('Simbolo').agg({
        'Cantidad': 'sum',
        'Costo': 'sum'
    }).round(2)
    resumen['PPP'] = resumen['Costo'] / resumen['Cantidad']
    
    print("\nPPP calculados:")
    print(resumen[['PPP']].head(10))
    
    # DB
    conn = pymysql.connect(
        host='cpl16.main-hosting.eu',
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_DATABASE
    )
    cursor = conn.cursor()
    
    # Limpiar solo USA
    cursor.execute("DELETE FROM portfolio_monitor WHERE moneda = 'ARS' OR moneda = 'USD'")
    
    for ticker in resumen.index:
        cant_neta = cantidades_netas.get(ticker, 0)
        if cant_neta > 0:
            ppp = round(resumen.loc[ticker, 'PPP'], 2)
            
            # Moneda
            etf_us = ['IEF', 'SGOV', 'VCIT', 'VIG', 'QUAL', 'DDI']
            moneda = 'USD' if ticker in etf_us else 'ARS'
            
            cursor.execute("""
                INSERT INTO portfolio_monitor 
                (ticker, cantidad, precio_compra, moneda, estado) 
                VALUES (%s, %s, %s, %s, 'activo')
            """, (ticker, cant_neta, ppp, moneda))
            
            print(f"✅ {ticker}: {cant_neta} x ${ppp} ({moneda})")
    
    conn.commit()
    conn.close()
    print("\n🎉 ¡¡BASE DE DATOS LISTA!!")
    
    print("\nVerifica:")
    print("SELECT ticker, cantidad, precio_compra, moneda FROM portfolio_monitor")

if __name__ == "__main__":
    actualizar_db_solo_usa()