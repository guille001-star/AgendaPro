from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, timedelta, date
import calendar

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    public_url = url_for('public.agenda', slug=current_user.slug, _external=True)
    
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    cal = calendar.Calendar()
    month_days = cal.itermonthdays2(year, month)
    
    enabled_dates = AvailableDay.query.filter_by(professional_id=current_user.id).all()
    enabled_map = {d.date: d for d in enabled_dates}
    
    calendar_data = []
    for day, weekday in month_days:
        if day == 0:
            calendar_data.append({'type': 'empty'})
        else:
            current_date = date(year, month, day)
            is_enabled = current_date in enabled_map
            is_past = current_date < date.today()
            
            calendar_data.append({
                'type': 'day',
                'day': day,
                'date': current_date,
                'is_enabled': is_enabled,
                'is_past': is_past,
                'start': enabled_map.get(current_date).start_time if is_enabled else None,
                'end': enabled_map.get(current_date).end_time if is_enabled else None
            })

    hoy = date.today()
    turnos_hoy = Appointment.query.filter_by(professional_id=current_user.id)\
        .filter(Appointment.date == hoy).order_by(Appointment.time).all()
    proximos = Appointment.query.filter_by(professional_id=current_user.id)\
        .filter(Appointment.date > hoy).order_by(Appointment.date, Appointment.time).limit(10).all()
    
    month_name = datetime(year, month, 1).strftime("%B").capitalize()

    return render_template('dashboard/index.html', 
                           turnos_hoy=turnos_hoy, proximos=proximos,
                           public_url=public_url,
                           calendar_data=calendar_data, 
                           year=year, month=month, month_name=month_name)

@dashboard.route('/settings', methods=['POST'])
@login_required
def settings():
    duration = request.form.get('duration')
    if duration:
        current_user.appointment_duration = int(duration)
        db.session.commit()
        flash('Duración actualizada.')
    return redirect(url_for('dashboard.index'))

@dashboard.route('/save_day', methods=['POST'])
@login_required
def save_day():
    data = request.get_json()
    date_str = data.get('date')
    start_str = data.get('start_time')
    end_str = data.get('end_time')
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    start_obj = datetime.strptime(start_str, '%H:%M').time()
    end_obj = datetime.strptime(end_str, '%H:%M').time()
    
    avail = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
    
    if avail:
        avail.start_time = start_obj
        avail.end_time = end_obj
    else:
        new_avail = AvailableDay(
            professional_id=current_user.id,
            date=date_obj,
            start_time=start_obj,
            end_time=end_obj
        )
        db.session.add(new_avail)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@dashboard.route('/delete_day', methods=['POST'])
@login_required
def delete_day():
    data = request.get_json()
    date_str = data.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    avail = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
    if avail:
        db.session.delete(avail)
        db.session.commit()
    return jsonify({'status': 'success'})
