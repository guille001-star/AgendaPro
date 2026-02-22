from app import create_app, db
from sqlalchemy import text
from flask_login import current_user

app = create_app()

# --- MIGRACIÓN URGENTE PARA RAILWAY (PostgreSQL) ---
with app.app_context():
    try:
        # Intentar agregar columna 'notes'
        print("Intentando agregar columna 'notes'...")
        db.session.execute(text('ALTER TABLE appointments ADD COLUMN notes TEXT'))
        db.session.commit()
        print("Columna 'notes' agregada exitosamente.")
    except Exception as e:
        # Si da error, es porque ya existe o problema de permisos, ignoramos
        print(f"Info notas: {e}")
        db.session.rollback()

    try:
        # Intentar agregar columna 'status' por si falta
        print("Verificando columna 'status'...")
        db.session.execute(text("ALTER TABLE appointments ADD COLUMN status VARCHAR(20) DEFAULT 'reservado'"))
        db.session.commit()
        print("Columna 'status' agregada.")
    except Exception as e:
        print(f"Info status: {e}")
        db.session.rollback()
        
    # Crear otras tablas si faltan
    db.create_all()
# ----------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
