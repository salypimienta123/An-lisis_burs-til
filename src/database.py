import sqlite3

conn = sqlite3.connect("/data/bolsa.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS precios (
    fecha TEXT,
    cierre REAL
)
""")

conn.commit()
conn.close()