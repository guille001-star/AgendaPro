from app import db
from datetime import datetime

class AvailableDay(db.Model):
    __tablename__ = 'available_day'
    id = db.Column(db.Integer, primary_key=True)
    # CORREGIDO: Apunta a 'users.id'
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    
    def __repr__(self):
        return f'<AvailableDay {self.date}>'
