from app import create_app, db
from sqlalchemy import text
import os

app = create_app()

with app.app_context():
    # 1. Crear tablas si no existen
    db.create_all()
    
    # 2. Intentar agregar la columna 'client_email' si falta (Solo para PostgreSQL/Producción)
    # Usamos 'DATABASE_URL' para detectar si estamos en Railway
    database_url = os.environ.get('DATABASE_URL')
    if database_url and 'postgresql' in database_url:
        try:
            print("Verificando estructura de base de datos PostgreSQL...")
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN client_email VARCHAR(120)'))
            db.session.commit()
            print("Columna client_email agregada exitosamente.")
        except Exception as e:
            # Si la columna ya existe, dará error y lo ignoramos
            if "already exists" in str(e) or "already exists" in str(e).lower():
                print("La columna client_email ya existe. Todo ok.")
            else:
                print(f"Error migrando DB (puede ser normal si ya existe): {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
