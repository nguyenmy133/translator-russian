import sqlite3

conn = sqlite3.connect("translator.db")
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")

for table in tables:
    t_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
    count = cursor.fetchone()[0]
    print(f"Table '{t_name}' has {count} rows.")
    
    if count > 0:
        cursor.execute(f"SELECT * FROM {t_name} LIMIT 5")
        rows = cursor.fetchall()
        print(f"Sample rows from '{t_name}':")
        for row in rows:
            print(row)

conn.close()
