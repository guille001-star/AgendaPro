from app import create_app, db

# Creamos la instancia de la app usando la configuración definida
app = create_app()

# Contexto para crear las tablas si no existen
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)