import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Listar todas as tabelas
print("=== TABELAS ===")
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for table in tables:
    print(f"  - {table[0]}")

# Se a tabela vendas existir, mostrar sua estrutura
if ('vendas',) in tables:
    print("\n=== ESTRUTURA DA TABELA VENDAS ===")
    schema = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vendas'").fetchone()
    print(schema[0])

    print("\n=== DADOS DA TABELA VENDAS ===")
    rows = cursor.execute("SELECT * FROM vendas").fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("  (tabela vazia)")

conn.close()
