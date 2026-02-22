from app import create_app, db
from sqlalchemy import text, inspect
import os

app = create_app()

# --- FUNCIÓN DE AUTO-MIGRACIÓN (PostgreSQL y SQLite) ---
def upgrade_db():
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('appointments')]
        
        # 1. Agregar columna 'notes' si falta
        if 'notes' not in columns:
            try:
                db.session.execute(text('ALTER TABLE appointments ADD COLUMN notes TEXT'))
                db.session.commit()
                print("Columna 'notes' agregada exitosamente.")
            except Exception as e:
                print(f"Error o columna ya existente: {e}")
                db.session.rollback()

        # 2. Agregar columna 'status' si falta (por si acaso)
        if 'status' not in columns:
            try:
                # Default 'reservado' para que no rompa
                db.session.execute(text("ALTER TABLE appointments ADD COLUMN status VARCHAR(20) DEFAULT 'reservado'"))
                db.session.commit()
                print("Columna 'status' agregada exitosamente.")
            except Exception as e:
                print(f"Error o columna ya existente: {e}")
                db.session.rollback()

        # Crear tablas nuevas si no existen (ej: available_days)
        db.create_all()

upgrade_db()
# -------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
