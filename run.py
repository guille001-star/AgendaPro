from app import create_app, db
from sqlalchemy import text
import os

app = create_app()

with app.app_context():
    db.create_all()
    # Migración en caliente para agregar client_email si falta
    if os.path.exists('app.db'): 
        try:
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN client_email VARCHAR(120)'))
            db.session.commit()
            print("Columna client_email agregada localmente.")
        except: pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
