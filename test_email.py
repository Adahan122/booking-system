#!/usr/bin/env python
"""
Тестирование конфигурации email
Запустить: python test_email.py
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_email_config():
    """Проверяет конфигурацию email"""
    print("=" * 60)
    print("🔍 Проверка конфигурации Email")
    print("=" * 60)
    
    # Проверяем переменные окружения
    configs = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
        'MAIL_PORT': os.environ.get('MAIL_PORT'),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': '***' if os.environ.get('MAIL_PASSWORD') else None,
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
    }
    
    print("\n📋 Текущие параметры из .env:")
    for key, value in configs.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value or 'НЕ УСТАНОВЛЕНО'}")
    
    # Проверяем обязательные параметры
    required = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_SERVER']
    missing = [k for k in required if not os.environ.get(k)]
    
    if missing:
        print(f"\n❌ Ошибка: Не установлены параметры: {', '.join(missing)}")
        print("\n💡 Действия:")
        print("   1. Отредактируйте файл .env")
        print("   2. Установите значения для:")
        for param in missing:
            print(f"      - {param}")
        return False
    
    # Проверяем Flask-Mail
    try:
        from flask_mail import Mail
        print("\n✓ Flask-Mail установлена корректно")
    except ImportError:
        print("\n✗ Flask-Mail НЕ установлена")
        print("   Запустите: pip install Flask-Mail")
        return False
    
    # Проверяем подключение
    print("\n🔗 Попытка подключения к SMTP серверу...")
    try:
        import smtplib
        
        with smtplib.SMTP(
            host=os.environ.get('MAIL_SERVER'),
            port=int(os.environ.get('MAIL_PORT', 587))
        ) as server:
            
            if os.environ.get('MAIL_USE_TLS'):
                server.starttls()
            
            # Пытаемся авторизоваться
            server.login(
                os.environ.get('MAIL_USERNAME'),
                os.environ.get('MAIL_PASSWORD')
            )
            
            print("✓ Подключение к SMTP успешно!")
            print("✓ Авторизация прошла успешно!")
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("✗ Ошибка: Неверное имя пользователя или пароль")
        print("   Проверьте MAIL_USERNAME и MAIL_PASSWORD в .env")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ Ошибка SMTP: {e}")
        return False
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        print("   Проверьте:")
        print("   - Правильность MAIL_SERVER")
        print("   - Правильность MAIL_PORT")
        print("   - Интернет соединение")
        return False

def test_email_send():
    """Пытается отправить тестовое письмо"""
    from app import create_app
    from app.email import send_email
    
    print("\n" + "=" * 60)
    print("📧 Отправка тестового письма")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            send_email(
                subject='🧪 Тестовое письмо от системы бронирования',
                recipients=[os.environ.get('MAIL_USERNAME')],
                text_body='Это тестовое письмо. Если вы его получили, то конфигурация email работает корректно!',
                html_body='<h2>🎉 Тест успешен!</h2><p>Email конфигурация работает корректно.</p>'
            )
            print("✓ Письмо отправлено в асинхронный процесс")
            print("✓ Проверьте вашу почту (может быть в SPAM)")
            return True
        except Exception as e:
            print(f"✗ Ошибка при отправке: {e}")
            return False

if __name__ == '__main__':
    # Шаг 1: Проверяем конфигурацию
    config_ok = test_email_config()
    
    if config_ok and len(sys.argv) > 1 and sys.argv[1] == '--send':
        # Шаг 2: Опционально - пробуем отправить письмо
        email_ok = test_email_send()
        
        print("\n" + "=" * 60)
        if email_ok:
            print("✅ ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО!")
        else:
            print("⚠️  ЕСТЬ ПРОБЛЕМЫ С ОТПРАВКОЙ EMAIL")
        print("=" * 60)
    elif not config_ok:
        print("\n" + "=" * 60)
        print("❌ КОНФИГУРАЦИЯ EMAIL НЕВЕРНА")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✅ КОНФИГУРАЦИЯ EMAIL КОРРЕКТНА")
        print("\n💡 Для отправки тестового письма запустите:")
        print("   python test_email.py --send")
        print("=" * 60)
