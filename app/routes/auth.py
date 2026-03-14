from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
import uuid

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
        flash('Credenciales incorrectas.', 'danger')
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm: flash('No coinciden', 'danger'); return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first(): flash('Ya existe cuenta.', 'danger'); return redirect(url_for('auth.register'))
        new_user = User(email=email, name=name, slug=uuid.uuid4().hex[:8])
        new_user.set_password(password)
        db.session.add(new_user); db.session.commit()
        flash('Cuenta creada.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form.get('old_password')
        new = request.form.get('new_password')
        if current_user.check_password(old):
            current_user.set_password(new); db.session.commit()
            flash('Actualizada.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Incorrecta.', 'danger')
    return render_template('auth/change_password.html')
