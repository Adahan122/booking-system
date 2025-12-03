from flask import current_app
from flask_mail import Mail, Message
from app import mail
import threading

def send_async_email(app, msg):
    """Отправляет email асинхронно в отдельном потоке"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    """
    Отправляет email с поддержкой асинхронности
    
    Args:
        subject (str): Тема письма
        recipients (list): Список email адресатов
        text_body (str): Текстовое содержимое
        html_body (str): HTML содержимое (опционально)
    """
    msg = Message(
        subject=subject,
        recipients=recipients if isinstance(recipients, list) else [recipients],
        body=text_body,
        html=html_body
    )
    
    # Отправляем в отдельном потоке, чтобы не блокировать запрос
    thread = threading.Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    )
    thread.daemon = True
    thread.start()

def send_queue_notification_email(user_email, username, classroom_number, position, booking_date, start_time, end_time):
    """Отправляет уведомление об очереди"""
    subject = f"Вы в очереди бронирования - Позиция #{position}"
    
    text_body = f"""
Здравствуйте, {username}!

Ваша попытка забронировать аудиторию {classroom_number} на {booking_date} с {start_time} по {end_time} 
не удалась, т.к. это время уже занято.

Хорошая новость! Мы добавили вас в очередь ожидания.

Ваша позиция в очереди: #{position}

Когда эта аудитория станет доступна, мы вас уведомим!

С уважением,
Система бронирования аудиторий
    """
    
    html_body = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white; text-align: center;">
                    <h2 style="margin: 0;">📋 Вы добавлены в очередь</h2>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Здравствуйте, <strong>{username}</strong>!</p>
                    
                    <p>Ваша попытка забронировать аудиторию не удалась, т.к. это время уже занято.</p>
                    
                    <div style="background: #f0f7ff; border-left: 4px solid #4361ee; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Информация о бронировании:</strong></p>
                        <p style="margin: 5px 0;"><strong>Аудитория:</strong> {classroom_number}</p>
                        <p style="margin: 5px 0;"><strong>Дата:</strong> {booking_date}</p>
                        <p style="margin: 5px 0;"><strong>Время:</strong> {start_time} - {end_time}</p>
                    </div>
                    
                    <div style="background: #fffbf0; border-left: 4px solid #fbbf24; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>✓ Хорошая новость!</strong></p>
                        <p style="margin: 5px 0;">Мы добавили вас в очередь ожидания.</p>
                        <h3 style="color: #d97706; margin: 10px 0;">Ваша позиция: <strong>#{position}</strong></h3>
                        <p style="margin: 5px 0;">Когда эта аудитория станет доступна, мы вас уведомим!</p>
                    </div>
                    
                    <p>С уважением,<br><strong>Система бронирования аудиторий</strong></p>
                </div>
                
                <div style="text-align: center; padding: 15px; color: #666; font-size: 12px;">
                    <p>Это автоматическое письмо. Пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    send_email(subject, user_email, text_body, html_body)

def send_queue_approved_email(user_email, username, classroom_number, booking_date, start_time, end_time):
    """Отправляет уведомление об одобрении из очереди (когда можно уже забронировать)"""
    subject = f"Ваша очередь дошла! Аудитория {classroom_number} свободна"
    
    text_body = f"""
Здравствуйте, {username}!

Отличная новость! Аудитория {classroom_number} на {booking_date} с {start_time} по {end_time} теперь доступна!

Вы находились в очереди ожидания и теперь ваша очередь забронировать это время.

Пожалуйста, перейдите на сайт и подтвердите бронирование в течение 1 часа.

С уважением,
Система бронирования аудиторий
    """
    
    html_body = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white; text-align: center;">
                    <h2 style="margin: 0;">✅ Ваша очередь дошла!</h2>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Здравствуйте, <strong>{username}</strong>!</p>
                    
                    <div style="background: #f0fdf4; border-left: 4px solid #4ade80; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0; font-size: 18px;"><strong>🎉 Отличная новость!</strong></p>
                        <p style="margin: 10px 0;">Аудитория <strong>{classroom_number}</strong> теперь доступна для бронирования!</p>
                    </div>
                    
                    <div style="background: #f0f7ff; border-left: 4px solid #4361ee; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>📅 Информация о бронировании:</strong></p>
                        <p style="margin: 5px 0;"><strong>Аудитория:</strong> {classroom_number}</p>
                        <p style="margin: 5px 0;"><strong>Дата:</strong> {booking_date}</p>
                        <p style="margin: 5px 0;"><strong>Время:</strong> {start_time} - {end_time}</p>
                    </div>
                    
                    <div style="background: #fef3c7; border-left: 4px solid #fbbf24; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>⏰ Действуйте быстро!</strong></p>
                        <p style="margin: 5px 0;">Пожалуйста, подтвердите бронирование в течение <strong>1 часа</strong>.</p>
                        <p style="margin: 5px 0;">Иначе это время может быть предложено другому пользователю.</p>
                    </div>
                    
                    <p>С уважением,<br><strong>Система бронирования аудиторий</strong></p>
                </div>
                
                <div style="text-align: center; padding: 15px; color: #666; font-size: 12px;">
                    <p>Это автоматическое письмо. Пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    send_email(subject, user_email, text_body, html_body)

def send_booking_cancelled_email(user_email, username, classroom_number, booking_date, start_time, end_time):
    """Отправляет уведомление об отмене бронирования"""
    subject = f"Бронирование отменено - Аудитория {classroom_number}"
    
    text_body = f"""
Здравствуйте, {username}!

Ваше бронирование было отменено.

Информация:
- Аудитория: {classroom_number}
- Дата: {booking_date}
- Время: {start_time} - {end_time}

С уважением,
Система бронирования аудиторий
    """
    
    html_body = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white; text-align: center;">
                    <h2 style="margin: 0;">🔔 Уведомление об отмене</h2>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Здравствуйте, <strong>{username}</strong>!</p>
                    
                    <p>Ваше бронирование было отменено.</p>
                    
                    <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>Информация о отмене:</strong></p>
                        <p style="margin: 5px 0;"><strong>Аудитория:</strong> {classroom_number}</p>
                        <p style="margin: 5px 0;"><strong>Дата:</strong> {booking_date}</p>
                        <p style="margin: 5px 0;"><strong>Время:</strong> {start_time} - {end_time}</p>
                    </div>
                    
                    <p>С уважением,<br><strong>Система бронирования аудиторий</strong></p>
                </div>
                
                <div style="text-align: center; padding: 15px; color: #666; font-size: 12px;">
                    <p>Это автоматическое письмо. Пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    send_email(subject, user_email, text_body, html_body)
