"""Ejecuta insert_30_vehicles.sql contra monitoring_innovation.db"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "monitoring_innovation.db"
sql_path = Path(__file__).parent / "insert_30_vehicles.sql"

sql = sql_path.read_text(encoding="utf-8")
idx = sql.upper().find("INSERT INTO")
if idx < 0:
    raise SystemExit("No se encontró INSERT INTO en insert_30_vehicles.sql")
sql = sql[idx:].rstrip().rstrip(";")

conn = sqlite3.connect(db_path)
try:
    before = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    conn.execute(sql)
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    print(f"Listo: {before} -> {after} vehículos (+{after - before})")
finally:
    conn.close()
