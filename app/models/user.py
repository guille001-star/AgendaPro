from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Campos específicos para la agenda
    profession = db.Column(db.String(100), nullable=True) # Ej: Psicólogo, Dentista
    slug = db.Column(db.String(100), unique=True, nullable=True) # URL amigable (ej: app.com/dr-perez)
    appointment_duration = db.Column(db.Integer, default=30) # Minutos por turno
    
    # Relación con los turnos
    appointments = db.relationship('Appointment', backref='professional', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Función requerida por Flask-Login para cargar usuario
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))