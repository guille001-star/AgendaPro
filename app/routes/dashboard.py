from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.schedule import Schedule
from datetime import datetime, date

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    public_url = url_for('public.agenda', slug=current_user.slug, _external=True)
    
    # Turnos de HOY
    hoy = date.today()
    turnos_hoy = Appointment.query.filter_by(professional_id=current_user.id)\
        .filter(Appointment.date == hoy).order_by(Appointment.time).all()
        
    # Proximos turnos (Futuros)
    proximos = Appointment.query.filter_by(professional_id=current_user.id)\
        .filter(Appointment.date > hoy).order_by(Appointment.date, Appointment.time).limit(10).all()
        
    # Historial (Pasados)
    historial = Appointment.query.filter_by(professional_id=current_user.id)\
        .filter(Appointment.date < hoy).order_by(Appointment.date.desc()).limit(5).all()
        
    horarios = Schedule.query.filter_by(professional_id=current_user.id).all()
    
    return render_template('dashboard/index.html', 
                           turnos_hoy=turnos_hoy, 
                           proximos=proximos, 
                           historial=historial, 
                           horarios=horarios, 
                           public_url=public_url)

@dashboard.route('/settings', methods=['POST'])
@login_required
def settings():
    duration = request.form.get('duration')
    if duration:
        current_user.appointment_duration = int(duration)
        db.session.commit()
        flash('Duración actualizada.')
    return redirect(url_for('dashboard.index'))

@dashboard.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    day = request.form.get('day')
    start = request.form.get('start')
    end = request.form.get('end')
    if day and start and end:
        start_time = datetime.strptime(start, '%H:%M').time()
        end_time = datetime.strptime(end, '%H:%M').time()
        new_schedule = Schedule(
            professional_id=current_user.id,
            day_of_week=int(day),
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(new_schedule)
        db.session.commit()
        flash('Horario agregado.')
    return redirect(url_for('dashboard.index'))

@dashboard.route('/delete_schedule/<int:id>')
@login_required
def delete_schedule(id):
    horario = Schedule.query.get_or_404(id)
    if horario.professional_id == current_user.id:
        db.session.delete(horario)
        db.session.commit()
        flash('Horario eliminado.')
    return redirect(url_for('dashboard.index'))
