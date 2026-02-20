from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

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
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Verificar si el usuario ya existe
        user = User.query.filter_by(email=email).first()
        if user:
            flash('El email ya está registrado.')
            return redirect(url_for('auth.register'))
        
        # Crear nuevo usuario
        new_user = User(email=email, name=name)
        new_user.set_password(password)
        # Generamos un slug simple para la URL (ej: nombre-apellido)
        new_user.slug = name.lower().replace(" ", "-")
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html', registro=True)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))