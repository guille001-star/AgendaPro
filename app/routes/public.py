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
        except ValueError:
            flash('Formato inválido.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        day = AvailableDay.query.filter_by(professional_id=professional.id, date=apt_date).first()
        if not day:
            flash('Día no disponible.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))

        # --- LÓGICA DE PAGO ---
        if professional.appointment_price and professional.appointment_price > 0 and professional.mp_access_token:
            status = 'pendiente'
        else:
            status = 'reservado'

        new_apt = Appointment(
            professional_id=professional.id,
            date=apt_date,
            time=apt_time,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            status=status
        )
        db.session.add(new_apt)
        db.session.commit()

        if status == 'pendiente':
            try:
                sdk = mercadopago.SDK(professional.mp_access_token)
                
                base_url = request.host_url.rstrip('/')
                # Pasamos el slug en la URL de éxito para saber a dónde volver
                success_url = f"{base_url}/pago/exito/{professional.slug}"
                failure_url = f"{base_url}/pago/error/{professional.slug}"
                
                preference_data = {
                    "items": [
                        {
                            "title": f"Turno {professional.name}",
                            "quantity": 1,
                            "currency_id": "ARS",
                            "unit_price": float(professional.appointment_price)
                        }
                    ],
                    "payer": {"email": client_email},
                    "back_urls": {
                        "success": success_url,
                        "failure": failure_url,
                    },
                    "external_reference": str(new_apt.id)
                }
                
                preference_response = sdk.preference().create(preference_data)

                payment_url = None
                if 'response' in preference_response:
                    payment_url = preference_response['response'].get('init_point')
                    if not payment_url:
                        payment_url = preference_response['response'].get('sandbox_init_point')

                if payment_url:
                    return redirect(payment_url)
                else:
                    error_msg = preference_response.get('response', {}).get('message', 'Error desconocido')
                    flash(f'Error MP: {error_msg}', 'danger')
                    return redirect(url_for('public.agenda', slug=slug))

            except Exception as e:
                flash(f'Error crítico: {str(e)}', 'danger')
                return redirect(url_for('public.agenda', slug=slug))

        flash('¡Turno reservado!', 'success')
        return redirect(url_for('public.agenda', slug=slug))

    today = date.today()
    enabled_days = AvailableDay.query.filter(
        AvailableDay.professional_id == professional.id,
        AvailableDay.date >= today
    ).order_by(AvailableDay.date).all()
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_days)

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'error': 'No'}), 404
    try: selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'error': 'Fecha'}), 400
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not day: return jsonify({'message': 'No habilitado.'})
    start_time = day.start_time or dt_time(9,0)
    end_time = day.end_time or dt_time(18,0)
    duration = day.slot_duration or 30
    # IMPORTANTE: Solo mostrar como reservados los que están 'reservado' o 'pendiente' (por si pagó pero no volvió)
    apps = Appointment.query.filter_by(professional_id=professional.id, date=selected_date).filter(Appointment.status.in_(['reservado', 'pendiente'])).all()
    booked = [a.time for a in apps]
    slots = []
    curr = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)
    while curr < end:
        if curr.time() not in booked: slots.append(curr.time().strftime('%H:%M'))
        curr += timedelta(minutes=duration)
    return jsonify({'slots': slots})

# --- RUTAS DE RETORNO CON SLUG ---

@public.route('/pago/exito/<slug>')
def pago_exito(slug):
    # Buscamos el turno pendiente más reciente de este profesional para confirmarlo
    # Idealmente usaríamos el external_reference, pero así es más simple y robusto
    professional = User.query.filter_by(slug=slug).first()
    if professional:
        # Actualizar el último turno pendiente a reservado
        apt = Appointment.query.filter_by(professional_id=professional.id, status='pendiente').order_by(Appointment.id.desc()).first()
        if apt:
            apt.status = 'reservado'
            db.session.commit()
            
    flash('¡Pago realizado! Su turno está confirmado.', 'success')
    return redirect(url_for('public.agenda', slug=slug))

@public.route('/pago/error/<slug>')
def pago_error(slug):
    flash('El pago fue rechazado. Intente nuevamente.', 'danger')
    return redirect(url_for('public.agenda', slug=slug))
