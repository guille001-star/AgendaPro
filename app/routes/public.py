from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from datetime import datetime, timedelta

public = Blueprint('public', __name__)

@public.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter(db.func.lower(User.slug) == slug.lower()).first_or_404()
    
    if request.method == 'POST':
        client_name = request.form.get('name')
        client_phone = request.form.get('phone')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        
        print(f"--- NUEVA RESERVA RECIBIDA ---") # Log en consola
        print(f"Cliente: {client_name}, Tel: {client_phone}")
        print(f"Fecha: {date_str}, Hora: {time_str}")
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            new_appointment = Appointment(
                professional_id=professional.id,
                client_name=client_name,
                client_phone=client_phone,
                date=date_obj,
                time=time_obj
            )
            db.session.add(new_appointment)
            db.session.commit()
            print("Guardado en BD correctamente.")
            flash('¡Turno reservado con éxito!')
        except Exception as e:
            print(f"ERROR al guardar: {e}")
            flash('Hubo un error al reservar.')
            
        return redirect(url_for('public.agenda', slug=professional.slug))
        
    today = datetime.today().date()
    available_days = [today + timedelta(days=i) for i in range(7)]
    return render_template('public/agenda.html', professional=professional, days=available_days)
