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
        try:
            apt_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            apt_time = datetime.strptime(request.form['time_slot'], '%H:%M').time()
            new_apt = Appointment(professional_id=professional.id, date=apt_date, time=apt_time, client_name=request.form['name'], client_email=request.form.get('email'), client_phone=request.form.get('phone'), status='reservado')
            db.session.add(new_apt); db.session.commit()
            flash('¡Turno reservado!', 'success')
        except: flash('Error al reservar.', 'danger')
        return redirect(url_for('public.agenda', slug=slug))

    today = date.today()
    enabled_days = AvailableDay.query.filter(AvailableDay.professional_id == professional.id, AvailableDay.date >= today).order_by(AvailableDay.date).all()
    # CAMBIO AQUÍ: de 'public/agenda.html' a 'pages/agenda.html'
    return render_template('pages/agenda.html', professional=professional, enabled_dates=enabled_days)

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'error': 'No encontrado'}), 404
    try: selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'error': 'Fecha invalida'}), 400
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not day: return jsonify({'message': 'Dia no habilitado.'})
    start_time = day.start_time if day.start_time else dt_time(9, 0)
    end_time = day.end_time if day.end_time else dt_time(18, 0)
    appointments = Appointment.query.filter_by(professional_id=professional.id, date=selected_date, status='reservado').all()
    booked = [a.time for a in appointments]
    slots = []
    curr = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)
    while curr < end:
        if curr.time() not in booked: slots.append(curr.time().strftime('%H:%M'))
        curr += timedelta(minutes=30)
    return jsonify({'slots': slots})
