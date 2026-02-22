from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, timedelta, date
from urllib.parse import quote

public = Blueprint('public', __name__)

@public.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter(db.func.lower(User.slug) == slug.lower()).first()
    if not professional:
        return jsonify({'status': 'error', 'message': 'Profesional no encontrado', 'slots': []})

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Fecha inválida', 'slots': []})

    avail = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not avail:
        return jsonify({'status': 'error', 'message': 'Día no habilitado', 'slots': []})

    if not avail.start_time or not avail.end_time:
         return jsonify({'status': 'error', 'message': 'Horario no configurado', 'slots': []})

    duration_minutes = professional.appointment_duration or 30
    booked = Appointment.query.filter_by(professional_id=professional.id, date=selected_date, status='reservado').all()
    booked_times = [t.time for t in booked]
    
    slots = []
    current_t = datetime.combine(date.today(), avail.start_time)
    end_t = datetime.combine(date.today(), avail.end_time)
    duration = timedelta(minutes=duration_minutes)
    
    while current_t.time() < end_t.time():
        slot_time = current_t.time()
        if slot_time not in booked_times:
            slots.append(slot_time.strftime('%H:%M'))
        current_t += duration
        
    return jsonify({'slots': slots})

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter(db.func.lower(User.slug) == slug.lower()).first_or_404()
    
    if request.method == 'POST':
        client_name = request.form.get('name')
        client_email = request.form.get('email')
        client_phone = request.form.get('phone')
        date_str = request.form.get('date')
        time_str = request.form.get('time_slot')
        notes = request.form.get('notes')
        
        if not time_str:
            flash('Por favor selecciona un horario.')
            return redirect(url_for('public.agenda', slug=slug))

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            new_appointment = Appointment(
                professional_id=professional.id,
                client_name=client_name,
                client_email=client_email,
                client_phone=client_phone,
                date=date_obj,
                time=time_obj,
                notes=notes
            )
            db.session.add(new_appointment)
            db.session.commit()
            
            # REDIRIGIR A PANTALLA DE CONFIRMACIÓN
            return render_template('public/confirmacion.html', 
                                   professional=professional, 
                                   date=date_obj, 
                                   time=time_obj,
                                   client_name=client_name)
                
        except Exception as e:
            db.session.rollback()
            print(f"Error reservando: {e}")
            flash('Error al reservar.')
            return redirect(url_for('public.agenda', slug=slug))
        
    today = date.today()
    enabled_dates = AvailableDay.query.filter_by(professional_id=professional.id)\
        .filter(AvailableDay.date >= today).order_by(AvailableDay.date).limit(30).all()
    
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_dates)
