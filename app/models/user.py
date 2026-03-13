from app import db, login_manager
from flask_login import UserMixin
from flask import current_app
from cryptography.fernet import Fernet
import base64
import hashlib

# --- FUNCIÓN DE ENCRIPTACIÓN ROBUSTA ---
def get_cipher():
    # Usa el SECRET_KEY de la app para generar una clave única de 32 bytes
    key = hashlib.sha256(current_app.config['SECRET_KEY'].encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    slug = db.Column(db.String(100), unique=True)
    
    # --- CAMPOS MERCADO PAGO ---
    # Columna real en BD (almacena el token encriptado)
    _mp_access_token = db.Column("mp_access_token", db.String(500))
    mp_public_key = db.Column(db.String(200))
    appointment_price = db.Column(db.Float, default=0.0)

    # --- PROPIEDAD INTELIGENTE (ENCRIPTA AL GUARDAR) ---
    @property
    def mp_access_token(self):
        """Desencripta el token al leerlo."""
        if not self._mp_access_token:
            return None
        try:
            # Intentar desencriptar
            cipher = get_cipher()
            return cipher.decrypt(self._mp_access_token.encode()).decode()
        except:
            # Si falla (token viejo sin encriptar), devolver tal cual
            return self._mp_access_token

    @mp_access_token.setter
    def mp_access_token(self, value):
        """Encripta el token al guardarlo."""
        if not value:
            self._mp_access_token = None
        else:
            try:
                # Intentar encriptar
                cipher = get_cipher()
                self._mp_access_token = cipher.encrypt(value.encode()).decode()
            except:
                # Si falla (contexto de app no listo), guardar temporalmente (pasará en tests locales)
                self._mp_access_token = value

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
