from app import create_app, db
from app.models import User, Classroom, Booking

def init_database():
    app = create_app()
    
    with app.app_context():
        print("🗑️ Удаляем старую базу данных...")
        try:
            db.drop_all()
            print("✅ Старые таблицы удалены")
        except Exception as e:
            print(f"ℹ️ Не было старых таблиц для удаления: {e}")
        
        print("🔄 Создаем таблицы...")
        try:
            db.create_all()
            print("✅ Таблицы созданы успешно")
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            return
        
        print("🏫 Создаем аудитории...")
        classrooms = []
        for i in range(401, 424):
            classroom = Classroom(
                room_number=str(i),
                capacity=30 if i < 410 else 25 if i < 420 else 40,
                floor=4,
                has_projector=i % 2 == 0,
                has_computers=i in [405, 406, 415, 416]
            )
            classrooms.append(classroom)
        
        try:
            db.session.add_all(classrooms)
            print(f"✅ Создано {len(classrooms)} аудиторий")
        except Exception as e:
            print(f"❌ Ошибка при создании аудиторий: {e}")
            return
        
        print("👥 Создаем пользователей...")
        users_data = [
            {'username': 'admin', 'email': 'admin@example.com', 'role': 'teacher', 'password': 'admin'},
            {'username': 'teacher', 'email': 'teacher@example.com', 'role': 'teacher', 'password': 'teacher'},
            {'username': 'student', 'email': 'student@example.com', 'role': 'student', 'password': 'student'}
        ]
        
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"✅ Создан пользователь: {user_data['username']}")
        
        try:
            db.session.commit()
            print("✅ Все данные сохранены в базе")
        except Exception as e:
            print(f"❌ Ошибка при сохранении данных: {e}")
            db.session.rollback()
            return
        
        # Проверяем что все создалось
        try:
            user_count = User.query.count()
            classroom_count = Classroom.query.count()
            print(f"\n📊 Проверка: {user_count} пользователей, {classroom_count} аудиторий")
            
            print("\n🎉 База данных создана успешно!")
            print("\n👤 Тестовые пользователи:")
            print("   Преподаватель - логин: teacher, пароль: teacher")
            print("   Студент - логин: student, пароль: student")
            print("   Админ - логин: admin, пароль: admin")
            
        except Exception as e:
            print(f"❌ Ошибка при проверке данных: {e}")

if __name__ == '__main__':
    init_database()