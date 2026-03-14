from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
# Creamos el limitador (inactivo hasta init_app)
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # ProxyFix asegura que Railway vea la IP real del usuario
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ACTIVAR LIMITADOR
    limiter.init_app(app)

    @app.template_filter('format_date')
    def format_date(value):
        if value: return value.strftime('%d/%m/%Y')
        return ""

    from app.models.user import User
    from app.models.appointment import Appointment
    from app.models.available_day import AvailableDay

    with app.app_context():
        try:
            db.create_all()
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS start_time TIME'))
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS end_time TIME'))
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS slot_duration INTEGER DEFAULT 30'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS mp_access_token VARCHAR(200)'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS mp_public_key VARCHAR(200)'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS appointment_price FLOAT DEFAULT 0'))
            db.session.commit()
            print(">>> Sistema iniciado correctamente.")
        except Exception as e:
            db.session.rollback()
            print(f">>> Nota DB: {e}")

    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.public import public
    from app.routes.admin import admin

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(public)
    app.register_blueprint(admin, url_prefix='/admin')

    return app
