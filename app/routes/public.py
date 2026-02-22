from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, timedelta, date

public = Blueprint('public', __name__)

@public.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first_or_404()
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    avail = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not avail:
        return jsonify({'status': 'error', 'message': 'Día no disponible'})
    
    # FIX: Filtrar solo turnos 'reservado', ignorar 'cancelado'
    booked = Appointment.query.filter_by(professional_id=professional.id, date=selected_date, status='reservado').all()
    booked_times = [t.time for t in booked]
    
    slots = []
    current_t = datetime.combine(date.today(), avail.start_time)
    end_t = datetime.combine(date.today(), avail.end_time)
    duration = timedelta(minutes=professional.appointment_duration)
    
    while current_t.time() < end_t.time():
        slot_time = current_t.time()
        is_booked = slot_time in booked_times
        
        is_past = False
        if selected_date == date.today():
            if slot_time < datetime.now().time():
                is_past = True

        if not is_booked and not is_past:
            slots.append(slot_time.strftime('%H:%M'))
        
        current_t += duration
        
    return jsonify({'slots': slots})

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter(db.func.lower(User.slug) == slug.lower()).first_or_404()
    
    if request.method == 'POST':
        client_name = request.form.get('name')
        client_phone = request.form.get('phone')
        date_str = request.form.get('date')
        time_str = request.form.get('time_slot')
        notes = request.form.get('notes') # NUEVO
        
        if not time_str:
            flash('Por favor selecciona un horario.')
            return redirect(url_for('public.agenda', slug=slug))

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            new_appointment = Appointment(
                professional_id=professional.id,
                client_name=client_name,
                client_phone=client_phone,
                date=date_obj,
                time=time_obj,
                notes=notes # NUEVO
            )
            db.session.add(new_appointment)
            db.session.commit()
            flash('¡Turno reservado con éxito!')
        except Exception as e:
            flash('Error al reservar.')
            
        return redirect(url_for('public.agenda', slug=slug))
        
    today = date.today()
    enabled_dates = AvailableDay.query.filter_by(professional_id=professional.id)\
        .filter(AvailableDay.date >= today).order_by(AvailableDay.date).limit(30).all()
    
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_dates)
