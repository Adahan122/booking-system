from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

migrate = Migrate()
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Импорты должны быть здесь, после инициализации app
    with app.app_context():
        from app.auth import auth_bp
        from app.routes import main_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)

    return app


# Импорт моделей должен быть в конце
from app import models