import pandas as pd

# 1. Cargar el CSV con la codificación correcta
try:
    df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
except FileNotFoundError:
    print("No se encontró el archivo. Asegurate de que esté en la misma carpeta.")
    exit()

# Limpiar espacios en los nombres de las columnas
df.columns = [col.strip() for col in df.columns]

# Identificar columnas clave (por si cambian los nombres con tildes)
col_simbolo = 'Simbolo'
col_precio = 'Precio Ponderado'
col_cantidad = 'Cantidad'
col_tipo = [c for c in df.columns if 'Tipo' in c][0] # Busca la columna de "Tipo Transacción"

# Convertir precios y cantidades a números (manejando la coma decimal de Excel)
df[col_cantidad] = pd.to_numeric(df[col_cantidad].astype(str).str.replace(',', '.'), errors='coerce')
df[col_precio] = pd.to_numeric(df[col_precio].astype(str).str.replace(',', '.'), errors='coerce')

# 2. Filtrar solo las COMPRAS para calcular el precio de entrada
compras = df[df[col_tipo].str.contains('Compra', na=False)].copy()
compras['Costo_Total'] = compras[col_cantidad] * compras[col_precio]

# 3. Agrupar por Activo
resumen = compras.groupby(col_simbolo).agg({
    col_cantidad: 'sum',
    'Costo_Total': 'sum'
})

# Calcular el Precio Promedio Ponderado (PPP)
resumen['PPP'] = resumen['Costo_Total'] / resumen[col_cantidad]

print("--- Datos procesados para tu Base de Datos ---")
print(resumen[['PPP']])