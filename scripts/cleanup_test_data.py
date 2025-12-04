from app import create_app, db
from app.models import User, Booking, Classroom

app = create_app()

with app.app_context():
    # Delete bookings with purpose 'Test conflict'
    removed = 0
    bookings = Booking.query.filter(Booking.purpose=='Test conflict').all()
    for b in bookings:
        db.session.delete(b)
        removed += 1

    # Delete test user 'testbot'
    user = User.query.filter_by(username='testbot').first()
    u_removed = 0
    if user:
        # delete user's bookings just in case
        for b in user.bookings.all():
            db.session.delete(b)
            removed += 1
        db.session.delete(user)
        u_removed = 1

    db.session.commit()

    # Remove classroom '101' only if it has no bookings and was created by test
    classroom = Classroom.query.filter_by(room_number='101').first()
    c_removed = 0
    if classroom:
        # check for bookings
        if classroom.bookings.count() == 0:
            db.session.delete(classroom)
            db.session.commit()
            c_removed = 1

    print(f"Removed bookings: {removed}, removed user: {u_removed}, removed classroom: {c_removed}")
