from app import create_app, db
from sqlalchemy import text
import os

app = create_app()

with app.app_context():
    # 1. Crear tablas si no existen
    db.create_all()
    
    # 2. LIMPIEZA TOTAL DE PRODUCCIÓN (Solo se ejecutará una vez)
    # Verificamos si existe una variable de entorno para permitir el borrado
    # Para activarlo, crea la variable RESET_DB = true en Railway
    if os.environ.get('RESET_DB') == 'true':
        print("!!! EJECUTANDO LIMPIEZA DE BASE DE DATOS !!!")
        try:
            # Desactivamos restricciones de claves foráneas temporalmente
            db.session.execute(text('SET CONSTRAINTS ALL DEFERRED'))
            
            # Borramos tablas (PostgreSQL)
            db.session.execute(text('TRUNCATE TABLE appointments, available_day, users RESTART IDENTITY CASCADE'))
            
            db.session.commit()
            print("!!! LIMPIEZA COMPLETADA. BORRE LA VARIABLE RESET_DB AHORA !!!")
        except Exception as e:
            print(f"Error en limpieza (puede ser normal si tablas vacias): {e}")
            db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
