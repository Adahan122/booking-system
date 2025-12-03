from app import create_app, db
from app.models import User, Classroom

def test_database():
    app = create_app()
    
    with app.app_context():
        print("🔍 Проверяем базу данных...")
        
        # Проверяем существование таблиц
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Таблицы в базе: {tables}")
        
        # Проверяем данные
        try:
            user_count = User.query.count()
            classroom_count = Classroom.query.count()
            print(f"👥 Пользователей: {user_count}")
            print(f"🏫 Аудиторий: {classroom_count}")
            
            if user_count > 0:
                users = User.query.all()
                for user in users:
                    print(f"   - {user.username} ({user.role})")
                    
            if classroom_count > 0:
                classrooms = Classroom.query.limit(5).all()
                for classroom in classrooms:
                    print(f"   - Аудитория {classroom.room_number}")
                    
        except Exception as e:
            print(f"❌ Ошибка при проверке данных: {e}")

if __name__ == '__main__':
    test_database()