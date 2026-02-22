from app import create_app, db
from flask_migrate import Migrate # Por si usas migrate en el futuro
import sqlite3 # Para la migración local simple
import os

app = create_app()

# --- Mini Script de Migración Local (SQLite) ---
# Esto agrega la columna 'notes' si no existe, sin borrar datos.
# En PostgreSQL (Railway) SQLAlchemy lo maneja diferente, pero esto es para tu PC local.
if os.path.exists('app.db'): # Chequeo simple si existe DB local
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        # Intentar agregar columna
        cursor.execute("ALTER TABLE appointments ADD COLUMN notes TEXT")
        conn.commit()
        print("Columna 'notes' agregada a la base de datos local.")
    except sqlite3.OperationalError:
        # Si da error es porque ya existe, todo bien
        pass
    finally:
        conn.close()
# -----------------------------------------------

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
