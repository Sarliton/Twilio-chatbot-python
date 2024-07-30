import pandas as pd
import sqlite3

# Carregar o arquivo Excel
excel_file = 'clientes.xlsx'  # Substitua pelo caminho do seu arquivo Excel
df = pd.read_excel(excel_file)

# Conectar ao banco de dados SQLite (ou criar um novo)
conn = sqlite3.connect('clientes.db')

# Converter o DataFrame para uma tabela SQLite
df.to_sql('clientes', conn, if_exists='replace', index=False)

# Fechar a conexão
conn.close()
