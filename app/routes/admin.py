from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay

admin = Blueprint('admin', __name__)

@admin.route('/super-admin')
@login_required
def index():
    # Solo el usuario ID 1 (el primero en registrarse) es admin
    if current_user.id != 1:
        return "Acceso denegado", 403
    
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('admin/index.html', users=users)

@admin.route('/super-admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.id != 1:
        return "Acceso denegado", 403
    
    user = User.query.get_or_404(user_id)
    user.set_password('123456') # Password temporal
    db.session.commit()
    flash(f'Password de {user.name} reseteado a 123456')
    return redirect(url_for('admin.index'))

# RUTA DE LIMPIEZA (USAR Y LUEGO ELIMINAR O COMENTAR)
@admin.route('/limpiar-base-datos')
@login_required
def clean_db():
    if current_user.id != 1:
        return "Acceso denegado", 403
    
    try:
        # Borrar turnos
        Appointment.query.delete()
        # Borrar días disponibles
        AvailableDay.query.delete()
        # Borrar usuarios (menos el admin actual)
        User.query.filter(User.id != current_user.id).delete()
        
        db.session.commit()
        return "<h1>Limpieza exitosa!</h1><p>Todos los datos de prueba han sido borrados.<br><a href='/dashboard'>Volver al Dashboard</a></p>"
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"
