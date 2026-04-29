import pandas as pd

df = pd.read_csv('OperacionesFinalizadas.csv', sep=';', encoding='latin1')
df.columns = [col.strip() for col in df.columns]

print("🔍 VALORES REALES 'Tipo Transacción':")
print(df['Tipo Transacción'].value_counts())
print("\n🔍 Primeras 10 filas:")
print(df[['Tipo Transacción', 'Simbolo', 'Cantidad']].head(10))
print("\n🔍 Texto exacto (minúsculas):")
print(df['Tipo Transacción'].str.lower().unique()[:10])