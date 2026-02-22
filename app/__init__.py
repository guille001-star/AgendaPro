from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config, format_date
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app) # Iniciar Mail

    app.jinja_env.filters['format_date'] = format_date

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    from app.routes.auth import auth as auth_bp
    from app.routes.dashboard import dashboard as dash_bp
    from app.routes.public import public as public_bp
    from app.routes.admin import admin as admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dash_bp, url_prefix='/dashboard')
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    from app.models.user import User
    from app.models.appointment import Appointment
    from app.models.available_day import AvailableDay

    return app
