import sqlite3
import os

# Ruta de la BD
db_path = 'instance/agendapro.db' # Ajusta si tu BD está en otro lado
if not os.path.exists(db_path):
    print("No se encontró la base de datos local, asumiendo que está en la nube o ya actualizada.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar si existen las columnas
    cursor.execute("PRAGMA table_info(available_day)")
    columns = [col[1] for col in cursor.fetchall()]
    
    changes = False
    if 'start_time' not in columns:
        print("Agregando columna start_time...")
        cursor.execute("ALTER TABLE available_day ADD COLUMN start_time TIME")
        changes = True
    if 'end_time' not in columns:
        print("Agregando columna end_time...")
        cursor.execute("ALTER TABLE available_day ADD COLUMN end_time TIME")
        changes = True
        
    if changes:
        conn.commit()
        print("Base de datos actualizada correctamente.")
    else:
        print("La base de datos ya tenía las columnas.")
    
    conn.close()
