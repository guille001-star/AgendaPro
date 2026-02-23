from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from sqlalchemy import text
import os
import re

admin = Blueprint('admin', __name__)

# Función simple para generar slug (nombre-url)
def generate_slug(name):
    # Elimina caracteres raros, pasa a minúsculas y reemplaza espacios por guiones
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', name).lower().strip()
    return re.sub(r'[\s]+', '-', clean)

@admin.route('/super-admin')
@login_required
def index():
    if current_user.id != 1:
        return "Acceso denegado", 403
    
    # Mostrar todos los usuarios menos uno mismo
    users = User.query.filter(User.id != current_user.id).order_by(User.id.desc()).all()
    return render_template('admin/index.html', users=users)

# Ruta para NUEVO PROFESIONAL (Formulario)
@admin.route('/super-admin/nuevo', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.id != 1:
        return "Acceso denegado", 403

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('admin.new_user'))

        # Verificar si email ya existe
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('El email ya está registrado.')
            return redirect(url_for('admin.new_user'))

        # Crear usuario
        slug = generate_slug(name)
        
        # Asegurar slug único (si ya existe juan-perez, probar juan-perez-2)
        if User.query.filter_by(slug=slug).first():
            slug = slug + "-" + str(User.query.count())

        new_professional = User(name=name, email=email, slug=slug)
        new_professional.set_password(password)
        
        db.session.add(new_professional)
        db.session.commit()
        
        flash(f'Profesional {name} creado exitosamente.')
        return redirect(url_for('admin.index'))

    return render_template('admin/create_user.html')

# Resetar clave
@admin.route('/super-admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.id != 1:
        return "Acceso denegado", 403
    user = User.query.get_or_404(user_id)
    new_pass = 'cliente123'
    user.set_password(new_pass)
    db.session.commit()
    flash(f'Password de {user.name} reseteado a: {new_pass}')
    return redirect(url_for('admin.index'))

# Ruta de limpieza (Mover o borrar después de usar)
@admin.route('/factory-reset')
def factory_reset():
    if os.environ.get('RESET_DB') != 'true':
        return "<h1>Acceso Denegado</h1>", 403
    try:
        db.session.execute(text('TRUNCATE TABLE appointments, available_days, users RESTART IDENTITY CASCADE'))
        db.session.commit()
        admin = User(name='Admin', email='admin@admin.com', slug='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        return "OK"
    except Exception as e:
        return str(e)
