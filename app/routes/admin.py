from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay

admin = Blueprint('admin', __name__)

# Decorador simple para proteger la ruta (Solo el primer usuario es admin)
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return "Acceso denegado", 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin.route('/super-admin')
@login_required
@admin_required
def panel():
    total_users = User.query.count()
    total_appointments = Appointment.query.count()
    total_days_configured = AvailableDay.query.count()
    
    # Ultimos 5 profesionales registrados
    latest_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Top profesionales con mas turnos (requiere query especial)
    # Usamos una consulta raw simple para contar
    from sqlalchemy import func
    top_users = db.session.query(
        User.name, 
        func.count(Appointment.id).label('count')
    ).join(Appointment).group_by(User.id).order_by(func.count(Appointment.id).desc()).limit(5).all()

    return render_template('admin/panel.html', 
                           total_users=total_users,
                           total_appointments=total_appointments,
                           total_days_configured=total_days_configured,
                           latest_users=latest_users,
                           top_users=top_users)
