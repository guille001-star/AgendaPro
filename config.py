import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def format_date(value):
    """Convierte fecha YYYY-MM-DD a 'Lunes 20 de Enero'"""
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    date_obj = value
    if isinstance(value, str):
        date_obj = datetime.strptime(value, '%Y-%m-%d').date()
        
    return f"{days[date_obj.weekday()]} {date_obj.day} de {months[date_obj.month-1]}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-por-defecto-muy-dificil'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///agendapro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
