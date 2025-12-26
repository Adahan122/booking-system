from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Classroom, Booking, User, RecurringBooking, BookingQueue
from app.forms import BookingForm, RecurringBookingForm
from datetime import datetime, date,timedelta
from app.email import (
    send_queue_notification_email,
    send_queue_approved_email,
    send_booking_cancelled_email
)





main_bp = Blueprint('main', __name__)

@main_bp.context_processor
def inject_now():
    return {'now': datetime.now()}

@main_bp.route('/')
@main_bp.route('/index')
def index():
    classroom_count = Classroom.query.count()
    return render_template('index.html', title='Главная', classroom_count=classroom_count)

@main_bp.route('/classrooms')
def classrooms():

    status_filter = request.args.get('status', 'all')
    equipment_filter = request.args.get('equipment', 'all')
    floor_filter = request.args.get('floor', 'all')

    query = Classroom.query.filter_by(is_active=True)
    
    if equipment_filter != 'all':
        if equipment_filter == 'projector':
            query = query.filter_by(has_projector=True)
        elif equipment_filter == 'computers':
            query = query.filter_by(has_computers=True)
    
    if floor_filter != 'all':
        query = query.filter_by(floor=int(floor_filter))
    
    classrooms_list = query.all()
    
    # Получаем текущие активные бронирования
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    
    # Для каждой аудитории проверяем, занята ли она сейчас
    for classroom in classrooms_list:
        # Проверяем, есть ли активное бронирование на эту аудиторию прямо сейчас
        active_booking = Booking.query.filter(
            Booking.classroom_id == classroom.id,
            Booking.booking_date == current_date,
            Booking.status == 'approved',
            Booking.start_time <= current_time,
            Booking.end_time > current_time
        ).first()
        
        classroom.is_occupied_now = active_booking is not None
        if active_booking:
            classroom.occupied_by = active_booking.user.username
            classroom.occupied_until = active_booking.end_time
            classroom.booking_purpose = active_booking.purpose
        
        # Также проверяем бронирования на сегодня (для отображения расписания)
        today_bookings = Booking.query.filter(
            Booking.classroom_id == classroom.id,
            Booking.booking_date == current_date,
            Booking.status == 'approved'
        ).order_by(Booking.start_time).all()
        
        classroom.today_bookings = today_bookings
    
    # Применяем фильтр по статусу (свободные/занятые)
    if status_filter == 'free':
        classrooms_list = [c for c in classrooms_list if not c.is_occupied_now]
    elif status_filter == 'occupied':
        classrooms_list = [c for c in classrooms_list if c.is_occupied_now]
    
    # Рассчитываем максимальную дату для календаря
    from datetime import timedelta
    max_date = current_date + timedelta(days=30)
    
    return render_template('classrooms.html', 
                         title='Аудитории', 
                         classrooms=classrooms_list, 
                         now=now,
                         current_date=current_date,
                         max_date=max_date,
                         status_filter=status_filter,
                         equipment_filter=equipment_filter,
                         floor_filter=floor_filter)


@main_bp.route('/api/check_availability/<int:classroom_id>/<string:date>/<string:start_time>/<string:end_time>')
def check_availability(classroom_id, date, start_time, end_time):
    """Проверяет доступность аудитории на указанное время"""
    try:
        booking_date = datetime.strptime(date, '%Y-%m-%d').date()
        start = datetime.strptime(start_time, '%H:%M').time()
        end = datetime.strptime(end_time, '%H:%M').time()
        
        # Проверяем наличие пересекающихся бронирований
        conflicting_booking = Booking.query.filter(
            Booking.classroom_id == classroom_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['pending', 'approved']),
            ((Booking.start_time <= start) & (Booking.end_time > start)) |
            ((Booking.start_time < end) & (Booking.end_time >= end)) |
            ((Booking.start_time >= start) & (Booking.end_time <= end))
        ).first()
        
        is_available = conflicting_booking is None
        
        return jsonify({
            'classroom_id': classroom_id,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'is_available': is_available,
            'conflict': {
                'exists': conflicting_booking is not None,
                'user': conflicting_booking.user.username if conflicting_booking else None,
                'purpose': conflicting_booking.purpose if conflicting_booking else None,
                'time': f"{conflicting_booking.start_time.strftime('%H:%M')} - {conflicting_booking.end_time.strftime('%H:%M')}" if conflicting_booking else None
            } if conflicting_booking else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@main_bp.route('/api/classroom_schedule/<int:classroom_id>')
def classroom_schedule(classroom_id):
    """Возвращает расписание аудитории на сегодня"""
    today = date.today()
    
    # Получаем все бронирования на сегодня
    bookings = Booking.query.filter(
        Booking.classroom_id == classroom_id,
        Booking.booking_date == today,
        Booking.status.in_(['approved', 'pending'])
    ).all()
    
    # Создаем расписание по часам
    schedule = []
    for hour in range(8, 22):  # с 8:00 до 21:00
        time_slot = f"{hour:02d}:00"
        is_booked = False
        booking_info = None
        
        for booking in bookings:
            start_hour = booking.start_time.hour
            end_hour = booking.end_time.hour
            
            if start_hour <= hour < end_hour:
                is_booked = True
                booking_info = {
                    'user': booking.user.username,
                    'purpose': booking.purpose,
                    'status': booking.status
                }
                break
        
        schedule.append({
            'time': time_slot,
            'is_booked': is_booked,
            'booking': booking_info
        })
    
    return jsonify({
        'classroom_id': classroom_id,
        'date': today.strftime('%Y-%m-%d'),
        'schedule': schedule
    })

# @main_bp.route('/booking', methods=['GET', 'POST'])
# @login_required
# def booking():
#     form = BookingForm()
#     classrooms = Classroom.query.filter_by(is_active=True).all()
#     form.classroom_id.choices = [(c.id, f"Аудитория {c.room_number} (вместимость: {c.capacity})") for c in classrooms]
    
#     if form.validate_on_submit():
#         start_time = datetime.strptime(form.start_time.data, '%H:%M').time()
#         end_time = datetime.strptime(form.end_time.data, '%H:%M').time()
        
#         if start_time >= end_time:
#             flash('Время окончания должно быть позже времени начала', 'danger')
#             return render_template('booking.html', title='Бронирование', form=form)
        
#         existing_booking = Booking.query.filter(
#             Booking.classroom_id == form.classroom_id.data,
#             Booking.booking_date == form.booking_date.data,
#             Booking.status.in_(['pending', 'approved']),
#             ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
#             ((Booking.start_time < end_time) & (Booking.end_time >= end_time)) |
#             ((Booking.start_time >= start_time) & (Booking.end_time <= end_time))
#         ).first()
        
#         if existing_booking:
#             flash('Аудитория уже забронирована на выбранное время', 'danger')
#             return render_template('booking.html', title='Бронирование', form=form)
        
#         booking = Booking(
#             user_id=current_user.id,
#             classroom_id=form.classroom_id.data,
#             booking_date=form.booking_date.data,
#             start_time=start_time,
#             end_time=end_time,
#             purpose=form.purpose.data,
#             status='approved' if current_user.role == 'teacher' else 'pending'
#         )
        
#         db.session.add(booking)
#         db.session.commit()
        
#         status_msg = 'одобрено' if current_user.role == 'teacher' else 'ожидает подтверждения'
#         flash(f'Бронирование успешно создано и {status_msg}!', 'success')
#         return redirect(url_for('main.profile'))
    
#     return render_template('booking.html', title='Бронирование', form=form)

@main_bp.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    form = BookingForm()
    classrooms = Classroom.query.filter_by(is_active=True).all()
    form.classroom_id.choices = [(c.id, f"Аудитория {c.room_number} (вместимость: {c.capacity})") for c in classrooms]
    
    # Если приходит с параметром classroom, заполняем форму автоматически
    selected_classroom_id = request.args.get('classroom', type=int)
    preselected_classroom = None
    if selected_classroom_id:
        preselected_classroom = Classroom.query.get(selected_classroom_id)
        if preselected_classroom:
            form.classroom_id.data = selected_classroom_id
    
    if form.validate_on_submit():
        start_time = datetime.strptime(form.start_time.data, '%H:%M').time()
        end_time = datetime.strptime(form.end_time.data, '%H:%M').time()
        
        # Проверяем корректность времени
        if start_time >= end_time:
            flash('Время окончания должно быть позже времени начала', 'danger')
            return render_template('booking.html', title='Бронирование', form=form)
        
        # Проверяем, что бронирование не более чем на 4 часа
        time_diff = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
        if time_diff.total_seconds() > 4 * 3600:
            flash('Максимальное время бронирования - 4 часа', 'danger')
            return render_template('booking.html', title='Бронирование', form=form)
        
        # Проверяем, что дата бронирования не в прошлом и не слишком далеко в будущем
        max_booking_date = date.today() + timedelta(days=30)
        if form.booking_date.data < date.today():
            flash('Нельзя бронировать аудиторию на прошедшую дату', 'danger')
            return render_template('booking.html', title='Бронирование', form=form)
        
        if form.booking_date.data > max_booking_date:
            flash('Можно бронировать аудиторию не более чем на 30 дней вперед', 'danger')
            return render_template('booking.html', title='Бронирование', form=form)
        
        # === ВАЖНО: Проверяем, не закончилось ли уже текущее время ===
        if form.booking_date.data == date.today():
            current_time = datetime.now().time()
            if start_time < current_time:
                flash('Нельзя бронировать аудиторию на прошедшее время', 'danger')
                return render_template('booking.html', title='Бронирование', form=form)
        
        # Проверяем доступность аудитории
        existing_booking = Booking.query.filter(
            Booking.classroom_id == form.classroom_id.data,
            Booking.booking_date == form.booking_date.data,
            Booking.status.in_(['pending', 'approved']),
            ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
            ((Booking.start_time < end_time) & (Booking.end_time >= end_time)) |
            ((Booking.start_time >= start_time) & (Booking.end_time <= end_time))
        ).first()
        
        if existing_booking:
            # Аудитория занята — предлагаем встать в очередь
            queue_count = BookingQueue.query.filter(
                BookingQueue.classroom_id == form.classroom_id.data,
                BookingQueue.booking_date == form.booking_date.data,
                BookingQueue.start_time == start_time,
                BookingQueue.end_time == end_time,
                BookingQueue.status == 'waiting'
            ).count()
            
            new_queue_entry = BookingQueue(
                user_id=current_user.id,
                classroom_id=form.classroom_id.data,
                booking_date=form.booking_date.data,
                start_time=start_time,
                end_time=end_time,
                queue_position=queue_count + 1,
                status='waiting'
            )
            db.session.add(new_queue_entry)
            db.session.commit()
            
            # Отправляем email уведомление об очереди
            classroom = Classroom.query.get(form.classroom_id.data)
            try:
                send_queue_notification_email(
                    user_email=current_user.email,
                    username=current_user.username,
                    classroom_number=classroom.room_number,
                    position=queue_count + 1,
                    booking_date=form.booking_date.data.strftime('%d.%m.%Y'),
                    start_time=start_time.strftime('%H:%M'),
                    end_time=end_time.strftime('%H:%M')
                )
            except Exception as e:
                print(f'Ошибка при отправке email: {e}')
            
            flash(f'Аудитория занята. Вы встали в очередь (позиция {queue_count + 1}). Вас уведомят, когда слот освободится.', 'info')
            return redirect(url_for('main.booking'))
        
        
        # Проверяем, не бронирует ли пользователь другую аудиторию на это же время
        user_conflict = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.booking_date == form.booking_date.data,
            Booking.status.in_(['pending', 'approved']),
            ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
            ((Booking.start_time < end_time) & (Booking.end_time >= end_time)) |
            ((Booking.start_time >= start_time) & (Booking.end_time <= end_time))
        ).first()
        
        if user_conflict:
            flash('У вас уже есть бронирование на это время в другой аудитории', 'danger')
            return render_template('booking.html', title='Бронирование', form=form)
        
        # Ограничиваем количество бронирований в день для студентов
        if current_user.role == 'student':
            today_bookings_count = Booking.query.filter(
                Booking.user_id == current_user.id,
                Booking.booking_date == form.booking_date.data,
                Booking.status.in_(['pending', 'approved'])
            ).count()
            
            if today_bookings_count >= 2:
                flash('Вы не можете забронировать более 2 аудиторий в день', 'danger')
                return render_template('booking.html', title='Бронирование', form=form)
        
        # Создаем бронирование
        booking = Booking(
            user_id=current_user.id,
            classroom_id=form.classroom_id.data,
            booking_date=form.booking_date.data,
            start_time=start_time,
            end_time=end_time,
            purpose=form.purpose.data,
            status='approved' if current_user.role == 'teacher' else 'pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        status_msg = 'одобрено' if current_user.role == 'teacher' else 'ожидает подтверждения'
        flash(f'Бронирование успешно создано и {status_msg}!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('booking.html', title='Бронирование', form=form, preselected_classroom=preselected_classroom)




@main_bp.route('/recurring_booking', methods=['GET', 'POST'])
@login_required
def recurring_booking():
    """Создание повторяющегося бронирования"""
    form = RecurringBookingForm()
    classrooms = Classroom.query.filter_by(is_active=True).all()
    form.classroom_id.choices = [(c.id, f"Аудитория {c.room_number}") for c in classrooms]
    
    if form.validate_on_submit():
        # Проверяем корректность дат
        if form.end_date.data <= form.start_date.data:
            flash('Дата окончания должна быть позже даты начала', 'danger')
            return render_template('recurring_booking.html', title='Регулярное бронирование', form=form)
        
        if form.start_date.data < date.today():
            flash('Нельзя создавать бронирования на прошедшие даты', 'danger')
            return render_template('recurring_booking.html', title='Регулярное бронирование', form=form)
        
        # Проверяем доступность для первых 4 недель
        from datetime import timedelta
        check_end_date = min(form.end_date.data, form.start_date.data + timedelta(days=28))
        
        for i in range(4):
            current_date = form.start_date.data + timedelta(days=i * (7 if form.recurrence_type.data == 'weekly' else 14))
            if current_date > check_end_date:
                break
            
            # Проверяем доступность для этой даты
            start_time = datetime.strptime(form.start_time.data, '%H:%M').time()
            end_time = datetime.strptime(form.end_time.data, '%H:%M').time()
            
            existing = Booking.query.filter(
                Booking.classroom_id == form.classroom_id.data,
                Booking.booking_date == current_date,
                Booking.status.in_(['pending', 'approved']),
                ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
                ((Booking.start_time < end_time) & (Booking.end_time >= end_time))
            ).first()
            
            if existing:
                flash(f'Аудитория занята {current_date.strftime("%d.%m.%Y")} в это время', 'danger')
                return render_template('recurring_booking.html', title='Регулярное бронирование', form=form)
        
        # Создаем повторяющееся бронирование
        recurring = RecurringBooking(
            user_id=current_user.id,
            classroom_id=form.classroom_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            day_of_week=form.day_of_week.data,
            start_time=datetime.strptime(form.start_time.data, '%H:%M').time(),
            end_time=datetime.strptime(form.end_time.data, '%H:%M').time(),
            recurrence_type=form.recurrence_type.data,
            purpose=form.purpose.data
        )
        
        db.session.add(recurring)
        db.session.commit()
        
        # Генерируем бронирования на первые 4 недели
        generated_bookings = recurring.generate_bookings(
            start_date=form.start_date.data,
            end_date=min(form.end_date.data, form.start_date.data + timedelta(days=28))
        )
        
        for booking in generated_bookings:
            db.session.add(booking)
        
        db.session.commit()
        
        flash(f'Регулярное бронирование создано! Создано {len(generated_bookings)} бронирований.', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('recurring_booking.html', title='Регулярное бронирование', form=form)


@main_bp.route('/cancel_recurring/<int:recurring_id>')
@login_required
def cancel_recurring(recurring_id):
    """Отмена повторяющегося бронирования"""
    recurring = RecurringBooking.query.get_or_404(recurring_id)
    
    # Проверяем права
    if recurring.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Вы можете отменять только свои регулярные бронирования', 'danger')
        return redirect(url_for('main.profile'))
    
    # Отменяем все будущие бронирования из этой серии
    future_bookings = Booking.query.filter(
        Booking.recurring_booking_id == recurring_id,
        Booking.booking_date >= date.today(),
        Booking.status.in_(['pending', 'approved'])
    ).all()
    
    for booking in future_bookings:
        db.session.delete(booking)
    
    recurring.status = 'cancelled'
    db.session.commit()
    
    flash(f'Регулярное бронирование отменено. Удалено {len(future_bookings)} будущих бронирований.', 'success')
    return redirect(url_for('main.profile'))


def auto_complete_past_bookings():
    """Автоматически помечает прошедшие бронирования как завершенные"""
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()
    
    # Находим бронирования, которые уже закончились но еще активны
    expired_bookings = Booking.query.filter(
        ((Booking.booking_date < current_date) |
         ((Booking.booking_date == current_date) & (Booking.end_time < current_time))),
        Booking.status.in_(['approved', 'pending'])
    ).all()
    
    for booking in expired_bookings:
        booking.status = 'completed'
    
    if expired_bookings:
        db.session.commit()
        print(f"Автоматически завершено {len(expired_bookings)} бронирований")

@main_bp.route('/profile')
@login_required
def profile():
    try:
        # Автоматически завершаем прошедшие бронирования
        auto_complete_past_bookings()
        
        # Получаем бронирования ТОЛЬКО текущего пользователя
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
            Booking.booking_date.desc(), 
            Booking.start_time.desc()
        ).all()
        
        # Получаем очередь ожидания текущего пользователя
        user_queue_entries = BookingQueue.query.filter_by(user_id=current_user.id).order_by(
            BookingQueue.booking_date.desc(),
            BookingQueue.start_time.desc()
        ).all()
        
        return render_template('profile.html', 
                             title='Мой профиль', 
                             bookings=user_bookings,
                             queue_entries=user_queue_entries,
                             current_date=date.today())
    except Exception as e:
        flash('Ошибка загрузки данных профиля.', 'danger')
        return render_template('profile.html', 
                             title='Мой профиль', 
                             bookings=[],
                             queue_entries=[],
                             current_date=date.today())
    


@main_bp.route('/calendar')
@login_required
def calendar_view():
    """Календарь бронирований"""
    # Получаем параметры месяца/года
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)
    
    # Проверяем корректность месяца/года
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 2020 or year > 2030:
        year = datetime.now().year
    
    # Создаем календарь на месяц
    import calendar
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Получаем бронирования на месяц
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    # Для студентов - только их бронирования, для преподавателей - все
    if current_user.role in ['teacher', 'admin']:
        month_bookings = Booking.query.filter(
            Booking.booking_date >= start_date,
            Booking.booking_date < end_date,
            Booking.status.in_(['approved', 'pending'])
        ).all()
    else:
        month_bookings = Booking.query.filter(
            Booking.booking_date >= start_date,
            Booking.booking_date < end_date,
            Booking.user_id == current_user.id,
            Booking.status.in_(['approved', 'pending'])
        ).all()
    
    # Группируем бронирования по датам
    bookings_by_date = {}
    for booking in month_bookings:
        date_str = booking.booking_date.strftime('%Y-%m-%d')
        if date_str not in bookings_by_date:
            bookings_by_date[date_str] = []
        bookings_by_date[date_str].append(booking)
    
    # Получаем статистику занятости по аудиториям
    classroom_stats = {}
    classrooms = Classroom.query.filter_by(is_active=True).all()
    for classroom in classrooms:
        classroom_bookings = [b for b in month_bookings if b.classroom_id == classroom.id]
        classroom_stats[classroom.id] = {
            'room_number': classroom.room_number,
            'total_hours': sum((b.end_time.hour - b.start_time.hour) for b in classroom_bookings),
            'booking_count': len(classroom_bookings),
            'utilization': (len(classroom_bookings) / 22) * 100  # 22 рабочих дня в месяце
        }
    
    # Соседние месяцы для навигации
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    return render_template('calendar.html',
                         title='Календарь бронирований',
                         calendar=cal,
                         year=year,
                         month=month,
                         month_name=month_name,
                         bookings_by_date=bookings_by_date,
                         classroom_stats=classroom_stats,
                         today=date.today(),
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year)


@main_bp.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем, что пользователь отменяет свое бронирование
    # или это преподаватель/админ
    if booking.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Вы можете отменять только свои бронирования', 'danger')
        return redirect(url_for('main.profile'))
    
    # Проверяем, что бронирование еще не началось
    booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
    if booking_datetime < datetime.now():
        flash('Нельзя отменить прошедшее бронирование', 'danger')
        return redirect(url_for('main.profile'))
    
    db.session.delete(booking)
    db.session.commit()
    
    # Уведомляем первого в очереди
    queue_entry = BookingQueue.query.filter(
        BookingQueue.classroom_id == booking.classroom_id,
        BookingQueue.booking_date == booking.booking_date,
        BookingQueue.start_time == booking.start_time,
        BookingQueue.end_time == booking.end_time,
        BookingQueue.status == 'waiting'
    ).order_by(BookingQueue.queue_position).first()
    
    if queue_entry:
        queue_entry.status = 'notified'
        queue_entry.notified = True
        db.session.commit()
        
        # Отправляем email уведомление
        classroom = Classroom.query.get(booking.classroom_id)
        try:
            send_queue_approved_email(
                user_email=queue_entry.user.email,
                username=queue_entry.user.username,
                classroom_number=classroom.room_number,
                booking_date=booking.booking_date.strftime('%d.%m.%Y'),
                start_time=booking.start_time.strftime('%H:%M'),
                end_time=booking.end_time.strftime('%H:%M')
            )
        except Exception as e:
            print(f'Ошибка при отправке email: {e}')
        
        flash(f'Уведомление отправлено пользователю {queue_entry.user.username} о возможности бронирования', 'info')
    
    flash('Бронирование успешно отменено', 'success')
    return redirect(url_for('main.profile'))

@main_bp.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role not in ['teacher', 'admin']:
        flash('У вас нет прав для доступа к этой странице.', 'danger')
        return redirect(url_for('main.index'))
    
    pending_bookings = Booking.query.filter_by(status='pending').order_by(Booking.booking_date, Booking.start_time).all()
    approved_bookings = Booking.query.filter(Booking.status == 'approved', Booking.booking_date >= date.today()).all()
    
    return render_template('admin_bookings.html', 
                         title='Управление бронированиями',
                         pending_bookings=pending_bookings,
                         approved_bookings=approved_bookings)

@main_bp.route('/admin/approve_booking/<int:booking_id>')
@login_required
def approve_booking(booking_id):
    if current_user.role not in ['teacher', 'admin']:
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))
    
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'approved'
    db.session.commit()
    flash('Бронирование одобрено', 'success')
    return redirect(url_for('main.admin_bookings'))

@main_bp.route('/remove_from_queue/<int:queue_id>')
@login_required
def remove_from_queue(queue_id):
    queue_entry = BookingQueue.query.get_or_404(queue_id)
    
    # Проверяем, что пользователь удаляет свой запрос из очереди
    if queue_entry.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Вы можете удалять только свои записи из очереди', 'danger')
        return redirect(url_for('main.profile'))
    
    # Удаляем из очереди
    classroom_id = queue_entry.classroom_id
    db.session.delete(queue_entry)
    db.session.commit()
    
    # Переиндексируем позиции в очереди
    remaining_queue = BookingQueue.query.filter(
        BookingQueue.classroom_id == classroom_id,
        BookingQueue.booking_date == queue_entry.booking_date,
        BookingQueue.start_time == queue_entry.start_time,
        BookingQueue.end_time == queue_entry.end_time,
        BookingQueue.status == 'waiting'
    ).order_by(BookingQueue.created_at).all()
    
    for idx, entry in enumerate(remaining_queue, 1):
        entry.queue_position = idx
    
    db.session.commit()
    flash('Вы удалены из очереди', 'success')
    return redirect(url_for('main.profile'))
@main_bp.route('/admin/reject_booking/<int:booking_id>')
@login_required
def reject_booking(booking_id):
    if current_user.role not in ['teacher', 'admin']:
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))
    
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'rejected'
    db.session.commit()
    
    flash(f'Бронирование аудитории {booking.classroom.room_number} отклонено.', 'info')
    return redirect(url_for('main.admin_bookings'))