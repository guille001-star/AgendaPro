from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, date, time as dt_time, timedelta

public = Blueprint('public', __name__)

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        # Lógica simple de reserva (Sin pago)
        date_str = request.form['date']
        time_str = request.form['time_slot']
        client_name = request.form['name']
        client_email = request.form.get('email')
        client_phone = request.form.get('phone')
        
        try:
            apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            apt_time = datetime.strptime(time_str, '%H:%M').time()
        except:
            flash('Error en fecha u hora.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        new_apt = Appointment(
            professional_id=professional.id,
            date=apt_date,
            time=apt_time,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            status='reservado'
        )
        db.session.add(new_apt)
        db.session.commit()
        flash('¡Turno reservado con éxito!', 'success')
        return redirect(url_for('public.agenda', slug=slug))

    # GET
    today = date.today()
    enabled_days = AvailableDay.query.filter(
        AvailableDay.professional_id == professional.id,
        AvailableDay.date >= today
    ).order_by(AvailableDay.date).all()
    
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_days)

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'error': 'No encontrado'}), 404
    try: selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'error': 'Fecha inválida'}), 400

    day = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not day: return jsonify({'message': 'Día no habilitado.'})

    start_time = day.start_time if day.start_time else dt_time(9, 0)
    end_time = day.end_time if day.end_time else dt_time(18, 0)

    appointments = Appointment.query.filter_by(professional_id=professional.id, date=selected_date, status='reservado').all()
    booked_times = [apt.time for apt in appointments]

    slots = []
    current_dt = datetime.combine(selected_date, start_time)
    end_dt = datetime.combine(selected_date, end_time)

    while current_dt < end_dt:
        slot_time = current_dt.time()
        if slot_time not in booked_times: slots.append(slot_time.strftime('%H:%M'))
        current_dt += timedelta(minutes=30)

    return jsonify({'slots': slots})
