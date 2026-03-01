from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Email o contraseña incorrectos.')
            
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Lógica de registro simple (opcional, si decides reabrirla)
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('El email ya existe.')
            return redirect(url_for('auth.register'))
            
        user = User(email=email, name=name, slug=name.lower().replace(" ", "-"))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# --- NUEVA RUTA: CAMBIAR CLAVE ---
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pass = request.form.get('current_password')
        new_pass = request.form.get('new_password')
        confirm_pass = request.form.get('confirm_password')
        
        if not current_user.check_password(current_pass):
            flash('La contraseña actual es incorrecta.')
            return redirect(url_for('auth.change_password'))
            
        if new_pass != confirm_pass:
            flash('La nueva contraseña no coincide.')
            return redirect(url_for('auth.change_password'))
            
        if len(new_pass) < 4:
            flash('La contraseña debe tener al menos 4 caracteres.')
            return redirect(url_for('auth.change_password'))
            
        current_user.set_password(new_pass)
        db.session.commit()
        flash('Contraseña actualizada exitosamente.')
        return redirect(url_for('dashboard.index'))
        
    return render_template('auth/change_password.html')
