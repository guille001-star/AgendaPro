from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # --- FILTRO JINJA ---
    @app.template_filter('format_date')
    def format_date(value):
        if value:
            return value.strftime('%d/%m/%Y')
        return ""
    # --------------------

    from app.models.user import User
    from app.models.appointment import Appointment
    from app.models.available_day import AvailableDay
    
    # --- MIGRACIÓN SEGURA ---
    with app.app_context():
        try:
            db.create_all()
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS start_time TIME'))
            db.session.execute(text('ALTER TABLE available_day ADD COLUMN IF NOT EXISTS end_time TIME'))
            db.session.commit()
            print(">>> Sistema iniciado correctamente.")
        except Exception as e:
            db.session.rollback()
            print(f">>> Nota DB: {e}")
    # ------------------------

    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.public import public
    
    # REGISTRO CON PREFIJOS CORRECTOS
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(public) # Public no necesita prefijo, sus rutas son específicas (/agenda, etc)

    return app
