from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, date, time as dt_time, timedelta
from sqlalchemy import or_

public = Blueprint('public', __name__)

# --- RUTA PRINCIPAL DE AGENDA ---
@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        date_str = request.form['date']
        time_str = request.form['time_slot']
        client_name = request.form['name']
        client_email = request.form.get('email')
        client_phone = request.form['phone']
        notes = request.form.get('notes', '')

        try:
            apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            apt_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash('Formato de fecha u hora inválido.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        # Validar día disponible
        day = AvailableDay.query.filter_by(professional_id=professional.id, date=apt_date).first()
        if not day:
            flash('Este día no está disponible.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        # Crear turno
        new_apt = Appointment(
            professional_id=professional.id,
            date=apt_date,
            time=apt_time,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            notes=notes,
            status='reservado'
        )
        db.session.add(new_apt)
        db.session.commit()

        flash('¡Turno reservado con éxito!', 'success')
        return redirect(url_for('public.agenda', slug=slug))

    # GET: Mostrar agenda
    today = date.today()
    enabled_days = AvailableDay.query.filter(
        AvailableDay.professional_id == professional.id,
        AvailableDay.date >= today
    ).order_by(AvailableDay.date).all()
    
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_days)

# --- RUTA PARA OBTENER HORARIOS (AJAX) ---
@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional:
        return jsonify({'error': 'Profesional no encontrado'}), 404

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida'}), 400

    # Buscar el día habilitado
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    
    if not day:
        return jsonify({'message': 'Día no habilitado por el profesional.'})

    # Determinar horario de atención
    # Si start_time es NULL (datos antiguos), usar 09:00 - 18:00 por defecto
    start_time = day.start_time if day.start_time else dt_time(9, 0)
    end_time = day.end_time if day.end_time else dt_time(18, 0)

    # Buscar turnos ya reservados
    appointments = Appointment.query.filter_by(
        professional_id=professional.id,
        date=selected_date,
        status='reservado'
    ).all()
    
    booked_times = [apt.time for apt in appointments]

    # Generar slots cada 30 mins
    slots = []
    current_dt = datetime.combine(selected_date, start_time)
    end_dt = datetime.combine(selected_date, end_time)

    while current_dt < end_dt:
        slot_time = current_dt.time()
        if slot_time not in booked_times:
            slots.append(slot_time.strftime('%H:%M'))
        current_dt += timedelta(minutes=30)

    return jsonify({'slots': slots})
