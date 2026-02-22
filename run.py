from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    db.create_all()
    
    # --- RESCATE ---
    # Buscamos al primer usuario (ID 1) que siempre es el Admin
    admin_user = User.query.get(1)
    
    if admin_user:
        print(f"----------------------------------------")
        print(f"RESCATE DE CUENTA:")
        print(f"Usuario encontrado: {admin_user.name}")
        print(f"Email registrado: {admin_user.email}")
        print(f"Nueva contraseña: 123456")
        print(f"----------------------------------------")
        
        admin_user.set_password('123456')
        db.session.commit()
    else:
        print("No se encontró ningún usuario. Debes registrarte primero.")
        
    # Listar todos los usuarios para debug
    all_users = User.query.all()
    print("LISTA DE USUARIOS EN LA BASE DE DATOS:")
    for u in all_users:
        print(f"ID: {u.id} | Email: {u.email} | Nombre: {u.name}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
