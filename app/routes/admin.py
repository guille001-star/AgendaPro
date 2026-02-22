from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from werkzeug.security import generate_password_hash
from sqlalchemy import func

admin = Blueprint('admin', __name__)

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
    
    # Mostramos TODOS los usuarios para gestión
    all_users = User.query.order_by(User.id.desc()).all()
    
    top_users = db.session.query(
        User.name, 
        func.count(Appointment.id).label('count')
    ).join(Appointment).group_by(User.id).order_by(func.count(Appointment.id).desc()).limit(5).all()

    return render_template('admin/panel.html', 
                           total_users=total_users,
                           total_appointments=total_appointments,
                           total_days_configured=total_days_configured,
                           all_users=all_users,
                           top_users=top_users)

# NUEVA RUTA: Resetear contraseña
@admin.route('/super-admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    # Reseteamos la contraseña a '123456'
    user.set_password('123456')
    db.session.commit()
    flash(f'Contraseña de {user.name} reseteada a: 123456')
    return redirect(url_for('admin.panel'))
