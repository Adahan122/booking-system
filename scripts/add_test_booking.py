from app import create_app, db
from app.models import User, Classroom, Booking
from datetime import date, datetime

app = create_app()

with app.app_context():
    # Найти или создать аудиторию
    classroom = Classroom.query.first()
    if not classroom:
        classroom = Classroom(room_number='101', capacity=20, floor=1)
        db.session.add(classroom)
        db.session.commit()
        print('Created classroom id', classroom.id)
    else:
        print('Using classroom id', classroom.id)

    # Найти или создать тестового пользователя
    user = User.query.filter_by(username='testbot').first()
    if not user:
        user = User(username='testbot', email='testbot@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        print('Created user id', user.id)
    else:
        print('Using user id', user.id)

    booking_date = date.today()
    start = datetime.strptime('08:00', '%H:%M').time()
    end = datetime.strptime('09:00', '%H:%M').time()

    existing = Booking.query.filter(
        Booking.classroom_id == classroom.id,
        Booking.booking_date == booking_date,
        Booking.start_time == start,
        Booking.end_time == end
    ).first()

    if existing:
        print('Booking already exists with id', existing.id)
    else:
        booking = Booking(
            user_id=user.id,
            classroom_id=classroom.id,
            booking_date=booking_date,
            start_time=start,
            end_time=end,
            purpose='Test conflict',
            status='approved'
        )
        db.session.add(booking)
        db.session.commit()
        print('Created booking id', booking.id)
