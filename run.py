from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Crear tablas si faltan
    db.create_all()
    
    # --- RESCATE DE CONTRASEÑA ---
    # Busca tu usuario por email
    admin_user = User.query.filter_by(email='geopat001@gmail.com').first()
    if admin_user:
        # Si existe, le pone la clave 123456
        admin_user.set_password('123456')
        db.session.commit()
        print("¡CONTRASEÑA RESCATADA! Tu nueva clave es: 123456")
    else:
        print("Usuario admin no encontrado. Verifica el email en la BD.")
    # ------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
