from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    @app.template_filter('format_date')
    def format_date(value):
        if value: return value.strftime('%d/%m/%Y')
        return ""
    from app.models.user import User
    from app.models.appointment import Appointment
    from app.models.available_day import AvailableDay
    from app.models.time_block import TimeBlock
    with app.app_context():
        try:
            db.create_all()
            print(">>> Sistema OK. Tabla TimeBlock creada.")
        except Exception as e:
            print(f">>> Error DB: {e}")
    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.public import public
    from app.routes.admin import admin
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(public)
    app.register_blueprint(admin, url_prefix='/admin')
    return app
