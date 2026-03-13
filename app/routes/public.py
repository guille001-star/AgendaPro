from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, date, time as dt_time, timedelta
import mercadopago

public = Blueprint('public', __name__)

@public.route('/')
def home():
    return redirect(url_for('auth.login'))

@public.route('/directorio')
def lista():
    users = User.query.all()
    return render_template('public/lista.html', users=users)

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'POST':
        date_str = request.form['date']
        time_str = request.form['time_slot']
        client_name = request.form['name']
        client_email = request.form.get('email')
        client_phone = request.form.get('phone')

        try:
            apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            apt_time = datetime.strptime(time_str, '%H:%M').time()
        except:
            flash('Error en datos.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        day = AvailableDay.query.filter_by(professional_id=professional.id, date=apt_date).first()
        if not day:
            flash('Dia no disponible.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        requiere_pago = professional.appointment_price and professional.appointment_price > 0 and professional.mp_access_token

        status = 'pendiente' if requiere_pago else 'reservado'
        
        new_apt = Appointment(
            professional_id=professional.id, date=apt_date, time=apt_time,
            client_name=client_name, client_email=client_email, client_phone=client_phone, status=status
        )
        db.session.add(new_apt)
        db.session.commit()

        if requiere_pago:
            try:
                sdk = mercadopago.SDK(professional.mp_access_token) 
                base_url = request.host_url.rstrip('/')
                
                preference_data = {
                    "items": [{
                        "title": f"Turno {professional.name} - {apt_date}",
                        "quantity": 1,
                        "currency_id": "ARS",
                        "unit_price": float(professional.appointment_price)
                    }],
                    "payer": {"email": client_email},
                    "back_urls": {
                        "success": f"{base_url}/pago/exito",
                        "failure": f"{base_url}/pago/error",
                    },
                    "auto_return": "approved",
                    "external_reference": str(new_apt.id)
                }
                
                pref_response = sdk.preference().create(preference_data)
                pay_url = pref_response["response"].get("init_point") or pref_response["response"].get("sandbox_init_point")
                
                if pay_url:
                    return redirect(pay_url)
                else:
                    flash('Error al generar link de pago.', 'danger')
                    db.session.delete(new_apt); db.session.commit()
            except Exception as e:
                flash(f'Error MP: {str(e)}', 'danger')
                db.session.delete(new_apt); db.session.commit()
        
        flash('¡Turno reservado!', 'success')
        return redirect(url_for('public.agenda', slug=slug))

    today = date.today()
    enabled_days = AvailableDay.query.filter(AvailableDay.professional_id == professional.id, AvailableDay.date >= today).order_by(AvailableDay.date).all()
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_days)

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'error': 'No'}), 404
    try: d = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'error': 'Fecha'}), 400
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=d).first()
    if not day: return jsonify({'message': 'No habilitado.'})
    
    start = day.start_time or dt_time(9,0)
    end = day.end_time or dt_time(18,0)
    dur = day.slot_duration or 30
    
    apps = Appointment.query.filter_by(professional_id=professional.id, date=d).filter(Appointment.status.in_(['reservado', 'pendiente'])).all()
    booked = [a.time for a in apps]
    
    slots = []
    curr = datetime.combine(d, start)
    end_dt = datetime.combine(d, end)
    while curr < end_dt:
        if curr.time() not in booked: slots.append(curr.time().strftime('%H:%M'))
        curr += timedelta(minutes=dur)
    return jsonify({'slots': slots})

# --- RETORNO MERCADO PAGO (MEJORADO) ---
@public.route('/pago/exito')
def pago_exito():
    ref = request.args.get('external_reference')
    if ref:
        apt = Appointment.query.get(int(ref))
        if apt and apt.status == 'pendiente':
            apt.status = 'reservado'
            db.session.commit()
            
            # REDIRIGIR A LA AGENDA DEL PROFESIONAL
            professional = User.query.get(apt.professional_id)
            if professional:
                flash('¡Pago confirmado! Su turno está reservado.', 'success')
                return redirect(url_for('public.agenda', slug=professional.slug))
    
    flash('Pago recibido.', 'success')
    return redirect(url_for('public.home'))

@public.route('/pago/error')
def pago_error():
    flash('El pago fue rechazado. Intente nuevamente.', 'danger')
    return redirect(url_for('public.home'))
