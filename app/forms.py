from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length
from app.models import User
from datetime import date, timedelta
import re

def validate_email(form, field):
    email = field.data
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError('Пожалуйста, введите корректный email адрес.')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Роль', choices=[('student', 'Студент'), ('teacher', 'Преподаватель')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другое имя пользователя.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой email адрес.')

class BookingForm(FlaskForm):
    classroom_id = SelectField('Аудитория', coerce=int, validators=[DataRequired()])
    booking_date = DateField('Дата бронирования', 
                           validators=[DataRequired()], 
                           default=date.today,  # Здесь тоже нужно исправить на date.today()
                           render_kw={'min': date.today().strftime('%Y-%m-%d'),
                                     'max': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')})
    start_time = SelectField('Время начала', choices=[
        ('08:00', '08:00'), ('09:00', '09:00'), ('10:00', '10:00'), ('11:00', '11:00'),
        ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00'), ('15:00', '15:00'),
        ('16:00', '16:00'), ('17:00', '17:00'), ('18:00', '18:00'), ('19:00', '19:00'), ('20:00', '20:00')
    ], validators=[DataRequired()])
    end_time = SelectField('Время окончания', choices=[
        ('09:00', '09:00'), ('10:00', '10:00'), ('11:00', '11:00'), ('12:00', '12:00'),
        ('13:00', '13:00'), ('14:00', '14:00'), ('15:00', '15:00'), ('16:00', '16:00'),
        ('17:00', '17:00'), ('18:00', '18:00'), ('19:00', '19:00'), ('20:00', '20:00'), ('21:00', '21:00')
    ], validators=[DataRequired()])
    purpose = TextAreaField('Цель бронирования', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Забронировать')

class RecurringBookingForm(FlaskForm):
    classroom_id = SelectField('Аудитория', coerce=int, validators=[DataRequired()])
    start_date = DateField('Дата начала', validators=[DataRequired()], default=date.today)  # Исправьте на date.today()
    end_date = DateField('Дата окончания', validators=[DataRequired()], 
                        default=date.today() + timedelta(days=90))
    day_of_week = SelectField('День недели', choices=[
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
        (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')
    ], validators=[DataRequired()])
    start_time = SelectField('Время начала', choices=[
        ('08:00', '08:00'), ('09:00', '09:00'), ('10:00', '10:00'),
        ('11:00', '11:00'), ('12:00', '12:00'), ('13:00', '13:00'),
        ('14:00', '14:00'), ('15:00', '15:00'), ('16:00', '16:00'),
        ('17:00', '17:00'), ('18:00', '18:00'), ('19:00', '19:00'), ('20:00', '20:00')
    ], validators=[DataRequired()])
    end_time = SelectField('Время окончания', choices=[
        ('09:00', '09:00'), ('10:00', '10:00'), ('11:00', '11:00'),
        ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00'),
        ('15:00', '15:00'), ('16:00', '16:00'), ('17:00', '17:00'),
        ('18:00', '18:00'), ('19:00', '19:00'), ('20:00', '20:00'), ('21:00', '21:00')
    ], validators=[DataRequired()])
    recurrence_type = SelectField('Повторение', choices=[
        ('weekly', 'Каждую неделю'),
        ('biweekly', 'Каждые две недели')
    ], default='weekly')
    purpose = TextAreaField('Цель бронирования', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Создать регулярное бронирование')