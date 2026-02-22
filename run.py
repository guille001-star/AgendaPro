from app import create_app, db
import sqlite3 
import os

app = create_app()

# --- Mini Script de Migración Local (SQLite) ---
if os.path.exists('app.db'): 
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE appointments ADD COLUMN notes TEXT")
        conn.commit()
        print("Columna 'notes' agregada a la base de datos local.")
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
# -----------------------------------------------

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
