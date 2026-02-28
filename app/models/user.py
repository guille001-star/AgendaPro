from app import db, login_manager
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    slug = db.Column(db.String(100), unique=True)
    # Dejamos los campos de precio para no romper la BD, pero no los usamos en la UI
    appointment_price = db.Column(db.Float, default=0.0)
    mp_access_token = db.Column(db.String(200))
    mp_public_key = db.Column(db.String(200))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
