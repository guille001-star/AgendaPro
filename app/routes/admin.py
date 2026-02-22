from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from sqlalchemy import text
import os

admin = Blueprint('admin', __name__)

@admin.route('/super-admin')
@login_required
def index():
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
    user.set_password('123456')
    db.session.commit()
    flash(f'Password de {user.name} reseteado a 123456')
    return redirect(url_for('admin.index'))

# --- RUTA DE EMERGENCIA CORREGIDA (SIN is_admin) ---
@admin.route('/factory-reset')
def factory_reset():
    if os.environ.get('RESET_DB') != 'true':
        return "<h1>Acceso Denegado</h1><p>La variable RESET_DB no está activa.</p>", 403

    try:
        print(">>> INICIANDO LIMPIEZA TOTAL <<<")
        db.session.execute(text('TRUNCATE TABLE appointments, available_days, users RESTART IDENTITY CASCADE'))
        db.session.commit()
        
        # Crear Usuario Admin (Sin is_admin)
        admin = User(
            name='Guillermo Oyarzo',
            email='geopat001@gmail.com',
            slug='guillermo-oyarzo'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        return """
        <h1 style='color:green;font-family:sans-serif'>¡ÉXITO!</h1>
        <p>La base de datos ha sido limpiada.</p>
        <p>Tu usuario Admin (ID 1) ha sido creado.</p>
        <ul>
            <li><b>Email:</b> geopat001@gmail.com</li>
            <li><b>Clave:</b> admin123</li>
        </ul>
        <a href='/auth/login' style='background:indigo;color:white;padding:10px 20px;text-decoration:none;border-radius:5px'>Ir a Login</a>
        <p style="color:red"><b>IMPORTANTE:</b> Borra la variable RESET_DB de Railway ahora.</p>
        """
    except Exception as e:
        db.session.rollback()
        return f"<h1>Error</h1><pre>{e}</pre>"
