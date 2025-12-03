# from app import db, login_manager
# from flask_login import UserMixin
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime

# class User(UserMixin, db.Model):
#     __tablename__ = 'user'
    
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(64), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(256))
#     role = db.Column(db.String(20), default='student')
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    
#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)
    
#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)
    
#     def __repr__(self):
#         return f'<User {self.username}>'

# class Classroom(db.Model):
#     __tablename__ = 'classroom'
    
#     id = db.Column(db.Integer, primary_key=True)
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Classroom(db.Model):
    __tablename__ = 'classroom'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    has_projector = db.Column(db.Boolean, default=False)
    has_computers = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    bookings = db.relationship('Booking', backref='classroom', lazy='dynamic')

    def __repr__(self):
        return f'<Classroom {self.room_number}>'


class RecurringBooking(db.Model):
    __tablename__ = 'recurring_booking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    recurrence_type = db.Column(db.String(20), default='weekly')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='recurring_bookings')
    classroom = db.relationship('Classroom', backref='recurring_bookings')


class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recurring_booking_id = db.Column(db.Integer, db.ForeignKey('recurring_booking.id'), nullable=True)

    recurring_booking = db.relationship('RecurringBooking', backref='generated_bookings')


class BookingQueue(db.Model):
    __tablename__ = 'booking_queue'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    queue_position = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='waiting')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='queue_entries')
    classroom = db.relationship('Classroom', backref='queue_entries')

    def __repr__(self):
        return f'<BookingQueue user={self.user_id} classroom={self.classroom_id}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))