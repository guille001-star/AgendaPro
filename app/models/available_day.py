from app import db

class AvailableDay(db.Model):
    __tablename__ = 'available_days'
    
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('professional_id', 'date', name='unique_prof_date'),)
