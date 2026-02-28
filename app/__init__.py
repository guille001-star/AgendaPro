from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.models.user import User
    from app.models.appointment import Appointment
    from app.models.available_day import AvailableDay
    
    # --- MIGRACIÓN AUTOMÁTICA PARA POSTGRESQL (RAILWAY) ---
    with app.app_context():
        try:
            # Intentar agregar columnas si no existen (PostgreSQL)
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS start_time TIME'))
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS end_time TIME'))
            db.session.commit()
            print(">>> Verificación de DB PostgreSQL OK.")
        except Exception as e:
            db.session.rollback()
            print(f">>> Info DB (puede ser normal si ya existen columnas): {e}")
    # ------------------------------------------------------

    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.public import public
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(public)

    return app
